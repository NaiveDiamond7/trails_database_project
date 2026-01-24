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

def view_rezerwacje():
    st.header("Rezerwacje")
    
    # Wybór usera
    users = crud.get_users_dict()
    if not users:
        st.error("Brak użytkowników.")
        return
    u_label = st.selectbox("Użytkownik", list(users.keys()))
    u_id = users[u_label]

    # Wybór pokoju (logika filtrowania w UI, dane z CRUD)
    schroniska = crud.get_schroniska_view()
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

            if st.button("Oblicz koszt"):
                val = crud.calculate_cost(p_opts[sel_pok], d_start, d_end, osoby)
                st.info(f"Koszt: {val} PLN")

            if st.button("Rezerwuj", type="primary"):
                success, msg = crud.make_reservation(p_opts[sel_pok], u_id, osoby, d_start, d_end)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
    
    st.divider()
    st.subheader("Historia rezerwacji")
    # Tutaj też warto dodać width="stretch" dla spójności, choć nie było w oryginale
    st.dataframe(crud.get_user_reservations(u_id), width="stretch")

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

# --- MAIN ---
def main():
    st.set_page_config(page_title="System Górski", layout="wide")
    st.title("🏔️ System Zarządzania Bazą Górską")

    menu = {
        "1. Regiony": view_regiony,
        "2. Szlaki": view_szlaki_manager,
        "3. Schroniska": view_schroniska,
        "4. Pokoje": view_pokoje_manager,
        "5. Rezerwacje": view_rezerwacje
    }
    
    sidebar_choice = st.sidebar.radio("Nawigacja", list(menu.keys()))
    
    menu[sidebar_choice]()

if __name__ == "__main__":
    main()