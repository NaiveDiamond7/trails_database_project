import streamlit as st
import crud
import datetime

# --- WIDOKI ---

def view_regiony():
    st.header("Zarządzanie Regionami")
    
    # Czyste wywołanie funkcji z crud.py
    df = crud.get_regiony()
    # ZMIANA: width="stretch" zamiast use_container_width=True
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
    st.header("Schroniska")
    # ZMIANA: width="stretch"
    st.dataframe(crud.get_schroniska_view(), width="stretch")
    
    # Pobieranie regionów do formularza
    reg_df = crud.get_regiony()
    reg_opts = {row['NAZWA']: row['ID_REGIONU'] for i, row in reg_df.iterrows()}

    with st.form("add_schronisko"):
        col1, col2 = st.columns(2)
        with col1:
            nazwa = st.text_input("Nazwa")
            region = st.selectbox("Region", list(reg_opts.keys()))
            wys = st.number_input("Wysokość", 1, 8850)
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

# W pliku app.py

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
    with st.expander("➕ Nowa rezerwacja", expanded=False):
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
                    p_opts = {f"Pokój {row['NR_POKOJU']} ({row['CENA_ZA_NOC']} PLN)": row['ID_POKOJU'] for i, row in pokoje.iterrows()}
                    sel_pok = st.selectbox("Pokój", list(p_opts.keys()))
                    
                    c1, c2 = st.columns(2)
                    d_start = c1.date_input("Od", datetime.date.today())
                    d_end = c2.date_input("Do", datetime.date.today() + datetime.timedelta(days=1))
                    osoby = st.slider("Osoby", 1, 10, 2)

                    col_btn1, col_btn2 = st.columns(2)
                    if col_btn1.button("Oblicz koszt"):
                        if d_end <= d_start:
                            st.error("Data końcowa musi być późniejsza.")
                        else:
                            val = crud.calculate_cost(p_opts[sel_pok], d_start, d_end, osoby)
                            st.info(f"Koszt: {val} PLN")

                    if col_btn2.button("Rezerwuj", type="primary"):
                        if d_end <= d_start:
                            st.error("Data końcowa musi być późniejsza.")
                        else:
                            success, msg = crud.make_reservation(p_opts[sel_pok], u_id, osoby, d_start, d_end)
                            if success:
                                st.success("Rezerwacja dokonana pomyślnie!")
                                st.rerun()
                            else:
                                st.error(msg)

    # 3. ZARZĄDZANIE REZERWACJAMI UŻYTKOWNIKA (USUWANIE)
    st.subheader(f"Aktywne rezerwacje użytkownika: {u_label.split(' (')[0]}")
    
    # Pobieramy rezerwacje tego konkretnego użytkownika
    user_res_df = crud.get_user_reservations(u_id)
    
    if user_res_df.empty:
        st.info("Ten użytkownik nie ma żadnych rezerwacji.")
    else:
        # Tworzymy listę do selectboxa: "ID: 15 | Schronisko Muminki (Pokój 101) | 2023-10-10 do 2023-10-12"
        res_opts = {}
        for i, row in user_res_df.iterrows():
            label = f"ID: {row['ID_REZERWACJI']} | {row['SCHRONISKO']} (P. {row['NR_POKOJU']}) | {row['DATA_ROZPOCZECIA']} - {row['DATA_ZAKONCZENIA']}"
            res_opts[label] = row['ID_REZERWACJI']
        
        col_del1, col_del2 = st.columns([3, 1])
        sel_res_to_del = col_del1.selectbox("Wybierz rezerwację do anulowania", list(res_opts.keys()))
        
        # Przycisk usuwania
        if col_del2.button("🗑️ Anuluj rezerwację"):
            res_id_del = res_opts[sel_res_to_del]
            success, msg = crud.delete_reservation(res_id_del)
            if success:
                st.success("Rezerwacja została anulowana, a miejsca zwolnione.")
                st.rerun()
            else:
                st.error(msg)
    
    # --- TABELA HISTORII (Dla wszystkich) ---
    st.divider()
    st.subheader("Globalna historia rezerwacji")
    
    # ZMIANA: Używamy get_all_reservations() zamiast get_user_reservations(u_id)
    df_rez = crud.get_all_reservations()
    
    # Opcjonalnie: Filtrowanie tabeli
    show_only_selected = st.checkbox("Pokaż tylko dla wybranego użytkownika")
    if show_only_selected:
         # Filtrujemy DataFrame w Pythonie (Login to pierwsza część klucza w słowniku users, ale tutaj mamy go w kolumnie)
         # Prościej: pobraliśmy wszystko, teraz filtrujemy po ID (ale ID usera nie ma w SELECT wprost, jest w JOIN)
         # Wróćmy: najłatwiej filtrować po Loginie lub Nazwisku które są w df_rez
         selected_login = u_label.split(' (')[0] # To jest uproszczenie, lepiej filtrować w SQL jeśli danych dużo
         # Ale skoro mamy CRUD w SQL:
         st.dataframe(crud.get_user_reservations(u_id), width="stretch")
    else:
        st.dataframe(df_rez, width="stretch")

def view_szlaki_manager():
    st.header("🥾 Zarządzanie Szlakami")

    # Dane pomocnicze (Słowniki)
    KOLORY = ['Czerwony', 'Niebieski', 'Zielony', 'Żółty', 'Czarny']
    TRUDNOSCI = ['Spacerowy', 'Bardzo łatwy', 'Łatwy', 'Średniozaawansowany', 'Zaawansowany', 'Ekspercki']
    
    # Pobieramy regiony z bazy do dropdowna
    regions_df = crud.get_regiony()
    region_map = {row['NAZWA']: row['ID_REGIONU'] for i, row in regions_df.iterrows()}

    tab1, tab2 = st.tabs(["📋 Przegląd i Edycja", "➕ Dodaj nowy szlak"])

    with tab1:
        # Wyszukiwanie
        df = crud.get_szlaki()
        search = st.text_input("Szukaj szlaku (nazwa):", key="search_szlak")
        if search:
            df = df[df['NAZWA'].str.contains(search, case=False)]
        
        # ZMIANA: width="stretch"
        st.dataframe(df, width="stretch")

        # Edycja
        st.subheader("Edycja Szlaku")
        opts = {f"{row['NAZWA']} ({row['KOLOR']})": row['ID_SZLAKU'] for i, row in df.iterrows()}
        sel_szlak = st.selectbox("Wybierz szlak do edycji", ["-- Wybierz --"] + list(opts.keys()))

        if sel_szlak != "-- Wybierz --":
            s_id = opts[sel_szlak]
            cur = df[df['ID_SZLAKU'] == s_id].iloc[0]

            with st.form("edit_szlak"):
                try:
                    curr_kolor_idx = KOLORY.index(cur['KOLOR'])
                    curr_trud_idx = TRUDNOSCI.index(cur['TRUDNOSC'])
                except:
                    curr_kolor_idx = 0
                    curr_trud_idx = 0

                c1, c2 = st.columns(2)
                new_nazwa = c1.text_input("Nazwa", value=cur['NAZWA'])
                new_kolor = c2.selectbox("Kolor", KOLORY, index=curr_kolor_idx)
                new_trud = c1.selectbox("Trudność", TRUDNOSCI, index=curr_trud_idx)
                
                new_dlug = c2.number_input("Długość (km)", value=float(cur['DLUGOSC']))
                new_czas = st.number_input("Czas (min)", value=int(cur['CZAS_PRZEJSCIA']))

                if st.form_submit_button("Aktualizuj Szlak"):
                    success, msg = crud.update_szlak(s_id, new_nazwa, new_kolor, new_trud, new_dlug, new_czas)
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
            n_kolor = c1.selectbox("Kolor", KOLORY)
            n_trud = c2.selectbox("Trudność", TRUDNOSCI)
            n_dlug = c1.number_input("Długość (km)", min_value=0.1)
            n_czas = c2.number_input("Czas (min)", min_value=1)

            if st.form_submit_button("Dodaj szlak"):
                success, msg = crud.add_szlak(region_map[reg_label], n_nazwa, n_kolor, n_trud, n_dlug, n_czas)
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