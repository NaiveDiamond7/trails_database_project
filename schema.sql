DROP TABLE rezerwacje CASCADE CONSTRAINTS;
DROP TABLE pokoje_wyposazenie CASCADE CONSTRAINTS;
DROP TABLE schroniska_wyposazenie CASCADE CONSTRAINTS;
DROP TABLE pokoje CASCADE CONSTRAINTS;
DROP TABLE schroniska CASCADE CONSTRAINTS;
DROP TABLE wyposazenia CASCADE CONSTRAINTS;
DROP TABLE kolejnosci CASCADE CONSTRAINTS;
DROP TABLE szlaki CASCADE CONSTRAINTS;
DROP TABLE odleglosci_miedzy_punktami CASCADE CONSTRAINTS;
DROP TABLE regiony CASCADE CONSTRAINTS;
DROP TABLE punkty CASCADE CONSTRAINTS;
DROP TABLE uzytkownicy CASCADE CONSTRAINTS;

CREATE TABLE regiony (
    id_regionu NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nazwa VARCHAR2(100) NOT NULL,
    UNIQUE(nazwa)
);

CREATE TABLE punkty (
    id_punktu NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_regionu NUMBER REFERENCES regiony(id_regionu) NOT NULL,
    nazwa VARCHAR2(100) NOT NULL,
    typ VARCHAR2(100) NOT NULL,
    wysokosc NUMBER(6, 2) NOT NULL,
    wspolrzedne_dlugosc NUMBER(9, 6) NOT NULL,
    wspolrzedne_szerokosc NUMBER(9, 6) NOT NULL,
    CONSTRAINT wysokosc_punkty_chk CHECK (wysokosc BETWEEN 0 AND 8851),
    UNIQUE(nazwa)
);

CREATE TABLE odleglosci_miedzy_punktami (
    id_pkt_od NUMBER REFERENCES punkty(id_punktu) NOT NULL,
    id_pkt_do NUMBER REFERENCES punkty(id_punktu) NOT NULL,
    odleglosc NUMBER(7, 3) NOT NULL,
    przewyzszenie NUMBER(6, 3) NOT NULL,
    czas_przejscia NUMBER(3),
    CONSTRAINT nazwy_pkt_chk CHECK (id_pkt_od <> id_pkt_do),
    CONSTRAINT odl_pkt_chk CHECK (odleglosc > 0),
    CONSTRAINT czas_pkt_chk CHECK (czas_przejscia > 0),
    PRIMARY KEY (id_pkt_od, id_pkt_do)
);

CREATE TABLE szlaki (
    id_szlaku NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_regionu NUMBER REFERENCES regiony(id_regionu) NOT NULL,
    kolor VARCHAR2(20) NOT NULL CHECK (kolor IN ('CZERWONY', 'NIEBIESKI', 'ZIELONY', 'ZOLTY', 'CZARNY', 'INNY')),
    nazwa VARCHAR2(100) NOT NULL,
    trudnosc VARCHAR2(30) NOT NULL, 
    dlugosc NUMBER(6, 2) NOT NULL,
    czas_przejscia NUMBER(3) NOT NULL,
    CONSTRAINT czas_szlaki_chk CHECK (czas_przejscia > 0),
    CONSTRAINT dlugosc_szlaki_chk CHECK(dlugosc > 0),
    CONSTRAINT trudnosc_chk CHECK (trudnosc IN('SPACEROWY', 'BARDZO LATWY', 'LATWY', 'SREDNIOZAAWANSOWANY', 'ZAAWANSOWANY', 'EKSPERCKI'))
);

CREATE TABLE kolejnosci (
    id_szlaku_kol NUMBER REFERENCES szlaki(id_szlaku) NOT NULL,
    id_punktu NUMBER REFERENCES punkty(id_punktu) NOT NULL,
    kolejnosc_na_szlaku NUMBER(2) NOT NULL,
    UNIQUE(id_szlaku_kol, kolejnosc_na_szlaku),
    PRIMARY KEY (id_szlaku_kol, id_punktu, kolejnosc_na_szlaku)
);

CREATE TABLE wyposazenia (
    id_wyposazenia NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nazwa VARCHAR2(100) NOT NULL,
    UNIQUE(nazwa)
);

CREATE TABLE schroniska (
    id_schroniska NUMBER REFERENCES punkty(id_punktu) NOT NULL,
    id_regionu NUMBER REFERENCES regiony(id_regionu) NOT NULL, 
    nazwa VARCHAR2(100) NOT NULL,
    wysokosc NUMBER(6, 2) NOT NULL,
    godzina_otwarcia VARCHAR2(5) CHECK (REGEXP_LIKE(godzina_otwarcia, '^([0-1][0-9]|2[0-3]):[0-5][0-9]$')) NOT NULL,
    godzina_zamkniecia VARCHAR2(5) CHECK (REGEXP_LIKE(godzina_zamkniecia, '^([0-1][0-9]|2[0-3]):[0-5][0-9]$')) NOT NULL,
    CONSTRAINT schr_wys_chk CHECK (wysokosc > 0),
    CONSTRAINT schroniska_region_nazwa_uk UNIQUE (id_regionu, nazwa),
    PRIMARY KEY (id_schroniska)
);

CREATE TABLE schroniska_wyposazenie (
    id_schroniska NUMBER REFERENCES schroniska(id_schroniska) NOT NULL,
    id_wyposazenia NUMBER REFERENCES wyposazenia(id_wyposazenia) NOT NULL,
    PRIMARY KEY (id_schroniska, id_wyposazenia)
);

CREATE TABLE pokoje (
    id_pokoju NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_schroniska NUMBER REFERENCES schroniska(id_schroniska) NOT NULL,
    nr_pokoju NUMBER(3) NOT NULL,
    liczba_miejsc_calkowita NUMBER(3) NOT NULL,
    liczba_miejsc_wolnych NUMBER(3) NOT NULL,
    cena_za_noc NUMBER(6, 2) NOT NULL,
    CONSTRAINT pokoje_miejsca_calk CHECK (liczba_miejsc_calkowita > 0),
    CONSTRAINT pokoje_miejsca_woln CHECK (liczba_miejsc_wolnych >= 0),
    CONSTRAINT pokoje_miejsca_logika CHECK (liczba_miejsc_wolnych <= liczba_miejsc_calkowita),
    CONSTRAINT nic_za_darmo CHECK (cena_za_noc > 0),
    UNIQUE(id_schroniska, nr_pokoju)
);

CREATE TABLE pokoje_wyposazenie (
    id_pokoju NUMBER REFERENCES pokoje(id_pokoju) NOT NULL,
    id_wyposazenia NUMBER REFERENCES wyposazenia(id_wyposazenia) NOT NULL,
    PRIMARY KEY (id_pokoju, id_wyposazenia)
);

CREATE TABLE uzytkownicy (
    id_uzytkownika NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    login VARCHAR2(30) NOT NULL,
    haslo VARCHAR2(100) NOT NULL,
    rola VARCHAR2(1) NOT NULL,
    imie VARCHAR2(100),
    nazwisko VARCHAR2(100) NOT NULL,
    email VARCHAR2(100) NOT NULL,
    CONSTRAINT uzytk_rola_chk CHECK (rola IN ('u', 'p')), 
    CONSTRAINT email_format_chk CHECK (REGEXP_LIKE(email, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')),
    UNIQUE(login),
    UNIQUE(email)
);

CREATE TABLE rezerwacje (
    id_rezerwacji NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pokoju NUMBER REFERENCES pokoje(id_pokoju) NOT NULL,
    id_uzytkownika NUMBER REFERENCES uzytkownicy(id_uzytkownika) NOT NULL,
    liczba_osob NUMBER(2) NOT NULL,
    data_rozpoczecia DATE NOT NULL,
    data_zakonczenia DATE NOT NULL,
    kwota NUMBER(8, 2) NOT NULL,
    status_rez VARCHAR2(20) NOT NULL,
    liczba_gwiazdek_opinia NUMBER(1),
    tresc_opinii VARCHAR2(300),
    CONSTRAINT rez_data_zak_chk CHECK (data_zakonczenia > data_rozpoczecia),
    CONSTRAINT rez_status_chk CHECK (status_rez IN ('zlozona', 'potwierdzona', 'oplacona', 'anulowana', 'zakonczona')),
    CONSTRAINT rez_lb_gwiazdek CHECK (liczba_gwiazdek_opinia BETWEEN 0 AND 5),
    CONSTRAINT rezerwacje_pokoj_daty_uk UNIQUE (id_pokoju, data_rozpoczecia, data_zakonczenia)
);

CREATE OR REPLACE FUNCTION oblicz_koszt_pobytu(
    p_id_pokoju IN NUMBER,
    p_data_rozp IN DATE,
    p_data_zak IN DATE,
    p_liczba_osob IN NUMBER
) RETURN NUMBER IS
    v_cena_za_noc NUMBER;
    v_liczba_dni NUMBER;
BEGIN
    SELECT cena_za_noc INTO v_cena_za_noc
    FROM pokoje
    WHERE id_pokoju = p_id_pokoju;

    v_liczba_dni := p_data_zak - p_data_rozp;

    IF v_liczba_dni <= 0 THEN
        RETURN 0;
    END IF;

    RETURN v_liczba_dni * v_cena_za_noc * p_liczba_osob;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN NULL;
END;
/

CREATE OR REPLACE PROCEDURE dokonaj_rezerwacji(
    p_id_pokoju IN NUMBER,
    p_id_uzytkownika IN NUMBER,
    p_liczba_osob IN NUMBER,
    p_data_rozp IN DATE,
    p_data_zak IN DATE
) IS
    v_wolne_miejsca NUMBER;
    v_koszt NUMBER;
BEGIN
    SELECT liczba_miejsc_wolnych INTO v_wolne_miejsca
    FROM pokoje
    WHERE id_pokoju = p_id_pokoju
    FOR UPDATE;

    IF v_wolne_miejsca < p_liczba_osob THEN
        RAISE_APPLICATION_ERROR(-20001, 'Brak wystarczającej liczby wolnych miejsc w tym pokoju.');
    END IF;

    v_koszt := oblicz_koszt_pobytu(p_id_pokoju, p_data_rozp, p_data_zak, p_liczba_osob);

    INSERT INTO rezerwacje (
        id_pokoju, id_uzytkownika, liczba_osob, data_rozpoczecia, 
        data_zakonczenia, kwota, status_rez
    ) VALUES (
        p_id_pokoju, p_id_uzytkownika, p_liczba_osob, p_data_rozp, 
        p_data_zak, v_koszt, 'zlozona'
    );

    UPDATE pokoje
    SET liczba_miejsc_wolnych = liczba_miejsc_wolnych - p_liczba_osob
    WHERE id_pokoju = p_id_pokoju;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Rezerwacja dokonana pomyślnie. Koszt: ' || v_koszt);
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END;
/