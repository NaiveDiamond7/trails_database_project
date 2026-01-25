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
Usuwanie(Delete)
Edyscja(Udpate)

Moduł Pokoje:
Dodawanie (Create)
Wyświetlanie (Read).
Wyszukiwanie (Search).
Edycja (Update) – zmiana ceny i miejsc.
Usuwanie (Delete).

Moduł Rezerwacje - tu uzyte procedury:
Dodawanie (Create)
Wyświetlanie (Read)
Usuwanie(Delete)
Wyszukiwanie, w tym po uzytkownikach.
Wyświetlanie rezerwacji globalnych, z podziałem na uzytkownikow


Sekcja schroniska aktualizuje i usuwa rekordy z dwóch tabeli wedle schematu! (połączenie tabel schroniska i punkty)


Czego brakuje:

Pozostałe tabele:
wyposazenia, pokoje_wyposazenie – brak obsługi (przydzielanie wyposażenia do pokoi).
