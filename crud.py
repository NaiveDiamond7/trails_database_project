import database as db
import oracledb

# --- REGIONY ---
def get_regiony():
    return db.execute_query_df("SELECT id_regionu, nazwa FROM regiony ORDER BY id_regionu")

def add_region(nazwa):
    return db.execute_dml("INSERT INTO regiony (nazwa) VALUES (:1)", [nazwa])

def delete_region(id_regionu):
    return db.execute_dml("DELETE FROM regiony WHERE id_regionu = :1", [id_regionu])

# --- SCHRONISKA ---
def get_schroniska_view():
    sql = """
    SELECT s.id_schroniska, s.nazwa, r.nazwa as region, s.wysokosc, 
           s.godzina_otwarcia, s.godzina_zamkniecia
    FROM schroniska s
    JOIN regiony r ON s.id_regionu = r.id_regionu
    """
    return db.execute_query_df(sql)

def add_schronisko_transaction(id_region, nazwa, wysokosc, otwarcie, zamkniecie):
    sql = """
    DECLARE
        v_id NUMBER;
    BEGIN
        INSERT INTO punkty (id_regionu, nazwa, typ, wysokosc, wspolrzedne_dlugosc, wspolrzedne_szerokosc)
        VALUES (:reg_id, :nazwa, 'Schronisko', :wys, 0, 0)
        RETURNING id_punktu INTO v_id;

        INSERT INTO schroniska (id_schroniska, id_regionu, nazwa, wysokosc, godzina_otwarcia, godzina_zamkniecia)
        VALUES (v_id, :reg_id, :nazwa, :wys, :godz_otw, :godz_zam);
    END;
    """
    params = [id_region, nazwa, wysokosc, otwarcie, zamkniecie]
    return db.execute_dml(sql, params)

# --- REZERWACJE (PROCEDURY I LOGIKA BIZNESOWA) ---
def get_users_dict():
    df = db.execute_query_df("SELECT id_uzytkownika, login, nazwisko FROM uzytkownicy")
    return {f"{row['LOGIN']} ({row['NAZWISKO']})": row['ID_UZYTKOWNIKA'] for i, row in df.iterrows()}

def get_pokoje_in_schronisko(id_schroniska):
    sql = "SELECT id_pokoju, nr_pokoju, cena_za_noc, liczba_miejsc_wolnych FROM pokoje WHERE id_schroniska = :1"
    return db.execute_query_df(sql, [id_schroniska])

def calculate_cost(id_pokoju, start, end, osoby):
    return db.execute_function("oblicz_koszt_pobytu", oracledb.NUMBER, [id_pokoju, start, end, osoby])

def make_reservation(id_pokoju, id_user, osoby, start, end):
    """
    Tworzy rezerwację z PEŁNĄ kontrolą pojemności pokoju w danym terminie.
    Sprawdza, czy suma osób w tym pokoju w nachodzących datach nie przekracza pojemności.
    """
    # 1. Pobierz pojemność całkowitą tego pokoju
    cap_sql = "SELECT liczba_miejsc_calkowita FROM pokoje WHERE id_pokoju = :1"
    cap_df = db.execute_query_df(cap_sql, [id_pokoju])
    
    if cap_df.empty:
        return False, "Błąd: Nie znaleziono wybranego pokoju."
    
    max_capacity = cap_df.iloc[0]['LICZBA_MIEJSC_CALKOWITA']

    # 2. Oblicz ile miejsc jest już zajętych w tym terminie przez KOGOKOLWIEK
    # Warunek nakładania się dat: (Start_Istniejąca < End_Nowa) AND (End_Istniejąca > Start_Nowa)
    overlap_sql = """
        SELECT COALESCE(SUM(liczba_osob), 0) as zajete
        FROM rezerwacje 
        WHERE id_pokoju = :1 
          AND status_rez != 'anulowana'
          AND data_rozpoczecia < :2 
          AND data_zakonczenia > :3
    """
    # Parametry: id_pokoju, data_konca_nowej, data_startu_nowej
    occ_df = db.execute_query_df(overlap_sql, [id_pokoju, end, start])
    current_occupancy = occ_df.iloc[0]['ZAJETE']

    # 3. Sprawdź czy zmieścimy nowe osoby
    if current_occupancy + osoby > max_capacity:
        remaining = max_capacity - current_occupancy
        if remaining <= 0:
            return False, f"Pokój jest w pełni zajęty w tym terminie."
        else:
            return False, f"Brak wystarczającej liczby miejsc. Wolne: {remaining}, Żądane: {osoby}."

    # 4. Jeśli wszystko OK, wykonaj procedurę
    return db.execute_procedure("dokonaj_rezerwacji", [id_pokoju, id_user, osoby, start, end])

def get_user_reservations(id_user):
    """Pobiera historię rezerwacji dla konkretnego użytkownika"""
    sql = """
        SELECT r.id_rezerwacji, u.login, u.imie, u.nazwisko, 
               s.nazwa as schronisko, p.nr_pokoju, r.liczba_osob,
               r.data_rozpoczecia, r.data_zakonczenia, r.status_rez, r.kwota
        FROM rezerwacje r
        JOIN pokoje p ON r.id_pokoju = p.id_pokoju
        JOIN schroniska s ON p.id_schroniska = s.id_schroniska
        JOIN uzytkownicy u ON r.id_uzytkownika = u.id_uzytkownika
        WHERE r.id_uzytkownika = :1
        ORDER BY r.id_rezerwacji DESC
    """
    return db.execute_query_df(sql, [id_user])

def get_all_reservations():
    """Pobiera historię WSZYSTKICH rezerwacji (do widoku globalnego)"""
    sql = """
        SELECT r.id_rezerwacji, u.login, u.imie, u.nazwisko, 
               s.nazwa as schronisko, p.nr_pokoju, r.liczba_osob,
               r.data_rozpoczecia, r.data_zakonczenia, r.status_rez, r.kwota
        FROM rezerwacje r
        JOIN pokoje p ON r.id_pokoju = p.id_pokoju
        JOIN schroniska s ON p.id_schroniska = s.id_schroniska
        JOIN uzytkownicy u ON r.id_uzytkownika = u.id_uzytkownika
        ORDER BY r.id_rezerwacji DESC
    """
    return db.execute_query_df(sql)

# W pliku crud.py (sekcja REZERWACJE)

def delete_reservation(id_rezerwacji):
    """
    Usuwa rezerwację i przywraca wolne miejsca w pokoju.
    Używamy bloku PL/SQL, aby zrobić to w jednej transakcji.
    """
    sql = """
    DECLARE
        v_pokoj NUMBER;
        v_osob NUMBER;
    BEGIN
        -- 1. Pobieramy dane rezerwacji przed usunięciem (używamy zmiennej :1)
        SELECT id_pokoju, liczba_osob INTO v_pokoj, v_osob
        FROM rezerwacje WHERE id_rezerwacji = :1;

        -- 2. Usuwamy rezerwację (ponownie używamy tej samej zmiennej :1)
        DELETE FROM rezerwacje WHERE id_rezerwacji = :1;

        -- 3. Oddajemy miejsca do puli wolnych w pokoju
        UPDATE pokoje 
        SET liczba_miejsc_wolnych = liczba_miejsc_wolnych + v_osob
        WHERE id_pokoju = v_pokoj;
    END;
    """
    # Sterownik podstawi tę jedną wartość w oba miejsca oznaczone jako :1
    return db.execute_dml(sql, [id_rezerwacji])

# --- SZLAKI ---

def get_szlaki():
    sql = """
        SELECT sz.id_szlaku, r.nazwa as region, sz.nazwa, sz.kolor, 
               sz.trudnosc, sz.dlugosc, sz.czas_przejscia
        FROM szlaki sz
        JOIN regiony r ON sz.id_regionu = r.id_regionu
        ORDER BY r.nazwa, sz.nazwa
    """
    return db.execute_query_df(sql)

def add_szlak(id_regionu, nazwa, kolor, trudnosc, dlugosc, czas):
    sql = """
        INSERT INTO szlaki (id_regionu, nazwa, kolor, trudnosc, dlugosc, czas_przejscia)
        VALUES (:1, :2, :3, :4, :5, :6)
    """
    return db.execute_dml(sql, [id_regionu, nazwa, kolor, trudnosc, dlugosc, czas])

def update_szlak(id_szlaku, nazwa, kolor, trudnosc, dlugosc, czas):
    sql = """
        UPDATE szlaki 
        SET nazwa = :1, kolor = :2, trudnosc = :3, dlugosc = :4, czas_przejscia = :5
        WHERE id_szlaku = :6
    """
    return db.execute_dml(sql, [nazwa, kolor, trudnosc, dlugosc, czas, id_szlaku])

def delete_szlak(id_szlaku):
    return db.execute_dml("DELETE FROM szlaki WHERE id_szlaku = :1", [id_szlaku])

# --- POKOJE ---
def get_pokoje_full():
    sql = """
        SELECT p.id_pokoju, s.nazwa as schronisko, p.nr_pokoju, 
               p.liczba_miejsc_calkowita, p.liczba_miejsc_wolnych, p.cena_za_noc
        FROM pokoje p
        JOIN schroniska s ON p.id_schroniska = s.id_schroniska
        ORDER BY s.nazwa, p.nr_pokoju
    """
    return db.execute_query_df(sql)

def update_pokoj(id_pokoju, nowa_cena, nowe_miejsca):
    sql = """
        UPDATE pokoje 
        SET cena_za_noc = :1, 
            liczba_miejsc_calkowita = :2,
            liczba_miejsc_wolnych = :3 
        WHERE id_pokoju = :4
    """
    return db.execute_dml(sql, [nowa_cena, nowe_miejsca, nowe_miejsca, id_pokoju])

def delete_pokoj(id_pokoju):
    return db.execute_dml("DELETE FROM pokoje WHERE id_pokoju = :1", [id_pokoju])

def add_pokoj(id_schroniska, nr_pokoju, miejsca, cena):
    sql = """
        INSERT INTO pokoje (id_schroniska, nr_pokoju, liczba_miejsc_calkowita, liczba_miejsc_wolnych, cena_za_noc)
        VALUES (:1, :2, :3, :4, :5)
    """
    return db.execute_dml(sql, [id_schroniska, nr_pokoju, miejsca, miejsca, cena])

# --- UZYTKOWNICY ---
def get_users_full():
    return db.execute_query_df("""
        SELECT id_uzytkownika, login, haslo, rola, imie, nazwisko, email 
        FROM uzytkownicy 
        ORDER BY nazwisko, imie
    """)

def add_user(login, haslo, rola, imie, nazwisko, email):
    sql = """
        INSERT INTO uzytkownicy (login, haslo, rola, imie, nazwisko, email)
        VALUES (:1, :2, :3, :4, :5, :6)
    """
    return db.execute_dml(sql, [login, haslo, rola, imie, nazwisko, email])

def update_user(id_user, login, haslo, rola, imie, nazwisko, email):
    sql = """
        UPDATE uzytkownicy 
        SET login = :1, haslo = :2, rola = :3, imie = :4, nazwisko = :5, email = :6
        WHERE id_uzytkownika = :7
    """
    return db.execute_dml(sql, [login, haslo, rola, imie, nazwisko, email, id_user])

def delete_user(id_user):
    return db.execute_dml("DELETE FROM uzytkownicy WHERE id_uzytkownika = :1", [id_user])