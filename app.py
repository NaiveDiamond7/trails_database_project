import streamlit as st
import crud
import datetime

# --- WIDOKI ---

def view_regiony():
    st.header("Zarządzanie Regionami")

    df = crud.get_regiony()
    st.dataframe(df, width="stretch")

    with st.expander("Dodaj nowy region"):
        with st.form("add_region"):
            new_name = st.text_input("Nazwa")
            if st.form_submit_button("Zapisz"):
                success, msg = crud.add_region(new_name)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with st.expander("Usuń region"):
        opts = {f"{row['NAZWA']}": row['ID_REGIONU'] for i, row in df.iterrows()}
        sel = st.selectbox("Wybierz", list(opts.keys()))
        if st.button("Usuń"):
            success, msg = crud.delete_region(opts[sel])
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

def view_schroniska():
    st.header("🏠 Zarządzanie Schroniskami")

    # Pobieranie regionów do formularzy (potrzebne w obu zakładkach)
    reg_df = crud.get_regiony()
    reg_opts = {row['NAZWA']: row['ID_REGIONU'] for i, row in reg_df.iterrows()}
    # Odwrócona mapa do ustawiania domyślnych wartości w edycji
    reg_rev = {row['ID_REGIONU']: row['NAZWA'] for i, row in reg_df.iterrows()}

    tab1, tab2 = st.tabs(["📋 Lista i Edycja", "➕ Dodaj nowe"])

    # === ZAKŁADKA 1: EDYCJA I USUWANIE ===
    with tab1:
        # Pobieranie danych
        df = crud.get_schroniska_view()

        # Wyszukiwanie
        search = st.text_input("Szukaj schroniska:", key="search_sch")
        if search:
            df = df[df['NAZWA'].str.contains(search, case=False)]

        st.dataframe(df, width="stretch")

        st.subheader("Edycja Schroniska")
        # Dropdown wyboru
        opts = {f"{row['NAZWA']}": row['ID_SCHRONISKA'] for i, row in df.iterrows()}
        sel_sch = st.selectbox("Wybierz schronisko do edycji", ["-- Wybierz --"] + list(opts.keys()))

        if sel_sch != "-- Wybierz --":
            s_id = opts[sel_sch]
            # Pobieramy wiersz danych z DataFrame
            cur = df[df['ID_SCHRONISKA'] == s_id].iloc[0]

            with st.form("edit_schronisko_form"):
                col1, col2 = st.columns(2)
                
                # Konwersja czasu string -> object (do formularza)
                try:
                    t_otw_obj = datetime.datetime.strptime(cur['GODZINA_OTWARCIA'], "%H:%M").time()
                    t_zam_obj = datetime.datetime.strptime(cur['GODZINA_ZAMKNIECIA'], "%H:%M").time()
                except:
                    t_otw_obj = datetime.time(8,0)
                    t_zam_obj = datetime.time(20,0)

                # Znalezienie indexu regionu
                # Pobieramy ID regionu z mapy nazw (trochę na około, bo w widoku mamy nazwę regionu, a potrzebujemy ID do update)
                curr_reg_name = cur['REGION']
                try:
                    curr_reg_id = reg_opts[curr_reg_name]
                    reg_index = list(reg_opts.keys()).index(curr_reg_name)
                except:
                    reg_index = 0

                with col1:
                    e_nazwa = st.text_input("Nazwa", value=cur['NAZWA'])
                    e_region = st.selectbox("Region", list(reg_opts.keys()), index=reg_index)
                    e_wys = st.number_input("Wysokość [m.n.p.m.]", 1, 8850, value=int(cur['WYSOKOSC']))
                with col2:
                    e_otw = st.time_input("Otwarcie", value=t_otw_obj)
                    e_zam = st.time_input("Zamknięcie", value=t_zam_obj)

                c_save, c_del = st.columns([1, 4])
                
                if c_save.form_submit_button("💾 Zaktualizuj"):
                    success, msg = crud.update_schronisko(
                        s_id, reg_opts[e_region], e_nazwa, e_wys, 
                        e_otw.strftime("%H:%M"), e_zam.strftime("%H:%M")
                    )
                    if success:
                        st.success("Zaktualizowano!")
                        st.rerun()
                    else:
                        st.error(msg)
                
                if c_del.form_submit_button("🗑️ Usuń schronisko", type="primary"):
                    success, msg = crud.delete_schronisko(s_id)
                    if success:
                        st.warning("Usunięto schronisko.")
                        st.rerun()
                    else:
                        st.error(msg)

    # === ZAKŁADKA 2: DODAWANIE ===
    with tab2:
        st.subheader("Nowe Schronisko")
        with st.form("add_schronisko"):
            col1, col2 = st.columns(2)
            with col1:
                nazwa = st.text_input("Nazwa")
                region = st.selectbox("Region", list(reg_opts.keys()), key="add_reg_sel")
                wys = st.number_input("Wysokość [m.n.p.m.]", 1, 8850)
            with col2:
                otw = st.time_input("Otwarcie", datetime.time(8,0))
                zam = st.time_input("Zamknięcie", datetime.time(20,0))
            
            if st.form_submit_button("Dodaj"):
                success, msg = crud.add_schronisko_transaction(
                    reg_opts[region], nazwa, wys, 
                    otw.strftime("%H:%M"), zam.strftime("%H:%M")
                )
                if success:
                    st.success("Dodano!")
                    st.rerun()
                else:
                    st.error(msg)

def view_rezerwacje():
    st.header("Rezerwacje")
    
    # 1. WYBÓR UŻYTKOWNIKA
    users = crud.get_users_dict()
    if not users:
        st.error("Brak użytkowników.")
        return
    
    col_u1, col_u2 = st.columns([1, 2])
    with col_u1:
        u_label = st.selectbox("Użytkownik (Rezerwujący)", list(users.keys()))
        u_id = users[u_label]

    # 2. NOWA REZERWACJA (Formularz)
    with st.expander("➕ Nowa rezerwacja", expanded=True): # Zmieniłem na expanded=True dla wygody testowania
        schroniska = crud.get_schroniska_view()
        if schroniska.empty:
            st.warning("Brak schronisk.")
        else:
            s_opts = {row['NAZWA']: row['ID_SCHRONISKA'] for i, row in schroniska.iterrows()}
            sel_sch = st.selectbox("Schronisko", list(s_opts.keys()))
            
            if sel_sch:
                pokoje = crud.get_pokoje_in_schronisko(s_opts[sel_sch])
                if pokoje.empty:
                    st.warning("Brak pokoi.")
                else:
                    capacity_map = {row['ID_POKOJU']: int(row['LICZBA_MIEJSC_CALKOWITA']) for i, row in pokoje.iterrows()}
                    
                    p_opts = {
                        f"Pokój {row['NR_POKOJU']} (Max: {row['LICZBA_MIEJSC_CALKOWITA']} os., {row['CENA_ZA_NOC']} PLN)": row['ID_POKOJU'] 
                        for i, row in pokoje.iterrows()
                    }
                    
                    sel_pok_label = st.selectbox("Pokój", list(p_opts.keys()))
                    sel_pok_id = p_opts[sel_pok_label]
                    
                    # Pobieramy max miejsc dla wybranego pokoju
                    max_osob = capacity_map[sel_pok_id]
                    
                    c1, c2 = st.columns(2)
                    d_start = c1.date_input("Od", datetime.date.today())
                    d_end = c2.date_input("Do", datetime.date.today() + datetime.timedelta(days=1))
                    
                    # ZMIANA: Zamiast Slidera -> Selectbox z listą od 1 do max_osob
                    osoby_options = list(range(1, max_osob + 1))
                    osoby = st.selectbox("Liczba osób", osoby_options)

                    col_btn1, col_btn2 = st.columns(2)
                    if col_btn1.button("Oblicz koszt"):
                        if d_end <= d_start:
                            st.error("Data końcowa musi być późniejsza.")
                        else:
                            val = crud.calculate_cost(sel_pok_id, d_start, d_end, osoby)
                            st.info(f"Koszt: {val} PLN")

                    if col_btn2.button("Rezerwuj", type="primary"):
                        if d_end <= d_start:
                            st.error("Data końcowa musi być późniejsza.")
                        else:
                            success, msg = crud.make_reservation(sel_pok_id, u_id, osoby, d_start, d_end)
                            if success:
                                st.success("Rezerwacja dokonana pomyślnie!")
                                st.rerun()
                            else:
                                st.error(msg)

    # 3. ZARZĄDZANIE REZERWACJAMI UŻYTKOWNIKA (USUWANIE)
    st.subheader(f"Aktywne rezerwacje użytkownika: {u_label.split(' (')[0]}")
    
    user_res_df = crud.get_user_reservations(u_id)
    
    if user_res_df.empty:
        st.info("Ten użytkownik nie ma żadnych rezerwacji.")
    else:
        res_opts = {}
        for i, row in user_res_df.iterrows():
            label = f"ID: {row['ID_REZERWACJI']} | {row['SCHRONISKO']} (P. {row['NR_POKOJU']}) | {row['DATA_ROZPOCZECIA']} - {row['DATA_ZAKONCZENIA']}"
            res_opts[label] = row['ID_REZERWACJI']
        
        col_del1, col_del2 = st.columns([3, 1])
        sel_res_to_del = col_del1.selectbox("Wybierz rezerwację do anulowania", list(res_opts.keys()))
        
        if col_del2.button("🗑️ Anuluj rezerwację"):
            res_id_del = res_opts[sel_res_to_del]
            success, msg = crud.delete_reservation(res_id_del)
            if success:
                st.success("Rezerwacja została anulowana, a miejsca zwolnione.")
                st.rerun()
            else:
                st.error(msg)
    
    # --- TABELA HISTORII ---
    st.divider()
    st.subheader("Globalna historia rezerwacji")
    
    df_rez = crud.get_all_reservations()
    
    show_only_selected = st.checkbox("Pokaż tylko dla wybranego użytkownika")
    if show_only_selected:
         st.dataframe(crud.get_user_reservations(u_id), width="stretch")
    else:
        st.dataframe(df_rez, width="stretch")

def view_szlaki_manager():
    st.header("🥾 Zarządzanie Szlakami")

    # --- SŁOWNIKI MAPUJĄCE (UI -> BAZA) ---
    # Klucz: To co widzi użytkownik (ładne PL)
    # Wartość: To co zapisujemy w bazie (bezpieczne ASCII)
    MAP_KOLOR = {
        'Czerwony': 'CZERWONY',
        'Niebieski': 'NIEBIESKI',
        'Zielony': 'ZIELONY',
        'Żółty': 'ZOLTY',
        'Czarny': 'CZARNY',
        'Inny': 'INNY'
    }
    
    MAP_TRUDNOSC = {
        'Spacerowy': 'SPACEROWY',
        'Bardzo łatwy': 'BARDZO LATWY',
        'Łatwy': 'LATWY',
        'Średniozaawansowany': 'SREDNIOZAAWANSOWANY',
        'Zaawansowany': 'ZAAWANSOWANY',
        'Ekspercki': 'EKSPERCKI'
    }

    # Słowniki odwrócone (BAZA -> UI) do wyświetlania w tabeli
    REV_KOLOR = {v: k for k, v in MAP_KOLOR.items()}
    REV_TRUDNOSC = {v: k for k, v in MAP_TRUDNOSC.items()}

    regions_df = crud.get_regiony()
    region_map = {row['NAZWA']: row['ID_REGIONU'] for i, row in regions_df.iterrows()}

    tab1, tab2 = st.tabs(["📋 Przegląd i Edycja", "➕ Dodaj nowy szlak"])

    with tab1:
        # Wyszukiwanie
        df = crud.get_szlaki()
        
        # TŁUMACZENIE TABELI: Podmieniamy kody z bazy na ładne nazwy PL
        if not df.empty:
            # Tworzymy kopie kolumn do wyświetlenia
            df['KOLOR_WYSWIETLANY'] = df['KOLOR'].map(REV_KOLOR).fillna(df['KOLOR'])
            df['TRUDNOSC_WYSWIETLANA'] = df['TRUDNOSC'].map(REV_TRUDNOSC).fillna(df['TRUDNOSC'])
            
            # Filtrowanie
            search = st.text_input("Szukaj szlaku (nazwa):", key="search_szlak")
            if search:
                df = df[df['NAZWA'].str.contains(search, case=False)]
            
            # Wybieramy co pokazać użytkownikowi (ukrywamy surowe kody ASCII)
            cols_to_show = ['ID_SZLAKU', 'REGION', 'NAZWA', 'KOLOR_WYSWIETLANY', 'TRUDNOSC_WYSWIETLANA', 'DLUGOSC', 'CZAS_PRZEJSCIA']
            st.dataframe(df[cols_to_show], width="stretch")
        else:
            st.info("Brak szlaków w bazie.")

        st.divider()
        st.subheader("Edycja Szlaku")
        
        if not df.empty:
            # W dropdownie też pokazujemy ładne nazwy
            # df iterrows zwraca surowe dane z bazy, więc musimy je przetłumaczyć w locie używając REV_...
            opts = {}
            for i, row in df.iterrows():
                k_pl = REV_KOLOR.get(row['KOLOR'], row['KOLOR'])
                label = f"{row['NAZWA']} ({k_pl})"
                opts[label] = row['ID_SZLAKU']

            sel_szlak = st.selectbox("Wybierz szlak do edycji", ["-- Wybierz --"] + list(opts.keys()))

            if sel_szlak != "-- Wybierz --":
                s_id = opts[sel_szlak]
                cur = df[df['ID_SZLAKU'] == s_id].iloc[0]

                with st.form("edit_szlak"):
                    # Ustawianie domyślnych wartości w formularzu
                    # Pobieramy z bazy np. 'ZOLTY', zamieniamy na 'Żółty' i szukamy indexu w liście
                    try:
                        current_kolor_pl = REV_KOLOR.get(cur['KOLOR'])
                        curr_kolor_idx = list(MAP_KOLOR.keys()).index(current_kolor_pl)
                        
                        current_trud_pl = REV_TRUDNOSC.get(cur['TRUDNOSC'])
                        curr_trud_idx = list(MAP_TRUDNOSC.keys()).index(current_trud_pl)
                    except:
                        curr_kolor_idx = 0
                        curr_trud_idx = 0

                    c1, c2 = st.columns(2)
                    new_nazwa = c1.text_input("Nazwa", value=cur['NAZWA'])
                    # Selectbox wyświetla polskie nazwy!
                    sel_kolor_pl = c2.selectbox("Kolor", list(MAP_KOLOR.keys()), index=curr_kolor_idx)
                    sel_trud_pl = c1.selectbox("Trudność", list(MAP_TRUDNOSC.keys()), index=curr_trud_idx)
                    
                    new_dlug = c2.number_input("Długość (km)", value=float(cur['DLUGOSC']))
                    new_czas = st.number_input("Czas (min)", value=int(cur['CZAS_PRZEJSCIA']))

                    if st.form_submit_button("Aktualizuj Szlak"):
                        # Tłumaczymy z powrotem na ASCII przed wysłaniem do bazy
                        db_kolor = MAP_KOLOR[sel_kolor_pl]     # Żółty -> ZOLTY
                        db_trudnosc = MAP_TRUDNOSC[sel_trud_pl] # Średni... -> SREDNIO...
                        
                        success, msg = crud.update_szlak(s_id, new_nazwa, db_kolor, db_trudnosc, new_dlug, new_czas)
                        if success:
                            st.success("Zapisano!")
                            st.rerun()
                        else:
                            st.error(msg)
                    
                    if st.form_submit_button("Usuń Szlak", type="primary"):
                        success, msg = crud.delete_szlak(s_id)
                        if success:
                            st.warning("Usunięto!")
                            st.rerun()
                        else:
                            st.error(msg)

    with tab2:
        st.subheader("Nowy Szlak")
        with st.form("add_szlak_form"):
            c1, c2 = st.columns(2)
            reg_label = c1.selectbox("Region", list(region_map.keys()))
            n_nazwa = c2.text_input("Nazwa szlaku")
            
            # Selectboxy z polskimi nazwami
            n_kolor_pl = c1.selectbox("Kolor", list(MAP_KOLOR.keys()))
            n_trud_pl = c2.selectbox("Trudność", list(MAP_TRUDNOSC.keys()))
            
            n_dlug = c1.number_input("Długość (km)", min_value=0.1)
            n_czas = c2.number_input("Czas (min)", min_value=1)

            if st.form_submit_button("Dodaj szlak"):
                # Konwersja PL -> ASCII
                db_kolor = MAP_KOLOR[n_kolor_pl]
                db_trudnosc = MAP_TRUDNOSC[n_trud_pl]

                success, msg = crud.add_szlak(region_map[reg_label], n_nazwa, db_kolor, db_trudnosc, n_dlug, n_czas)
                if success:
                    st.success("Szlak dodany!")
                    st.rerun()
                else:
                    st.error(msg)

def view_pokoje_manager():
    st.header("🏢 Zarządzanie Pokojami")

    # Tworzymy zakładki
    tab1, tab2 = st.tabs(["📋 Przegląd i Edycja", "➕ Dodaj nowy pokój"])

    # === ZAKŁADKA 1: Przeglądanie, Wyszukiwanie, Edycja, Usuwanie ===
    with tab1:
        # 1. POBIERANIE DANYCH
        df = crud.get_pokoje_full()

        # 2. WYSZUKIWANIE
        col_search, col_info = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("🔍 Szukaj (wpisz nazwę schroniska lub numer pokoju):", key="search_pokoj")
        
        if search_query:
            mask = (df['SCHRONISKO'].str.contains(search_query, case=False)) | \
                   (df['NR_POKOJU'].astype(str).str.contains(search_query))
            df_display = df[mask]
        else:
            df_display = df

        with col_info:
            st.info(f"Znaleziono: {len(df_display)}")

        # Wyświetlanie tabeli
        st.dataframe(df_display, width="stretch")
        st.markdown("---")

        # 3. MODYFIKACJA I USUWANIE
        st.subheader("🛠️ Edycja / Usuwanie")
        
        record_options = {
            f"{row['SCHRONISKO']} - Pokój nr {row['NR_POKOJU']} (ID: {row['ID_POKOJU']})": row['ID_POKOJU'] 
            for index, row in df_display.iterrows()
        }

        selected_label = st.selectbox("Wybierz pokój do edycji:", ["-- Wybierz z listy --"] + list(record_options.keys()))

        if selected_label != "-- Wybierz z listy --":
            selected_id = record_options[selected_label]
            current_data = df[df['ID_POKOJU'] == selected_id].iloc[0]

            with st.form("edit_pokoj_form"):
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("Schronisko", value=current_data['SCHRONISKO'], disabled=True)
                    new_places = st.number_input("Liczba miejsc", 
                                                 min_value=1, max_value=50, 
                                                 value=int(current_data['LICZBA_MIEJSC_CALKOWITA']))
                with c2:
                    st.text_input("Numer pokoju", value=current_data['NR_POKOJU'], disabled=True)
                    new_price = st.number_input("Cena za noc (PLN)", 
                                                min_value=0.0, 
                                                value=float(current_data['CENA_ZA_NOC']), step=10.0)

                col_save, col_del = st.columns([1, 4])
                with col_save:
                    if st.form_submit_button("💾 Zapisz zmiany"):
                        success, msg = crud.update_pokoj(selected_id, new_price, new_places)
                        if success:
                            st.success("Zaktualizowano!")
                            st.rerun()
                        else:
                            st.error(msg)
                
                with col_del:
                    if st.form_submit_button("🗑️ Usuń pokój", type="primary"):
                        success, msg = crud.delete_pokoj(selected_id)
                        if success:
                            st.warning("Pokój usunięty.")
                            st.rerun()
                        else:
                            st.error(msg)

    # === ZAKŁADKA 2: Dodawanie nowego pokoju ===
    with tab2:
        st.subheader("Definicja nowego pokoju")
        
        # Potrzebujemy listy schronisk do dropdowna
        # Wykorzystujemy istniejącą funkcję z crud
        schroniska_df = crud.get_schroniska_view()
        # Mapa: "Nazwa Schroniska" -> ID
        schroniska_map = {row['NAZWA']: row['ID_SCHRONISKA'] for i, row in schroniska_df.iterrows()}

        with st.form("add_pokoj_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                sel_schronisko = st.selectbox("Wybierz schronisko", list(schroniska_map.keys()))
                n_miejsca = st.number_input("Liczba miejsc", min_value=1, max_value=20, value=2)
            
            with col2:
                n_nr = st.number_input("Numer pokoju", min_value=1, value=101)
                n_cena = st.number_input("Cena za noc (PLN)", min_value=0.0, value=50.0, step=5.0)

            submitted = st.form_submit_button("Dodaj pokój")
            
            if submitted:
                # Pobieramy ID schroniska z mapy
                id_sch = schroniska_map[sel_schronisko]
                
                success, msg = crud.add_pokoj(id_sch, n_nr, n_miejsca, n_cena)
                if success:
                    st.success(f"Dodano pokój {n_nr} do schroniska {sel_schronisko}!")
                    # Rerun jest ważny, żeby nowy pokój pojawił się od razu w tabeli w zakładce 1
                    st.rerun()
                else:
                    st.error(msg)

def view_uzytkownicy_manager():
    st.header("👥 Zarządzanie Użytkownikami")

    # Pomocnicze mapowanie ról (Baza <-> UI)
    ROLA_MAP = {'Użytkownik': 'u', 'Pracownik': 'p'}
    ROLA_REV = {'u': 'Użytkownik', 'p': 'Pracownik'}

    tab1, tab2 = st.tabs(["📋 Lista i Edycja", "➕ Zarejestruj nowego"])

    # === ZAKŁADKA 1: PRZEGLĄD I EDYCJA ===
    with tab1:
        df = crud.get_users_full()

        # Wyszukiwanie
        search = st.text_input("Szukaj (login lub nazwisko):", key="search_user")
        if search:
            mask = df['LOGIN'].str.contains(search, case=False) | \
                   df['NAZWISKO'].str.contains(search, case=False)
            df = df[mask]
        
        # Wyświetlanie hasła w tabeli to zła praktyka produkcyjna, ale w projekcie edukacyjnym 
        # pomaga sprawdzić czy CRUD działa. Można ew. ukryć kolumnę.
        st.dataframe(df, width="stretch")

        st.subheader("Edycja Użytkownika")
        
        # Lista do wyboru: "Kowalski Jan (jank)"
        opts = {f"{row['NAZWISKO']} {row['IMIE']} ({row['LOGIN']})": row['ID_UZYTKOWNIKA'] for i, row in df.iterrows()}
        sel_user_label = st.selectbox("Wybierz użytkownika do edycji", ["-- Wybierz --"] + list(opts.keys()))

        if sel_user_label != "-- Wybierz --":
            uid = opts[sel_user_label]
            cur = df[df['ID_UZYTKOWNIKA'] == uid].iloc[0]

            with st.form("edit_user_form"):
                c1, c2 = st.columns(2)
                # Pobieramy obecną rolę i zamieniamy literkę 'u' na 'Użytkownik'
                curr_role_label = ROLA_REV.get(cur['ROLA'], 'Użytkownik')
                try:
                    role_index = list(ROLA_MAP.keys()).index(curr_role_label)
                except:
                    role_index = 0

                with c1:
                    u_login = st.text_input("Login", value=cur['LOGIN'])
                    u_imie = st.text_input("Imię", value=cur['IMIE'] if cur['IMIE'] else "")
                    u_rola = st.selectbox("Rola", list(ROLA_MAP.keys()), index=role_index)
                with c2:
                    u_haslo = st.text_input("Hasło", value=cur['HASLO'], type="password") # Ukrywanie znaków
                    u_nazwisko = st.text_input("Nazwisko", value=cur['NAZWISKO'])
                    u_email = st.text_input("Email", value=cur['EMAIL'])

                col_save, col_del = st.columns([1, 4])
                
                if col_save.form_submit_button("💾 Zaktualizuj"):
                    # Walidacja podstawowa
                    if not u_login or not u_nazwisko or not u_email:
                        st.error("Login, Nazwisko i Email są wymagane.")
                    else:
                        success, msg = crud.update_user(uid, u_login, u_haslo, ROLA_MAP[u_rola], u_imie, u_nazwisko, u_email)
                        if success:
                            st.success("Zaktualizowano dane!")
                            st.rerun()
                        else:
                            st.error(msg)
                
                if col_del.form_submit_button("🗑️ Usuń użytkownika", type="primary"):
                    success, msg = crud.delete_user(uid)
                    if success:
                        st.warning("Użytkownik usunięty.")
                        st.rerun()
                    else:
                        st.error(msg) # Np. jeśli ma aktywne rezerwacje (Klucz Obcy)

    # === ZAKŁADKA 2: DODAWANIE ===
    with tab2:
        st.subheader("Rejestracja nowego użytkownika")
        with st.form("add_user_form"):
            c1, c2 = st.columns(2)
            with c1:
                n_login = st.text_input("Login")
                n_imie = st.text_input("Imię")
                n_rola = st.selectbox("Rola", list(ROLA_MAP.keys()))
            with c2:
                n_haslo = st.text_input("Hasło", type="password")
                n_nazwisko = st.text_input("Nazwisko")
                n_email = st.text_input("Email")
            
            if st.form_submit_button("Zarejestruj"):
                if not n_login or not n_haslo or not n_nazwisko or not n_email:
                    st.error("Wypełnij wymagane pola (Login, Hasło, Nazwisko, Email).")
                else:
                    success, msg = crud.add_user(n_login, n_haslo, ROLA_MAP[n_rola], n_imie, n_nazwisko, n_email)
                    if success:
                        st.success(f"Dodano użytkownika {n_login}!")
                        st.rerun()
                    else:
                        st.error(msg)

# --- MAIN ---
def main():
    st.set_page_config(page_title="System Górski", layout="wide")
    st.title("🏔️ System Zarządzania Bazą Górską")

    menu = {
        "1. Użytkownicy": view_uzytkownicy_manager,
        "2. Regiony": view_regiony,
        "3. Szlaki": view_szlaki_manager,
        "4. Schroniska": view_schroniska,
        "5. Pokoje": view_pokoje_manager,
        "6. Rezerwacje": view_rezerwacje
    }
    
    sidebar_choice = st.sidebar.radio("Nawigacja", list(menu.keys()))
    
    menu[sidebar_choice]()

if __name__ == "__main__":
    main()