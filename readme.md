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

Moduł Rezerwacje - tu uzyte procedury:
Dodawanie (Create)
Wyświetlanie (Read)
Usuwanie(Delete)
Wyszukiwanie, w tym po uzytkownikach.
Wyświetlanie rezerwacji globalnych, z podziałem na uzytkownikow


Czego brakuje:

Brak edycji i usuwania Schronisk (Update/Delete):
Schroniska można tylko dodawać. Jeśli użytkownik zrobi literówkę w nazwie schroniska, nie ma jak jej poprawić w aplikacji.

vvv przeciez to mamy co autor (ja) mial na myśli pisząc to???
Brak zarządzania Użytkownikami:
Mamy tabelę uzytkownicy, ale używamy jej tylko do odczytu przy rezerwacji. Nie można dodać nowego użytkownika przez aplikację.

Pozostałe tabele:
wyposazenia, pokoje_wyposazenie – brak obsługi (przydzielanie wyposażenia do pokoi).

Do sprawdzenia:
Przy rezerwacji slider wyboru ilości osób ma być dynamiczny i nie dawać opcji wyboru więcej niz maksymalnej ilości osob do pokoju.
najlepiej jakby to nie był slider tbh.