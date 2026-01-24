database.py -> obsługa połączenia z bazą danych
crud.py -> wykonywanie operacji na bazie danych (create read update delete)
app.py -> obsługa aplikacji webowej (streamlit UI)

TODO

Co mamy zrobione:

Podział na app.py (UI), crud.py (SQL/Logika), database.py (Driver/Config).
Obsługa błędów Oracle (zamiana kodów ORA-xxxxx na ludzkie komunikaty).
Wyciszenie ostrzeżeń biblioteki Pandas.

Moduł Regiony:
Wyświetlanie (Read).
Dodawanie (Create).
Usuwanie (Delete).
Brakuje edycji (Update).

Moduł Szlaki (CRUD):
Pełne Create, Read, Update, Delete.
Wyszukiwanie po nazwie.
Formularze z listami rozwijanymi (Słowniki kolorów i trudności).

Moduł Schroniska:
Wyświetlanie (Read) z JOINem do regionów.
Dodawanie (Create) z transakcją (najpierw tabela punkty, potem schroniska).
Wspomaganie użytkownika (wybór regionu z listy).

Moduł Pokoje:
Dodawanie (Create)
Wyświetlanie (Read).
Wyszukiwanie (Search).
Edycja (Update) – zmiana ceny i miejsc.
Usuwanie (Delete).

Moduł Rezerwacje - tu uzyte procedury: (nie sprawdzone bo nie mamy jeszcze podzialu na userow!)
Wykorzystanie procedury składowanej (dokonaj_rezerwacji).
Wykorzystanie funkcji składowanej (oblicz_koszt_pobytu).
Filtrowanie pokoi po wyborze schroniska.


Czego brakuje:

Brak edycji i usuwania Schronisk (Update/Delete):
Schroniska można tylko dodawać. Jeśli użytkownik zrobi literówkę w nazwie schroniska, nie ma jak jej poprawić w aplikacji.

Brak zarządzania Użytkownikami:
Mamy tabelę uzytkownicy, ale używamy jej tylko do odczytu przy rezerwacji. Nie można dodać nowego użytkownika przez aplikację.

Pozostałe tabele:
wyposazenia, pokoje_wyposazenie – brak obsługi (przydzielanie wyposażenia do pokoi).