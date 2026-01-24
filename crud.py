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
    # Logika transakcyjna (Punkt -> Schronisko) w bloku PL/SQL
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

# --- REZERWACJE (PROCEDURY) ---
def get_users_dict():
    df = db.execute_query_df("SELECT id_uzytkownika, login, nazwisko FROM uzytkownicy")
    return {f"{row['LOGIN']} ({row['NAZWISKO']})": row['ID_UZYTKOWNIKA'] for i, row in df.iterrows()}

def get_pokoje_in_schronisko(id_schroniska):
    sql = "SELECT id_pokoju, nr_pokoju, cena_za_noc, liczba_miejsc_wolnych FROM pokoje WHERE id_schroniska = :1"
    return db.execute_query_df(sql, [id_schroniska])

def calculate_cost(id_pokoju, start, end, osoby):
    return db.execute_function("oblicz_koszt_pobytu", oracledb.NUMBER, [id_pokoju, start, end, osoby])

def make_reservation(id_pokoju, id_user, osoby, start, end):
    return db.execute_procedure("dokonaj_rezerwacji", [id_pokoju, id_user, osoby, start, end])

def get_user_reservations(id_user):
    sql = """
        SELECT r.id_rezerwacji, s.nazwa as schronisko, p.nr_pokoju, 
               r.data_rozpoczecia, r.data_zakonczenia, r.status_rez, r.kwota
        FROM rezerwacje r
        JOIN pokoje p ON r.id_pokoju = p.id_pokoju
        JOIN schroniska s ON p.id_schroniska = s.id_schroniska
        WHERE r.id_uzytkownika = :uid
        ORDER BY r.id_rezerwacji DESC
    """
    return db.execute_query_df(sql, [id_user])

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
    """Pobiera pokoje ze szczegółami schroniska do tabeli głównej"""
    sql = """
        SELECT p.id_pokoju, s.nazwa as schronisko, p.nr_pokoju, 
               p.liczba_miejsc_calkowita, p.liczba_miejsc_wolnych, p.cena_za_noc
        FROM pokoje p
        JOIN schroniska s ON p.id_schroniska = s.id_schroniska
        ORDER BY s.nazwa, p.nr_pokoju
    """
    return db.execute_query_df(sql)

def update_pokoj(id_pokoju, nowa_cena, nowe_miejsca):
    """
    Aktualizuje pokój. 
    POPRAWKA: Parametr 'nowe_miejsca' jest podany dwa razy, bo w SQL są placeholder-y :2 i :3.
    """
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
    """
    Dodaje nowy pokój.
    POPRAWKA: Parametr 'miejsca' jest podany dwa razy (dla całkowitych i wolnych).
    """
    sql = """
        INSERT INTO pokoje (id_schroniska, nr_pokoju, liczba_miejsc_calkowita, liczba_miejsc_wolnych, cena_za_noc)
        VALUES (:1, :2, :3, :4, :5)
    """
    return db.execute_dml(sql, [id_schroniska, nr_pokoju, miejsca, miejsca, cena])