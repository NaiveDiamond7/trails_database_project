def view_kolejnosci_manager():
    st.header("🔢 Kolejności punktów na szlakach")

    if 'kol_add_success' not in st.session_state:
        st.session_state['kol_add_success'] = False
    if st.session_state.get('kol_add_success'):
        st.success("Dodano kolejność.")
        st.session_state['kol_add_success'] = False

    df = crud.get_kolejnosci()
    szlaki_df = crud.get_szlaki()
    szlaki_rev = {row['ID_SZLAKU']: row['NAZWA'] for i, row in szlaki_df.iterrows()}
    szlaki_map = {f"{row['NAZWA']} (ID: {row['ID_SZLAKU']})": row['ID_SZLAKU'] for i, row in szlaki_df.iterrows()}
    punkty_df = crud.get_punkty()
    punkty_rev = {row['ID_PUNKTU']: row['NAZWA'] for i, row in punkty_df.iterrows()}
    punkty_map = {f"{row['NAZWA']} (ID: {row['ID_PUNKTU']})": row['ID_PUNKTU'] for i, row in punkty_df.iterrows()}

    tab1, tab2 = st.tabs(["📋 Przegląd i Usuwanie", "➕ Dodaj kolejność"])

    if st.session_state.get('kol_add_success'):
        with tab1:
            st.success("Dodano kolejność.")
        st.session_state['kol_add_success'] = False

    with tab1:
        if not df.empty:
            df_display = df.copy()
            df_display['SZLAK'] = df_display['ID_SZLAKU_KOL'].map(szlaki_rev).fillna(df_display['ID_SZLAKU_KOL'])
            df_display['PUNKT'] = df_display['ID_PUNKTU'].map(punkty_rev).fillna(df_display['ID_PUNKTU'])
            cols = ['ID_SZLAKU_KOL', 'SZLAK', 'PUNKT', 'KOLEJNOSC_NA_SZLAKU']
            st.dataframe(df_display[cols], width="stretch")
        else:
            st.dataframe(df, width="stretch")

        opts = {}
        for i, row in df.iterrows():
            sname = szlaki_rev.get(row['ID_SZLAKU_KOL'], row['ID_SZLAKU_KOL'])
            pname = punkty_rev.get(row['ID_PUNKTU'], row['ID_PUNKTU'])
            label = f"{sname} - {pname} (kolejność {row['KOLEJNOSC_NA_SZLAKU']})"
            opts[label] = (row['ID_SZLAKU_KOL'], row['ID_PUNKTU'], row['KOLEJNOSC_NA_SZLAKU'])
        sel = st.selectbox("Wybierz kolejność", ["-- Wybierz --"] + list(opts.keys()))
        if sel != "-- Wybierz --":
            if st.button("Usuń kolejność"):
                id_szlaku, id_punktu, kolejnosc = opts[sel]
                success, msg = crud.delete_kolejnosc(id_szlaku, id_punktu, kolejnosc)
                if success:
                    st.success("Usunięto kolejność.")
                    safe_rerun()
                else:
                    st.error(msg)

    with tab2:
        with st.form("add_kol_form"):
            sel_szlak = st.selectbox("Szlak", list(szlaki_map.keys()), key="kol_szlak")
            sel_punkt = st.selectbox("Punkt", list(punkty_map.keys()), key="kol_punkt")
            kolejnosc = st.number_input("Kolejność na szlaku", min_value=1)
            if st.form_submit_button("Dodaj"):
                id_szlaku = szlaki_map[sel_szlak]
                id_punktu = punkty_map[sel_punkt]
                success, msg = crud.add_kolejnosc(id_szlaku, id_punktu, kolejnosc)
                if success:
                    st.session_state['kol_add_success'] = True
                    safe_rerun()
                else:
                    st.error(msg)

def view_wyposazenie_manager():
    st.header("🛠️ Zarządzanie Wyposażeniem")

    if 'wyposazenie_tab' not in st.session_state:
        st.session_state['wyposazenie_tab'] = 0
    if 'wyposazenie_add_success' not in st.session_state:
        st.session_state['wyposazenie_add_success'] = False

    tab1, tab2 = st.tabs(["📋 Lista i Edycja", "➕ Dodaj nowe wyposażenie"])

    if st.session_state.get('wyposazenie_add_success'):
        with tab1:
            st.success("Dodano wyposażenie.")
        st.session_state['wyposazenie_add_success'] = False

    with tab1:
        df = crud.get_wyposazenia()
        st.dataframe(df, width="stretch")

        st.subheader("Edycja wyposażenia")
        opts = {row['NAZWA']: row['ID_WYPOSAZENIA'] for i, row in df.iterrows()}
        sel = st.selectbox("Wybierz wyposażenie do edycji", ["-- Wybierz --"] + list(opts.keys()))
        if sel != "-- Wybierz --":
            wid = opts[sel]
            cur = df[df['ID_WYPOSAZENIA'] == wid].iloc[0]
            with st.form("edit_wyposazenie_form"):
                new_name = st.text_input("Nazwa", value=cur['NAZWA'])
                c1, c2 = st.columns([1,1])
                if c1.form_submit_button("💾 Zapisz"):
                    success, msg = crud.update_wyposazenie(wid, new_name)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                if c2.form_submit_button("🗑️ Usuń", type="primary"):
                    success, msg = crud.delete_wyposazenie(wid)
                    if success:
                        st.warning("Usunięto wyposażenie.")
                        st.rerun()
                    else:
                        st.error(msg)

    with tab2:
        st.subheader("Dodaj nowe wyposażenie")
        with st.form("add_wyposazenie_form"):
            nazwa = st.text_input("Nazwa wyposażenia")
            if st.form_submit_button("Dodaj"):
                success, msg = crud.add_wyposazenie(nazwa)
                if success:
                    st.session_state['wyposazenie_tab'] = 0
                    st.session_state['wyposazenie_add_success'] = True
                    st.rerun()
                else:
                    st.error(msg)

    st.divider()
    st.header("🔗 Przypisz wyposażenie do schroniska/pokoju")
    tab3, tab4 = st.tabs(["Schroniska", "Pokoje"])

    with tab3:
        schroniska = crud.get_schroniska_view()
        sch_map = {row['NAZWA']: row['ID_SCHRONISKA'] for i, row in schroniska.iterrows()}
        sel_sch = st.selectbox("Schronisko", list(sch_map.keys()), key="wypsch")
        if sel_sch:
            sch_id = sch_map[sel_sch]
            sch_wyposazenie = crud.get_schroniska_wyposazenie(sch_id)
            all_wyp = crud.get_wyposazenia()
            st.write("Aktualne wyposażenie:")
            st.dataframe(sch_wyposazenie, width="stretch")
            add_opts = {row['NAZWA']: row['ID_WYPOSAZENIA'] for i, row in all_wyp.iterrows() if row['ID_WYPOSAZENIA'] not in sch_wyposazenie['ID_WYPOSAZENIA'].values}
            del_opts = {row['NAZWA']: row['ID_WYPOSAZENIA'] for i, row in sch_wyposazenie.iterrows()}
            c1, c2 = st.columns(2)
            with c1:
                sel_add = st.selectbox("Dodaj wyposażenie", ["-- Wybierz --"] + list(add_opts.keys()), key="addschwyp")
                if sel_add != "-- Wybierz --":
                    if st.button("Dodaj do schroniska"):
                        if not add_opts[sel_add]:
                            st.error("Nie wybrano wyposażenia do dodania.")
                        else:
                            success, msg = crud.add_schronisko_wyposazenie(sch_id, add_opts[sel_add])
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg if 'Błąd:' in msg else f"Błąd: {msg}")
            with c2:
                sel_del = st.selectbox("Usuń wyposażenie", ["-- Wybierz --"] + list(del_opts.keys()), key="delschwyp")
                if sel_del != "-- Wybierz --":
                    if st.button("Usuń ze schroniska"):
                        if not del_opts[sel_del]:
                            st.error("Nie wybrano wyposażenia do usunięcia.")
                        else:
                            success, msg = crud.delete_schronisko_wyposazenie(sch_id, del_opts[sel_del])
                            if success:
                                st.warning("Usunięto wyposażenie ze schroniska.")
                                st.rerun()
                            else:
                                st.error(msg if 'Błąd:' in msg else f"Błąd: {msg}")

    with tab4:
        pokoje = crud.get_pokoje_full()
        pokoje_map = {f"{row['SCHRONISKO']} - Pokój {row['NR_POKOJU']} (ID: {row['ID_POKOJU']})": row['ID_POKOJU'] for i, row in pokoje.iterrows()}
        sel_pok = st.selectbox("Pokój", list(pokoje_map.keys()), key="wyppok")
        if sel_pok:
            pok_id = pokoje_map[sel_pok]
            pok_wyp = crud.get_pokoje_wyposazenie(pok_id)
            all_wyp = crud.get_wyposazenia()
            st.write("Aktualne wyposażenie pokoju:")
            st.dataframe(pok_wyp, width="stretch")
            add_opts = {row['NAZWA']: row['ID_WYPOSAZENIA'] for i, row in all_wyp.iterrows() if row['ID_WYPOSAZENIA'] not in pok_wyp['ID_WYPOSAZENIA'].values}
            del_opts = {row['NAZWA']: row['ID_WYPOSAZENIA'] for i, row in pok_wyp.iterrows()}
            c1, c2 = st.columns(2)
            with c1:
                sel_add = st.selectbox("Dodaj wyposażenie", ["-- Wybierz --"] + list(add_opts.keys()), key="addpokwyp")
                if sel_add != "-- Wybierz --":
                    if st.button("Dodaj do pokoju"):
                        if not add_opts[sel_add]:
                            st.error("Nie wybrano wyposażenia do dodania.")
                        else:
                            success, msg = crud.add_pokoj_wyposazenie(pok_id, add_opts[sel_add])
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg if 'Błąd:' in msg else f"Błąd: {msg}")
            with c2:
                sel_del = st.selectbox("Usuń wyposażenie", ["-- Wybierz --"] + list(del_opts.keys()), key="delpokwyp")
                if sel_del != "-- Wybierz --":
                    if st.button("Usuń z pokoju"):
                        if not del_opts[sel_del]:
                            st.error("Nie wybrano wyposażenia do usunięcia.")
                        else:
                            success, msg = crud.delete_pokoj_wyposazenie(pok_id, del_opts[sel_del])
                            if success:
                                st.warning("Usunięto wyposażenie z pokoju.")
                                st.rerun()
                            else:
                                st.error(msg if 'Błąd:' in msg else f"Błąd: {msg}")
import streamlit as st
import crud
import datetime

def safe_rerun():
    try:
        return st.experimental_rerun()
    except Exception:
        try:
            return st.rerun()
        except Exception:
            return st.stop()

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

    reg_df = crud.get_regiony()
    reg_opts = {row['NAZWA']: row['ID_REGIONU'] for i, row in reg_df.iterrows()}
    reg_rev = {row['ID_REGIONU']: row['NAZWA'] for i, row in reg_df.iterrows()}

    if 'schroniska_tab' not in st.session_state:
        st.session_state['schroniska_tab'] = 0
    if 'schronisko_add_success' not in st.session_state:
        st.session_state['schronisko_add_success'] = False

    tab_labels = ["📋 Lista i Edycja", "➕ Dodaj nowe"]
    tab_idx = st.session_state['schroniska_tab']
    tabs = st.tabs(tab_labels)
    tab1, tab2 = tabs[0], tabs[1]

    if st.session_state['schronisko_add_success']:
        with tab1:
            st.success("Schronisko utworzono!")
        st.session_state['schronisko_add_success'] = False

    with tab1:
        df = crud.get_schroniska_view()

        search = st.text_input("Szukaj schroniska:", key="search_sch")
        if search:
            df = df[df['NAZWA'].str.contains(search, case=False)]

        st.dataframe(df, width="stretch")

        st.subheader("Edycja Schroniska")
        opts = {f"{row['NAZWA']}": row['ID_SCHRONISKA'] for i, row in df.iterrows()}
        sel_sch = st.selectbox("Wybierz schronisko do edycji", ["-- Wybierz --"] + list(opts.keys()))

        if sel_sch != "-- Wybierz --":
            s_id = opts[sel_sch]
            cur = df[df['ID_SCHRONISKA'] == s_id].iloc[0]

            with st.form("edit_schronisko_form"):
                col1, col2 = st.columns(2)
                
                try:
                    t_otw_obj = datetime.datetime.strptime(cur['GODZINA_OTWARCIA'], "%H:%M").time()
                    t_zam_obj = datetime.datetime.strptime(cur['GODZINA_ZAMKNIECIA'], "%H:%M").time()
                except:
                    t_otw_obj = datetime.time(8,0)
                    t_zam_obj = datetime.time(20,0)

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

    with tab2:
        st.subheader(":green[Dodaj nowe schronisko]")
        st.markdown("""
        <style>
        .schronisko-form .stTextInput>div>input, .schronisko-form .stNumberInput>div>input, .schronisko-form .stSelectbox>div>div {background: #f6f6f6; border-radius: 6px;}
        .schronisko-form .stTimeInput>div>input {background: #f6f6f6; border-radius: 6px;}
        </style>
        """, unsafe_allow_html=True)
        with st.form("add_schronisko", clear_on_submit=True):
            st.markdown('<div class="schronisko-form">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                nazwa = st.text_input("Nazwa schroniska", placeholder="Podaj nazwę schroniska")
                region = st.selectbox("Region", list(reg_opts.keys()), key="add_reg_sel")
                wys = st.number_input("Wysokość [m n.p.m.]", min_value=1, max_value=8850, value=1000, step=1)
            with col2:
                otw = st.time_input("Godzina otwarcia", datetime.time(8,0))
                zam = st.time_input("Godzina zamknięcia", datetime.time(20,0))
            st.markdown('</div>', unsafe_allow_html=True)
            submitted = st.form_submit_button(":heavy_plus_sign: Dodaj schronisko")
            if submitted:
                if not nazwa.strip():
                    st.error("Nazwa schroniska nie może być pusta.")
                elif len(nazwa.strip()) > 100:
                    st.error("Nazwa schroniska nie może przekraczać 100 znaków.")
                else:
                    success, msg = crud.add_schronisko_transaction(
                        reg_opts[region], nazwa.strip(), wys, 
                        otw.strftime("%H:%M"), zam.strftime("%H:%M"),
                        0, 0
                    )
                    if success:
                        st.session_state['schroniska_tab'] = 0
                        st.session_state['schronisko_add_success'] = True
                        st.rerun()
                    else:
                        st.error(msg if 'Błąd:' in msg else f"Błąd: {msg}")
                if success:
                    st.success("Dodano!")
                    st.rerun()
                else:
                    st.error(msg)

def view_rezerwacje():
    st.header("Rezerwacje")

    users = crud.get_users_dict()
    if not users:
        st.error("Brak użytkowników.")
        return
    u_label = st.selectbox("Wybierz użytkownika", list(users.keys()))
    u_id = users[u_label]

    tab_add, tab_manage = st.tabs(["➕ Nowa rezerwacja", "🛠️ Zarządzaj rezerwacjami"])

    with tab_add:
        st.subheader("Nowa rezerwacja")
        pokoje = crud.get_pokoje_full()
        if pokoje.empty:
            st.info("Brak pokoi do rezerwacji.")
        else:
            schroniska = pokoje['SCHRONISKO'].unique().tolist()
            schronisko_sel = st.selectbox("Schronisko", schroniska)
            pokoje_w_schronisku = pokoje[pokoje['SCHRONISKO'] == schronisko_sel]
            if pokoje_w_schronisku.empty:
                st.info("Brak pokoi w wybranym schronisku.")
            else:
                capacity_map = {row['ID_POKOJU']: int(row['LICZBA_MIEJSC_CALKOWITA']) for i, row in pokoje_w_schronisku.iterrows()}
                p_opts = {
                    f"Pokój {row['NR_POKOJU']} (Cena: {row.get('CENA_ZA_NOC', '')} PLN, Max: {row['LICZBA_MIEJSC_CALKOWITA']})": row['ID_POKOJU']
                    for i, row in pokoje_w_schronisku.iterrows()
                }
                with st.form("add_reservation_form", clear_on_submit=True):
                    sel_pok_label = st.selectbox("Pokój", list(p_opts.keys()))
                    sel_pok_id = p_opts[sel_pok_label]
                    max_osob = capacity_map[sel_pok_id]
                    c1, c2 = st.columns(2)
                    d_start = c1.date_input("Od", datetime.date.today())
                    d_end = c2.date_input("Do", datetime.date.today() + datetime.timedelta(days=1))
                    osoby_options = list(range(1, max_osob + 1))
                    osoby = st.selectbox("Liczba osób", osoby_options)
                    st.markdown("**Podgląd zajętości pokoju:**")
                    import pandas as pd
                    import calendar
                    res_df = crud.get_room_reservations(sel_pok_id)
                    busy_count = {}
                    for i, row in res_df.iterrows():
                        rng = pd.date_range(row['DATA_ROZPOCZECIA'], row['DATA_ZAKONCZENIA'] - pd.Timedelta(days=1))
                        for d in rng.date:
                            busy_count[d] = busy_count.get(d, 0) + int(row.get('LICZBA_OSOB', 1))
                    today = datetime.date.today()
                    cal = calendar.Calendar()
                    days = list(cal.itermonthdates(today.year, today.month))
                    cal_row = []
                    for d in days:
                        if d.month != today.month:
                            cal_row.append("⬜")
                        else:
                            occ = busy_count.get(d, 0)
                            if occ >= max_osob:
                                cal_row.append("🔴")
                            elif occ > 0:
                                cal_row.append("🟡")
                            else:
                                cal_row.append("🟢")
                    st.markdown("Dni zajęte: 🔴  |  częściowo zajęte: 🟡  |  wolne: 🟢  |  poza miesiącem: ⬜")
                    for i in range(0, len(cal_row), 7):
                        st.markdown(" ".join(cal_row[i:i+7]))

                    if st.form_submit_button("Zarezerwuj"):
                        if d_end <= d_start:
                            st.error("Data końcowa musi być późniejsza.")
                        else:
                            wybrane = list(pd.date_range(d_start, d_end - datetime.timedelta(days=1)).date)
                            can_reserve = True
                            for d in wybrane:
                                occ = busy_count.get(d, 0)
                                if occ + osoby > max_osob:
                                    can_reserve = False
                                    break
                            if not can_reserve:
                                st.error("Wybrany termin przekracza pojemność pokoju w niektóre dni!")
                            else:
                                success, msg = crud.make_reservation(sel_pok_id, u_id, osoby, d_start, d_end)
                                if success:
                                    st.success("Rezerwacja dokonana pomyślnie!")
                                    st.rerun()
                                else:
                                    st.error(msg)

    with tab_manage:
        st.subheader("Zarządzanie rezerwacjami")
        df_rez = crud.get_all_reservations()
        if df_rez.empty:
            st.info("Brak rezerwacji w systemie.")
        else:
            st.dataframe(df_rez, width="stretch")

            opts = {}
            for i, row in df_rez.iterrows():
                try:
                    start = row['DATA_ROZPOCZECIA'].date()
                    end = row['DATA_ZAKONCZENIA'].date()
                except:
                    start = row.get('DATA_ROZPOCZECIA')
                    end = row.get('DATA_ZAKONCZENIA')
                label = f"{row['ID_REZERWACJI']} — {row['LOGIN']} — {row['SCHRONISKO']} Pok. {row['NR_POKOJU']} ({start} → {end})"
                opts[label] = row['ID_REZERWACJI']

            sel = st.selectbox("Wybierz rezerwację do zarządzania", ["-- Wybierz --"] + list(opts.keys()))
            if sel != "-- Wybierz --":
                rez_id = opts[sel]
                cur = df_rez[df_rez['ID_REZERWACJI'] == rez_id].iloc[0]
                st.markdown(f"**Użytkownik:** {cur['LOGIN']} {cur.get('IMIE','')} {cur.get('NAZWISKO','')}")
                st.markdown(f"**Schronisko / Pokój:** {cur['SCHRONISKO']} / {cur['NR_POKOJU']}")
                st.markdown(f"**Liczba osób:** {cur.get('LICZBA_OSOB','')}")
                st.markdown(f"**Okres:** {cur.get('DATA_ROZPOCZECIA')} → {cur.get('DATA_ZAKONCZENIA')}")
                st.markdown(f"**Status:** {cur.get('STATUS_REZ','')}")
                st.markdown(f"**Kwota:** {cur.get('KWOTA','')}")

                c1, c2 = st.columns([1,3])
                if c1.button("Anuluj rezerwację"):
                    success, msg = crud.delete_reservation(rez_id)
                    if success:
                        st.success("Rezerwacja anulowana.")
                        st.rerun()
                    else:
                        st.error(msg)

def view_szlaki_manager():
    st.header("🥾 Zarządzanie Szlakami")

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

    REV_KOLOR = {v: k for k, v in MAP_KOLOR.items()}
    REV_TRUDNOSC = {v: k for k, v in MAP_TRUDNOSC.items()}

    regions_df = crud.get_regiony()
    region_map = {row['NAZWA']: row['ID_REGIONU'] for i, row in regions_df.iterrows()}

    if 'szlaki_tab' not in st.session_state:
        st.session_state['szlaki_tab'] = 0
    if 'szlak_add_success' not in st.session_state:
        st.session_state['szlak_add_success'] = False

    tab1, tab2 = st.tabs(["📋 Przegląd i Edycja", "➕ Dodaj nowy szlak"])

    if st.session_state.get('szlak_add_success'):
        with tab1:
            st.success("Szlak dodany.")
        st.session_state['szlak_add_success'] = False

    with tab1:
        df = crud.get_szlaki()
        
        if not df.empty:
            df['KOLOR_WYSWIETLANY'] = df['KOLOR'].map(REV_KOLOR).fillna(df['KOLOR'])
            df['TRUDNOSC_WYSWIETLANA'] = df['TRUDNOSC'].map(REV_TRUDNOSC).fillna(df['TRUDNOSC'])
            
            search = st.text_input("Szukaj szlaku (nazwa):", key="search_szlak")
            if search:
                df = df[df['NAZWA'].str.contains(search, case=False)]
            
            cols_to_show = ['ID_SZLAKU', 'REGION', 'NAZWA', 'KOLOR_WYSWIETLANY', 'TRUDNOSC_WYSWIETLANA', 'DLUGOSC', 'CZAS_PRZEJSCIA']
            st.dataframe(df[cols_to_show], width="stretch")
        else:
            st.info("Brak szlaków w bazie.")

        st.divider()
        st.subheader("Edycja Szlaku")
        
        if not df.empty:
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
                    sel_kolor_pl = c2.selectbox("Kolor", list(MAP_KOLOR.keys()), index=curr_kolor_idx)
                    sel_trud_pl = c1.selectbox("Trudność", list(MAP_TRUDNOSC.keys()), index=curr_trud_idx)
                    new_dlug = c2.number_input("Długość (km)", value=float(cur['DLUGOSC']))
                    new_czas = st.number_input("Czas (min)", value=int(cur['CZAS_PRZEJSCIA']))

                    if st.form_submit_button("Aktualizuj Szlak"):
                        db_kolor = MAP_KOLOR[sel_kolor_pl]
                        db_trudnosc = MAP_TRUDNOSC[sel_trud_pl]
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
            
            n_kolor_pl = c1.selectbox("Kolor", list(MAP_KOLOR.keys()))
            n_trud_pl = c2.selectbox("Trudność", list(MAP_TRUDNOSC.keys()))
            
            n_dlug = c1.number_input("Długość (km)", min_value=0.1)
            n_czas = c2.number_input("Czas (min)", min_value=1)

            if st.form_submit_button("Dodaj szlak"):
                db_kolor = MAP_KOLOR[n_kolor_pl]
                db_trudnosc = MAP_TRUDNOSC[n_trud_pl]
                success, msg = crud.add_szlak(region_map[reg_label], n_nazwa, db_kolor, db_trudnosc, n_dlug, n_czas)
                if success:
                    st.session_state['szlaki_tab'] = 0
                    st.session_state['szlak_add_success'] = True
                    safe_rerun()
                else:
                    st.error(msg)

def view_pokoje_manager():
    st.header("🏢 Zarządzanie Pokojami")
    if 'pokoj_add_success' not in st.session_state:
        st.session_state['pokoj_add_success'] = False
    if st.session_state['pokoj_add_success']:
        st.success("Pokój dodany!")
        st.session_state['pokoj_add_success'] = False
    tab_labels = ["📋 Przegląd i Edycja", "➕ Dodaj nowy pokój"]
    tab1, tab2 = st.tabs(tab_labels)
    with tab1:
        df = crud.get_pokoje_full()
        schroniska_list = sorted(df['SCHRONISKO'].unique().tolist()) if not df.empty else []
        schroniska_sel = st.selectbox("Wybierz schronisko", ["Wszystkie"] + schroniska_list, key="filter_schronisko")
        col_search, col_info = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("🔍 Szukaj (wpisz nazwę schroniska lub numer pokoju):", key="search_pokoj")
        if schroniska_sel != "Wszystkie":
            df = df[df['SCHRONISKO'] == schroniska_sel]
        if search_query:
            mask = (df['SCHRONISKO'].str.contains(search_query, case=False)) | \
                   (df['NR_POKOJU'].astype(str).str.contains(search_query))
            df_display = df[mask]
        else:
            df_display = df
        with col_info:
            st.info(f"Znaleziono: {len(df_display)}")
        st.dataframe(df_display, width="stretch")
        st.markdown("---")
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
                    new_places = st.number_input("Liczba miejsc", min_value=1, max_value=50, value=int(current_data['LICZBA_MIEJSC_CALKOWITA']))
                with c2:
                    new_price = st.number_input("Cena za noc (PLN)", min_value=0.0, value=float(current_data['CENA_ZA_NOC']), step=5.0)
                col_save, col_del = st.columns([1, 4])
                if col_save.form_submit_button("💾 Zapisz zmiany"):
                    success, msg = crud.update_pokoj(selected_id, new_price, new_places)
                    if success:
                        st.success("Zaktualizowano dane pokoju!")
                        st.rerun()
                    else:
                        st.error(msg)
                if col_del.form_submit_button("🗑️ Usuń pokój", type="primary"):
                    success, msg = crud.delete_pokoj(selected_id)
                    if success:
                        st.warning("Pokój usunięty.")
                        st.rerun()
                    else:
                        st.error(msg)
    with tab2:
        st.subheader("Definicja nowego pokoju")
        schroniska_df = crud.get_schroniska_view()
        schroniska_map = {row['NAZWA']: row['ID_SCHRONISKA'] for i, row in schroniska_df.iterrows()}
        with st.form("add_pokoj_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                sel_schronisko = st.selectbox("Wybierz schronisko", list(schroniska_map.keys()), key="add_pokoj_schronisko")
                n_miejsca = st.number_input("Liczba miejsc", min_value=1, max_value=20, value=2, key="add_pokoj_miejsca")
            with col2:
                n_nr = st.number_input("Numer pokoju", min_value=1, value=101, key="add_pokoj_nr")
                n_cena = st.number_input("Cena za noc (PLN)", min_value=0.0, value=50.0, step=5.0, key="add_pokoj_cena")
            submitted = st.form_submit_button("Dodaj pokój")
            if submitted:
                id_sch = schroniska_map[sel_schronisko]
                success, msg = crud.add_pokoj(id_sch, n_nr, n_miejsca, n_cena)
                if success:
                    st.session_state['pokoje_tab'] = 0
                    st.session_state['pokoj_add_success'] = True
                    st.rerun()
                else:
                    st.error(msg if 'Błąd:' in msg else f"Błąd: {msg}")

def view_uzytkownicy_manager():
    st.header("👥 Zarządzanie Użytkownikami")

    ROLA_MAP = {'Użytkownik': 'u', 'Pracownik': 'p'}
    ROLA_REV = {'u': 'Użytkownik', 'p': 'Pracownik'}

    if 'uzytkownicy_tab' not in st.session_state:
        st.session_state['uzytkownicy_tab'] = 0
    if 'uzytkownik_add_success' not in st.session_state:
        st.session_state['uzytkownik_add_success'] = False

    tab1, tab2 = st.tabs(["📋 Lista i Edycja", "➕ Zarejestruj nowego"])

    if st.session_state.get('uzytkownik_add_success'):
        with tab1:
            st.success("Dodano użytkownika.")
        st.session_state['uzytkownik_add_success'] = False

    with tab1:
        df = crud.get_users_full()

        search = st.text_input("Szukaj (login lub nazwisko):", key="search_user")
        if search:
            mask = df['LOGIN'].str.contains(search, case=False) | \
                   df['NAZWISKO'].str.contains(search, case=False)
            df = df[mask]
        
        st.dataframe(df, width="stretch")

        st.subheader("Edycja Użytkownika")
        
        opts = {f"{row['NAZWISKO']} {row['IMIE']} ({row['LOGIN']})": row['ID_UZYTKOWNIKA'] for i, row in df.iterrows()}
        sel_user_label = st.selectbox("Wybierz użytkownika do edycji", ["-- Wybierz --"] + list(opts.keys()))

        if sel_user_label != "-- Wybierz --":
            uid = opts[sel_user_label]
            cur = df[df['ID_UZYTKOWNIKA'] == uid].iloc[0]

            with st.form("edit_user_form"):
                c1, c2 = st.columns(2)
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
                    u_haslo = st.text_input("Hasło", value=cur['HASLO'], type="password")
                    u_nazwisko = st.text_input("Nazwisko", value=cur['NAZWISKO'])
                    u_email = st.text_input("Email", value=cur['EMAIL'])

                col_save, col_del = st.columns([1, 4])
                
                if col_save.form_submit_button("💾 Zaktualizuj"):
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
                        st.error(msg)

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
                        st.session_state['uzytkownicy_tab'] = 0
                        st.session_state['uzytkownik_add_success'] = True
                        st.rerun()
                    else:
                        st.error(msg)

def main():

    st.set_page_config(page_title="System Górski", layout="wide")


    menu_schroniska = {
        "Użytkownicy": view_uzytkownicy_manager,
        "Regiony": view_regiony,
        "Schroniska": view_schroniska,
        "Pokoje": view_pokoje_manager,
        "Wyposażenie": view_wyposazenie_manager,
        "Rezerwacje": view_rezerwacje
    }
    menu_szlaki = {
        "Szlaki": view_szlaki_manager,
        "Punkty": view_punkty_manager,
        "Odległości między punktami": view_odleglosci_manager,
        "Kolejności na szlakach": view_kolejnosci_manager
    }
    schroniska_keys = list(menu_schroniska.keys())
    szlaki_keys = list(menu_szlaki.keys())
    all_menu = schroniska_keys + szlaki_keys
    choice = st.sidebar.radio("Menu", all_menu, key="main_nav")
    if choice in menu_schroniska:
        menu_schroniska[choice]()
    else:
        menu_szlaki[choice]()

def view_punkty_manager():
    st.header("🗺️ Zarządzanie Punktami")
    if 'punkty_add_success' not in st.session_state:
        st.session_state['punkty_add_success'] = False
    if st.session_state['punkty_add_success']:
        st.success("Dodano punkt.")
        st.session_state['punkty_add_success'] = False
    df = crud.get_punkty()
    regions = crud.get_regiony()
    region_rev = {row['ID_REGIONU']: row['NAZWA'] for i, row in regions.iterrows()}
    regiony_df = crud.get_regiony()
    regiony_map = {row['NAZWA']: row['ID_REGIONU'] for i, row in regiony_df.iterrows()}
    popularne_typy = [
        "Schronisko", "Przełęcz", "Szczyt", "Polana", "Rozdroże", "Węzeł szlaków", "Miejscowość", "Jezioro", "Rzeka", "Inny"
    ]

    tab1, tab2 = st.tabs(["📋 Przegląd i Usuwanie", "➕ Dodaj punkt"])

    if st.session_state.get('punkty_add_success'):
        with tab1:
            st.success("Dodano punkt.")
        st.session_state['punkty_add_success'] = False

    with tab1:
        if not df.empty:
            df_display = df.copy()
            df_display['REGION'] = df_display['ID_REGIONU'].map(region_rev).fillna(df_display['ID_REGIONU'])
            cols = ['ID_PUNKTU', 'NAZWA', 'REGION', 'TYP', 'WYSOKOSC', 'WSPOLRZEDNE_DLUGOSC', 'WSPOLRZEDNE_SZEROKOSC']
            available = [c for c in cols if c in df_display.columns]
            st.dataframe(df_display[available], width="stretch")
        else:
            st.dataframe(df, width="stretch")

        opts = {f"{row['NAZWA']} (ID: {row['ID_PUNKTU']})": row['ID_PUNKTU'] for i, row in df.iterrows()}
        sel = st.selectbox("Wybierz punkt", ["-- Wybierz --"] + list(opts.keys()))
        if sel != "-- Wybierz --":
            if st.button("Usuń punkt"):
                success, msg = crud.delete_punkt(opts[sel])
                if success:
                    st.success("Usunięto punkt.")
                    st.rerun()
                else:
                    st.error(msg)

    with tab2:
        with st.form("add_punkt_form"):
            nazwa = st.text_input("Nazwa punktu")
            region_nazwa = st.selectbox("Region", list(regiony_map.keys()))
            typ = st.selectbox("Typ punktu", popularne_typy + ["Inny (wpisz własny)"])
            if typ == "Inny (wpisz własny)":
                typ = st.text_input("Wpisz własny typ punktu")
            wysokosc = st.number_input("Wysokość", min_value=0)
            dlugosc = st.number_input("Długość geograficzna", format="%.6f")
            szerokosc = st.number_input("Szerokość geograficzna", format="%.6f")
            submitted = st.form_submit_button("Dodaj")
            if submitted:
                id_regionu = regiony_map[region_nazwa]
                try:
                    typ_norm = str(typ).strip().lower()
                except:
                    typ_norm = ''
                if typ_norm.startswith('schron'):
                    success, msg = crud.add_schronisko_transaction(id_regionu, nazwa, wysokosc, '08:00', '20:00', dlugosc, szerokosc)
                else:
                    success, msg = crud.add_punkt(id_regionu, nazwa, typ, wysokosc, dlugosc, szerokosc)
                if success:
                    st.session_state['punkty_add_success'] = True
                    safe_rerun()
                else:
                    st.error(msg)

def view_odleglosci_manager():
    st.header("↔️ Odległości między punktami")
    if 'odl_add_success' not in st.session_state:
        st.session_state['odl_add_success'] = False
    if st.session_state['odl_add_success']:
        st.success("Dodano odległość.")
        st.session_state['odl_add_success'] = False
    tab_labels = ["📋 Przegląd i Edycja", "➕ Dodaj odległość"]
    tab1, tab2 = st.tabs(tab_labels)
    with tab1:
        st.subheader("")
        df = crud.get_odleglosci()
        punkty_df = crud.get_punkty()
        punkty_rev = {row['ID_PUNKTU']: row['NAZWA'] for i, row in punkty_df.iterrows()}
        if not df.empty:
            df_display = df.copy()
            df_display['PUNKT_OD'] = df_display['ID_PKT_OD'].map(punkty_rev).fillna(df_display['ID_PKT_OD'])
            df_display['PUNKT_DO'] = df_display['ID_PKT_DO'].map(punkty_rev).fillna(df_display['ID_PKT_DO'])
            cols = ['PUNKT_OD', 'PUNKT_DO', 'ODLEGLOSC', 'PRZEWYSZENIE', 'CZAS_PRZEJSCIA']
            available = [c for c in cols if c in df_display.columns]
            st.dataframe(df_display[available], width="stretch")
        else:
            st.dataframe(df, width="stretch")
        opts = {}
        for i, row in df.iterrows():
            od = punkty_rev.get(row['ID_PKT_OD'], row['ID_PKT_OD'])
            do = punkty_rev.get(row['ID_PKT_DO'], row['ID_PKT_DO'])
            label = f"{od} -> {do} ({row.get('ODLEGLOSC', '')} km)"
            opts[label] = (row['ID_PKT_OD'], row['ID_PKT_DO'])
        sel = st.selectbox("Wybierz odległość do usunięcia", ["-- Wybierz --"] + list(opts.keys()))
        if sel != "-- Wybierz --":
            if st.button("Usuń odległość"):
                id_od, id_do = opts[sel]
                success, msg = crud.delete_odleglosc(id_od, id_do)
                if success:
                    st.success("Usunięto odległość.")
                    safe_rerun()
                else:
                    st.error(msg)
    with tab2:
        st.subheader("")
        punkty_df = crud.get_punkty()
        punkty_map = {f"{row['NAZWA']} (ID: {row['ID_PUNKTU']})": row['ID_PUNKTU'] for i, row in punkty_df.iterrows()}
        with st.form("add_odl_form"):
            sel_od = st.selectbox("Punkt od", list(punkty_map.keys()), key="odl_od")
            sel_do = st.selectbox("Punkt do", list(punkty_map.keys()), key="odl_do")
            odl = st.number_input("Odległość (km)", min_value=0.001, format="%.3f")
            przew = st.number_input("Przewyższenie (m)", min_value=0.0, format="%.3f")
            czas = st.number_input("Czas przejścia (min)", min_value=1)
            if st.form_submit_button("Dodaj"):
                id_od = punkty_map[sel_od]
                id_do = punkty_map[sel_do]
                success, msg = crud.add_odleglosc(id_od, id_do, odl, przew, czas)
                if success:
                    st.session_state['odl_add_success'] = True
                    safe_rerun()
                else:
                    st.error(msg)
if __name__ == "__main__":
    main()