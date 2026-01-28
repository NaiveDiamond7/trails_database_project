# --- ROOM RESERVATIONS (for calendar view) ---
def get_room_reservations(id_pokoju):
    sql = """
        SELECT data_rozpoczecia, data_zakonczenia
        FROM rezerwacje
        WHERE id_pokoju = :1 AND status_rez != 'anulowana'
        ORDER BY data_rozpoczecia
    """
    return db.execute_query_df(sql, [id_pokoju])
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
    ORDER BY s.nazwa
    """
    return db.execute_query_df(sql)

def add_schronisko_transaction(id_region, nazwa, wysokosc, otwarcie, zamkniecie, dlugosc=0, szerokosc=0):
    sql = """
    DECLARE
        v_id NUMBER;
    BEGIN
        INSERT INTO punkty (id_regionu, nazwa, typ, wysokosc, wspolrzedne_dlugosc, wspolrzedne_szerokosc)
        VALUES (:1, :2, 'Schronisko', :3, :4, :5)
        RETURNING id_punktu INTO v_id;

        INSERT INTO schroniska (id_schroniska, id_regionu, nazwa, wysokosc, godzina_otwarcia, godzina_zamkniecia)
        VALUES (v_id, :1, :2, :3, :6, :7);
    END;
    """
    # binding order: id_region, nazwa, wysokosc, dlugosc, szerokosc, otwarcie, zamkniecie
    params = [id_region, nazwa, wysokosc, dlugosc, szerokosc, otwarcie, zamkniecie]
    return db.execute_dml(sql, params)

def update_schronisko(id_schroniska, id_regionu, nazwa, wysokosc, otwarcie, zamkniecie):
    sql = """
    BEGIN
        UPDATE punkty 
        SET id_regionu = :1, nazwa = :2, wysokosc = :3
        WHERE id_punktu = :4;

        UPDATE schroniska
        SET id_regionu = :1, nazwa = :2, wysokosc = :3, 
            godzina_otwarcia = :5, godzina_zamkniecia = :6
        WHERE id_schroniska = :4;
    END;
    """
    return db.execute_dml(sql, [id_regionu, nazwa, wysokosc, id_schroniska, otwarcie, zamkniecie])

def delete_schronisko(id_schroniska):
    sql = """
    BEGIN
        DELETE FROM schroniska WHERE id_schroniska = :1;
        DELETE FROM punkty WHERE id_punktu = :1;
    END;
    """
    return db.execute_dml(sql, [id_schroniska])

# --- REZERWACJE ---
def get_users_dict():
    df = db.execute_query_df("SELECT id_uzytkownika, login, nazwisko FROM uzytkownicy")
    return {f"{row['LOGIN']} ({row['NAZWISKO']})": row['ID_UZYTKOWNIKA'] for i, row in df.iterrows()}

def get_pokoje_in_schronisko(id_schroniska):
    sql = """
        SELECT id_pokoju, nr_pokoju, cena_za_noc, liczba_miejsc_wolnych, liczba_miejsc_calkowita 
        FROM pokoje 
        WHERE id_schroniska = :1
        ORDER BY nr_pokoju
    """
    return db.execute_query_df(sql, [id_schroniska])

def calculate_cost(id_pokoju, start, end, osoby):
    return db.execute_function("oblicz_koszt_pobytu", oracledb.NUMBER, [id_pokoju, start, end, osoby])

def make_reservation(id_pokoju, id_user, osoby, start, end):
    """
    Tworzy rezerwację w MODELU HOTELOWYM (Na wyłączność).
    Jeśli pokój jest zajęty, zwraca informację, kiedy się zwolni.
    """
    
    # 1. Sprawdzenie pojemności (Czy pokój w ogóle mieści tyle osób?)
    cap_sql = "SELECT liczba_miejsc_calkowita FROM pokoje WHERE id_pokoju = :1"
    cap_df = db.execute_query_df(cap_sql, [id_pokoju])
    if cap_df.empty:
        return False, "Błąd: Nie znaleziono pokoju."
    max_cap = cap_df.iloc[0]['LICZBA_MIEJSC_CALKOWITA']
    if osoby > max_cap:
        return False, f"Ten pokój mieści maksymalnie {max_cap} osób. Chcesz zarezerwować dla {osoby}."

    # 2. Sprawdzenie sumy osób na każdy dzień
    import pandas as pd
    res_sql = """
        SELECT data_rozpoczecia, data_zakonczenia, liczba_osob
        FROM rezerwacje
        WHERE id_pokoju = :1 AND status_rez != 'anulowana'
    """
    res_df = db.execute_query_df(res_sql, [id_pokoju])
    busy_count = {}
    for i, row in res_df.iterrows():
        rng = pd.date_range(row['DATA_ROZPOCZECIA'], row['DATA_ZAKONCZENIA'] - pd.Timedelta(days=1))
        for d in rng.date:
            busy_count[d] = busy_count.get(d, 0) + int(row.get('LICZBA_OSOB', 1))
    wybrane = list(pd.date_range(start, end - pd.Timedelta(days=1)).date)
    for d in wybrane:
        occ = busy_count.get(d, 0)
        if occ + osoby > max_cap:
            return False, "Wybrany termin przekracza pojemność pokoju w niektóre dni!"

    # 3. Jeśli czysto -> Rezerwujemy (współdzielenie, bez zmiany liczba_miejsc_wolnych)
    # Oblicz koszt
    koszt = db.execute_function("oblicz_koszt_pobytu", oracledb.NUMBER, [id_pokoju, start, end, osoby])
    if koszt is None:
        return False, "Nie można obliczyć kosztu pobytu."
    sql = """
    DECLARE
        v_id_pokoj NUMBER := :1;
        v_id_user NUMBER := :2;
        v_osob NUMBER := :3;
        v_start DATE := :4;
        v_end DATE := :5;
        v_kwota NUMBER := :6;
    BEGIN
        INSERT INTO rezerwacje (id_pokoju, id_uzytkownika, liczba_osob, data_rozpoczecia, data_zakonczenia, kwota, status_rez)
        VALUES (v_id_pokoj, v_id_user, v_osob, v_start, v_end, v_kwota, 'zlozona');

        BEGIN
            EXECUTE IMMEDIATE 'UPDATE pokoje SET liczba_miejsc_wolnych = liczba_miejsc_wolnych - :1 WHERE id_pokoju = :2' USING v_osob, v_id_pokoj;
        EXCEPTION WHEN OTHERS THEN
            NULL; -- kolumna moze nie istniec w schemacie, ignoruj
        END;
    END;
    """
    return db.execute_dml(sql, [id_pokoju, id_user, osoby, start, end, koszt])

def get_user_reservations(id_user):
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

def delete_reservation(id_rezerwacji):
    sql = """
    DECLARE
        v_pokoj NUMBER;
        v_osob NUMBER;
    BEGIN
        SELECT id_pokoju, liczba_osob INTO v_pokoj, v_osob
        FROM rezerwacje WHERE id_rezerwacji = :1;

        DELETE FROM rezerwacje WHERE id_rezerwacji = :1;

        BEGIN
            EXECUTE IMMEDIATE 'UPDATE pokoje SET liczba_miejsc_wolnych = liczba_miejsc_wolnych + :1 WHERE id_pokoju = :2' USING v_osob, v_pokoj;
        EXCEPTION WHEN OTHERS THEN
            NULL; -- kolumna moze nie istniec, ignoruj
        END;
    END;
    """
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
    """
    Pobiera pokoje oraz dynamicznie oblicza, ile osób mieszka w nich DZISIAJ.
    """
    sql = """
        SELECT p.id_pokoju, 
               s.nazwa as schronisko, 
               p.nr_pokoju, 
               p.liczba_miejsc_calkowita, 
               p.cena_za_noc,
               (
                   SELECT COALESCE(SUM(r.liczba_osob), 0)
                   FROM rezerwacje r
                   WHERE r.id_pokoju = p.id_pokoju
                     AND r.status_rez != 'anulowana'
                     AND TRUNC(SYSDATE) >= r.data_rozpoczecia 
                     AND TRUNC(SYSDATE) < r.data_zakonczenia
               ) as "ZAKWATEROWANI_DZIS"
        FROM pokoje p
        JOIN schroniska s ON p.id_schroniska = s.id_schroniska
        ORDER BY s.nazwa, p.nr_pokoju
    """
    return db.execute_query_df(sql)

def update_pokoj(id_pokoju, nowa_cena, nowe_miejsca):
    sql = """
    DECLARE
        v_id NUMBER := :3;
        v_cena NUMBER := :1;
        v_miejsca NUMBER := :2;
    BEGIN
        UPDATE pokoje 
        SET cena_za_noc = v_cena, 
            liczba_miejsc_calkowita = v_miejsca
        WHERE id_pokoju = v_id;

        BEGIN
            EXECUTE IMMEDIATE 'UPDATE pokoje SET liczba_miejsc_wolnych = :1 WHERE id_pokoju = :2' USING v_miejsca, v_id;
        EXCEPTION WHEN OTHERS THEN
            NULL; -- ignore if column missing
        END;
    END;
    """
    return db.execute_dml(sql, [nowa_cena, nowe_miejsca, id_pokoju])

def delete_pokoj(id_pokoju):
    return db.execute_dml("DELETE FROM pokoje WHERE id_pokoju = :1", [id_pokoju])

def add_pokoj(id_schroniska, nr_pokoju, miejsca, cena):
    sql = """
    DECLARE
        v_id_s NUMBER := :1;
        v_nr VARCHAR2(100) := :2;
        v_m NUMBER := :3;
        v_c NUMBER := :4;
    BEGIN
        INSERT INTO pokoje (id_schroniska, nr_pokoju, liczba_miejsc_calkowita, cena_za_noc)
        VALUES (v_id_s, v_nr, v_m, v_c);

        BEGIN
            EXECUTE IMMEDIATE 'UPDATE pokoje SET liczba_miejsc_wolnych = :1 WHERE id_schroniska = :2 AND nr_pokoju = :3' USING v_m, v_id_s, v_nr;
        EXCEPTION WHEN OTHERS THEN
            NULL; -- jeżeli kolumna nie istnieje w schemacie, ignoruj
        END;
    END;
    """
    return db.execute_dml(sql, [id_schroniska, nr_pokoju, miejsca, cena])

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
    try:
        return db.execute_dml(sql, [login, haslo, rola, imie, nazwisko, email])
    except Exception as e:
        msg = str(e).lower()
        if 'unique constraint' in msg and ('login' in msg or 'email' in msg):
            return False, 'Użytkownik o podanym loginie lub adresie email już istnieje.'
        return False, f'Błąd: {e}'

def update_user(id_user, login, haslo, rola, imie, nazwisko, email):
    sql = """
        UPDATE uzytkownicy 
        SET login = :1, haslo = :2, rola = :3, imie = :4, nazwisko = :5, email = :6
        WHERE id_uzytkownika = :7
    """
    return db.execute_dml(sql, [login, haslo, rola, imie, nazwisko, email, id_user])

def delete_user(id_user):
    return db.execute_dml("DELETE FROM uzytkownicy WHERE id_uzytkownika = :1", [id_user])

# --- WYPOSAŻENIA ---
def get_wyposazenia():
    return db.execute_query_df("SELECT id_wyposazenia, nazwa FROM wyposazenia ORDER BY nazwa")

def add_wyposazenie(nazwa):
    return db.execute_dml("INSERT INTO wyposazenia (nazwa) VALUES (:1)", [nazwa])

def update_wyposazenie(id_wyposazenia, nazwa):
    return db.execute_dml("UPDATE wyposazenia SET nazwa = :1 WHERE id_wyposazenia = :2", [nazwa, id_wyposazenia])

def delete_wyposazenie(id_wyposazenia):
    return db.execute_dml("DELETE FROM wyposazenia WHERE id_wyposazenia = :1", [id_wyposazenia])

# --- SCHRONISKA_WYPOSAŻENIE ---
def get_schroniska_wyposazenie(id_schroniska):
    sql = """
        SELECT w.id_wyposazenia, w.nazwa
        FROM schroniska_wyposazenie sw
        JOIN wyposazenia w ON sw.id_wyposazenia = w.id_wyposazenia
        WHERE sw.id_schroniska = :1
        ORDER BY w.nazwa
    """
    return db.execute_query_df(sql, [id_schroniska])

def add_schronisko_wyposazenie(id_schroniska, id_wyposazenia):
    return db.execute_dml("INSERT INTO schroniska_wyposazenie (id_schroniska, id_wyposazenia) VALUES (:1, :2)", [id_schroniska, id_wyposazenia])

def delete_schronisko_wyposazenie(id_schroniska, id_wyposazenia):
    return db.execute_dml("DELETE FROM schroniska_wyposazenie WHERE id_schroniska = :1 AND id_wyposazenia = :2", [id_schroniska, id_wyposazenia])

# --- POKOJE_WYPOSAŻENIE ---
def get_pokoje_wyposazenie(id_pokoju):
    sql = """
        SELECT w.id_wyposazenia, w.nazwa
        FROM pokoje_wyposazenie pw
        JOIN wyposazenia w ON pw.id_wyposazenia = w.id_wyposazenia
        WHERE pw.id_pokoju = :1
        ORDER BY w.nazwa
    """
    return db.execute_query_df(sql, [id_pokoju])

def add_pokoj_wyposazenie(id_pokoju, id_wyposazenia):
    return db.execute_dml("INSERT INTO pokoje_wyposazenie (id_pokoju, id_wyposazenia) VALUES (:1, :2)", [id_pokoju, id_wyposazenia])

def delete_pokoj_wyposazenie(id_pokoju, id_wyposazenia):
    return db.execute_dml("DELETE FROM pokoje_wyposazenie WHERE id_pokoju = :1 AND id_wyposazenia = :2", [id_pokoju, id_wyposazenia])

# --- PUNKTY ---
def get_punkty():
    return db.execute_query_df("SELECT id_punktu, id_regionu, nazwa, typ, wysokosc, wspolrzedne_dlugosc, wspolrzedne_szerokosc FROM punkty ORDER BY id_punktu")

def add_punkt(id_regionu, nazwa, typ, wysokosc, dlugosc, szerokosc):
    sql = "INSERT INTO punkty (id_regionu, nazwa, typ, wysokosc, wspolrzedne_dlugosc, wspolrzedne_szerokosc) VALUES (:1, :2, :3, :4, :5, :6)"
    return db.execute_dml(sql, [id_regionu, nazwa, typ, wysokosc, dlugosc, szerokosc])

def update_punkt(id_punktu, id_regionu, nazwa, typ, wysokosc, dlugosc, szerokosc):
    sql = "UPDATE punkty SET id_regionu = :1, nazwa = :2, typ = :3, wysokosc = :4, wspolrzedne_dlugosc = :5, wspolrzedne_szerokosc = :6 WHERE id_punktu = :7"
    return db.execute_dml(sql, [id_regionu, nazwa, typ, wysokosc, dlugosc, szerokosc, id_punktu])

def delete_punkt(id_punktu):
    return db.execute_dml("DELETE FROM punkty WHERE id_punktu = :1", [id_punktu])

# --- ODLEGLOSCI_MIEDZY_PUNKTAMI ---
def get_odleglosci():
    return db.execute_query_df("SELECT id_pkt_od, id_pkt_do, odleglosc, przewyzszenie, czas_przejscia FROM odleglosci_miedzy_punktami ORDER BY id_pkt_od, id_pkt_do")

def add_odleglosc(id_pkt_od, id_pkt_do, odleglosc, przewyzszenie, czas_przejscia):
    sql = "INSERT INTO odleglosci_miedzy_punktami (id_pkt_od, id_pkt_do, odleglosc, przewyzszenie, czas_przejscia) VALUES (:1, :2, :3, :4, :5)"
    return db.execute_dml(sql, [id_pkt_od, id_pkt_do, odleglosc, przewyzszenie, czas_przejscia])

def update_odleglosc(id_pkt_od, id_pkt_do, odleglosc, przewyzszenie, czas_przejscia):
    sql = "UPDATE odleglosci_miedzy_punktami SET odleglosc = :1, przewyzszenie = :2, czas_przejscia = :3 WHERE id_pkt_od = :4 AND id_pkt_do = :5"
    return db.execute_dml(sql, [odleglosc, przewyzszenie, czas_przejscia, id_pkt_od, id_pkt_do])

def delete_odleglosc(id_pkt_od, id_pkt_do):
    return db.execute_dml("DELETE FROM odleglosci_miedzy_punktami WHERE id_pkt_od = :1 AND id_pkt_do = :2", [id_pkt_od, id_pkt_do])

# --- KOLEJNOSCI ---
def get_kolejnosci():
    return db.execute_query_df("SELECT id_szlaku_kol, id_punktu, kolejnosc_na_szlaku FROM kolejnosci ORDER BY id_szlaku_kol, kolejnosc_na_szlaku")

def add_kolejnosc(id_szlaku_kol, id_punktu, kolejnosc_na_szlaku):
    sql = "INSERT INTO kolejnosci (id_szlaku_kol, id_punktu, kolejnosc_na_szlaku) VALUES (:1, :2, :3)"
    return db.execute_dml(sql, [id_szlaku_kol, id_punktu, kolejnosc_na_szlaku])

def update_kolejnosc(id_szlaku_kol, id_punktu, kolejnosc_na_szlaku):
    sql = "UPDATE kolejnosci SET kolejnosc_na_szlaku = :1 WHERE id_szlaku_kol = :2 AND id_punktu = :3"
    return db.execute_dml(sql, [kolejnosc_na_szlaku, id_szlaku_kol, id_punktu])

def delete_kolejnosc(id_szlaku_kol, id_punktu, kolejnosc_na_szlaku):
    return db.execute_dml("DELETE FROM kolejnosci WHERE id_szlaku_kol = :1 AND id_punktu = :2 AND kolejnosc_na_szlaku = :3", [id_szlaku_kol, id_punktu, kolejnosc_na_szlaku])