-- 1. REGIONY
INSERT INTO regiony (nazwa) VALUES ('Tatry');
INSERT INTO regiony (nazwa) VALUES ('Karkonosze');
INSERT INTO regiony (nazwa) VALUES ('Bieszczady');

-- 2. WYPOSAZENIA
INSERT INTO wyposazenia (nazwa) VALUES ('Wi-Fi');
INSERT INTO wyposazenia (nazwa) VALUES ('Prysznic');
INSERT INTO wyposazenia (nazwa) VALUES ('Wspólna kuchnia');
INSERT INTO wyposazenia (nazwa) VALUES ('Pościel');
INSERT INTO wyposazenia (nazwa) VALUES ('Ręczniki');
INSERT INTO wyposazenia (nazwa) VALUES ('Bufet');

-- 3. UZYTKOWNICY
INSERT INTO uzytkownicy (login, haslo, rola, imie, nazwisko, email) 
VALUES ('admin', 'admin123', 'p', 'Adam', 'Administrator', 'admin@system.pl');

INSERT INTO uzytkownicy (login, haslo, rola, imie, nazwisko, email) 
VALUES ('jan_kowalski', 'user123', 'u', 'Jan', 'Kowalski', 'jan@poczta.pl');

INSERT INTO uzytkownicy (login, haslo, rola, imie, nazwisko, email) 
VALUES ('anna_nowak', 'user123', 'u', 'Anna', 'Nowak', 'anna@poczta.pl');

-- 4. PUNKTY I SCHRONISKA (Bloki PL/SQL dla zachowania spójności ID)

-- Punkt zwykły: Kuźnice
INSERT INTO punkty (id_regionu, nazwa, typ, wysokosc, wspolrzedne_dlugosc, wspolrzedne_szerokosc)
VALUES ((SELECT id_regionu FROM regiony WHERE nazwa='Tatry'), 'Kuźnice', 'Szczyt/Przełęcz', 1010, 49.966, 19.980);

-- Punkt zwykły: Kasprowy Wierch
INSERT INTO punkty (id_regionu, nazwa, typ, wysokosc, wspolrzedne_dlugosc, wspolrzedne_szerokosc)
VALUES ((SELECT id_regionu FROM regiony WHERE nazwa='Tatry'), 'Kasprowy Wierch', 'Szczyt/Przełęcz', 1987, 49.931, 19.981);

-- Schronisko: Murowaniec
DECLARE
    v_reg_id NUMBER;
    v_pkt_id NUMBER;
BEGIN
    SELECT id_regionu INTO v_reg_id FROM regiony WHERE nazwa='Tatry';
    
    INSERT INTO punkty (id_regionu, nazwa, typ, wysokosc, wspolrzedne_dlugosc, wspolrzedne_szerokosc)
    VALUES (v_reg_id, 'Schronisko Murowaniec', 'Schronisko', 1500, 49.243, 20.007)
    RETURNING id_punktu INTO v_pkt_id;
    
    INSERT INTO schroniska (id_schroniska, id_regionu, nazwa, wysokosc, godzina_otwarcia, godzina_zamkniecia)
    VALUES (v_pkt_id, v_reg_id, 'Schronisko Murowaniec', 1500, '07:00', '22:00');
END;
/

-- Schronisko: Morskie Oko
DECLARE
    v_reg_id NUMBER;
    v_pkt_id NUMBER;
BEGIN
    SELECT id_regionu INTO v_reg_id FROM regiony WHERE nazwa='Tatry';
    
    INSERT INTO punkty (id_regionu, nazwa, typ, wysokosc, wspolrzedne_dlugosc, wspolrzedne_szerokosc)
    VALUES (v_reg_id, 'Schronisko Morskie Oko', 'Schronisko', 1410, 49.201, 20.071)
    RETURNING id_punktu INTO v_pkt_id;
    
    INSERT INTO schroniska (id_schroniska, id_regionu, nazwa, wysokosc, godzina_otwarcia, godzina_zamkniecia)
    VALUES (v_pkt_id, v_reg_id, 'Schronisko Morskie Oko', 1410, '08:00', '21:00');
END;
/

-- Schronisko: Samotnia (Karkonosze)
DECLARE
    v_reg_id NUMBER;
    v_pkt_id NUMBER;
BEGIN
    SELECT id_regionu INTO v_reg_id FROM regiony WHERE nazwa='Karkonosze';
    
    INSERT INTO punkty (id_regionu, nazwa, typ, wysokosc, wspolrzedne_dlugosc, wspolrzedne_szerokosc)
    VALUES (v_reg_id, 'Schronisko Samotnia', 'Schronisko', 1195, 50.748, 15.702)
    RETURNING id_punktu INTO v_pkt_id;
    
    INSERT INTO schroniska (id_schroniska, id_regionu, nazwa, wysokosc, godzina_otwarcia, godzina_zamkniecia)
    VALUES (v_pkt_id, v_reg_id, 'Schronisko Samotnia', 1195, '08:00', '20:00');
END;
/

-- 5. POKOJE
-- Pokoje w Murowańcu
INSERT INTO pokoje (id_schroniska, nr_pokoju, liczba_miejsc_calkowita, cena_za_noc)
VALUES ((SELECT id_schroniska FROM schroniska WHERE nazwa='Schronisko Murowaniec'), 101, 2, 120.00);

INSERT INTO pokoje (id_schroniska, nr_pokoju, liczba_miejsc_calkowita, cena_za_noc)
VALUES ((SELECT id_schroniska FROM schroniska WHERE nazwa='Schronisko Murowaniec'), 102, 4, 80.00);

INSERT INTO pokoje (id_schroniska, nr_pokoju, liczba_miejsc_calkowita, cena_za_noc)
VALUES ((SELECT id_schroniska FROM schroniska WHERE nazwa='Schronisko Murowaniec'), 103, 6, 60.00);

-- Pokoje w Morskim Oku
INSERT INTO pokoje (id_schroniska, nr_pokoju, liczba_miejsc_calkowita, cena_za_noc)
VALUES ((SELECT id_schroniska FROM schroniska WHERE nazwa='Schronisko Morskie Oko'), 1, 2, 150.00);

INSERT INTO pokoje (id_schroniska, nr_pokoju, liczba_miejsc_calkowita, cena_za_noc)
VALUES ((SELECT id_schroniska FROM schroniska WHERE nazwa='Schronisko Morskie Oko'), 2, 10, 40.00);

-- Pokoje w Samotni
INSERT INTO pokoje (id_schroniska, nr_pokoju, liczba_miejsc_calkowita, cena_za_noc)
VALUES ((SELECT id_schroniska FROM schroniska WHERE nazwa='Schronisko Samotnia'), 5, 2, 100.00);

-- 6. SZLAKI
DECLARE
    v_reg_id NUMBER;
BEGIN
    SELECT id_regionu INTO v_reg_id FROM regiony WHERE nazwa='Tatry';

    INSERT INTO szlaki (id_regionu, kolor, nazwa, trudnosc, dlugosc, czas_przejscia)
    VALUES (v_reg_id, 'NIEBIESKI', 'Szlak na Halę Gąsienicową', 'LATWY', 4.5, 90);
    
    INSERT INTO szlaki (id_regionu, kolor, nazwa, trudnosc, dlugosc, czas_przejscia)
    VALUES (v_reg_id, 'ZOLTY', 'Szlak na Kasprowy Wierch', 'SREDNIOZAAWANSOWANY', 6.2, 150);
END;
/

-- 7. KOLEJNOSCI NA SZLAKU
-- Szlak Niebieski: Kuźnice -> Murowaniec
INSERT INTO kolejnosci (id_szlaku_kol, id_punktu, kolejnosc_na_szlaku)
VALUES (
    (SELECT id_szlaku FROM szlaki WHERE nazwa='Szlak na Halę Gąsienicową'),
    (SELECT id_punktu FROM punkty WHERE nazwa='Kuźnice'),
    1
);

INSERT INTO kolejnosci (id_szlaku_kol, id_punktu, kolejnosc_na_szlaku)
VALUES (
    (SELECT id_szlaku FROM szlaki WHERE nazwa='Szlak na Halę Gąsienicową'),
    (SELECT id_punktu FROM punkty WHERE nazwa='Schronisko Murowaniec'),
    2
);

-- Szlak Żółty: Murowaniec -> Kasprowy Wierch
INSERT INTO kolejnosci (id_szlaku_kol, id_punktu, kolejnosc_na_szlaku)
VALUES (
    (SELECT id_szlaku FROM szlaki WHERE nazwa='Szlak na Kasprowy Wierch'),
    (SELECT id_punktu FROM punkty WHERE nazwa='Schronisko Murowaniec'),
    1
);

INSERT INTO kolejnosci (id_szlaku_kol, id_punktu, kolejnosc_na_szlaku)
VALUES (
    (SELECT id_szlaku FROM szlaki WHERE nazwa='Szlak na Kasprowy Wierch'),
    (SELECT id_punktu FROM punkty WHERE nazwa='Kasprowy Wierch'),
    2
);


-- 8. SCHRONISKA_WYPOSAZENIE
INSERT INTO schroniska_wyposazenie (id_schroniska, id_wyposazenia)
VALUES (
    (SELECT id_schroniska FROM schroniska WHERE nazwa='Schronisko Murowaniec'),
    (SELECT id_wyposazenia FROM wyposazenia WHERE nazwa='Wi-Fi')
);

INSERT INTO schroniska_wyposazenie (id_schroniska, id_wyposazenia)
VALUES (
    (SELECT id_schroniska FROM schroniska WHERE nazwa='Schronisko Murowaniec'),
    (SELECT id_wyposazenia FROM wyposazenia WHERE nazwa='Bufet')
);


-- 9. POKOJE_WYPOSAZENIE
INSERT INTO pokoje_wyposazenie (id_pokoju, id_wyposazenia)
VALUES (
    (SELECT id_pokoju FROM pokoje WHERE nr_pokoju=101 AND id_schroniska=(SELECT id_schroniska FROM schroniska WHERE nazwa='Schronisko Murowaniec')),
    (SELECT id_wyposazenia FROM wyposazenia WHERE nazwa='Prysznic')
);


-- 10. REZERWACJE
-- Jan rezerwuje pokój 101 w Murowańcu
INSERT INTO rezerwacje (id_pokoju, id_uzytkownika, liczba_osob, data_rozpoczecia, data_zakonczenia, kwota, status_rez)
VALUES (
    (SELECT id_pokoju FROM pokoje WHERE nr_pokoju=101 AND id_schroniska=(SELECT id_schroniska FROM schroniska WHERE nazwa='Schronisko Murowaniec')),
    (SELECT id_uzytkownika FROM uzytkownicy WHERE login='jan_kowalski'),
    2,
    TO_DATE('2025-06-01', 'YYYY-MM-DD'),
    TO_DATE('2025-06-03', 'YYYY-MM-DD'),
    240.00, 
    'potwierdzona'
);

-- Anna rezerwuje pokój w Morskim Oku
INSERT INTO rezerwacje (id_pokoju, id_uzytkownika, liczba_osob, data_rozpoczecia, data_zakonczenia, kwota, status_rez)
VALUES (
    (SELECT id_pokoju FROM pokoje WHERE nr_pokoju=1 AND id_schroniska=(SELECT id_schroniska FROM schroniska WHERE nazwa='Schronisko Morskie Oko')),
    (SELECT id_uzytkownika FROM uzytkownicy WHERE login='anna_nowak'),
    2,
    TO_DATE('2025-07-10', 'YYYY-MM-DD'),
    TO_DATE('2025-07-15', 'YYYY-MM-DD'),
    750.00,
    'oplacona'
);

COMMIT;