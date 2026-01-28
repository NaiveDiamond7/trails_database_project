import oracledb
import pandas as pd
import warnings
import os

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

os.environ["NLS_LANG"] = "POLISH_POLAND.AL32UTF8"

DB_CONFIG = {
    "user": "system",
    "password": "Test123",
    "dsn": "localhost:1521/FREEPDB1"
}

def get_connection():
    return oracledb.connect(**DB_CONFIG)

def execute_query_df(query, params=None):
    """Zwraca wynik SELECT jako Pandas DataFrame"""
    conn = get_connection()
    try:
        if params:
            return pd.read_sql(query, conn, params=params)
        return pd.read_sql(query, conn)
    finally:
        conn.close()

def execute_dml(query, params):
    """Wykonuje INSERT/UPDATE/DELETE. Zwraca (bool, message)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return True, "Operacja zakończona sukcesem."
    except Exception as e:
        msg = str(e)
        if "ORA-00001" in msg:
            return False, "Taki wpis już istnieje. Zmień dane lub wybierz inną nazwę."
        if "ORA-02292" in msg:
            return False, "Nie można usunąć, bo element jest powiązany z innymi danymi."
        if "ORA-02290" in msg:
            return False, "Wprowadzone dane nie spełniają wymagań (np. ograniczenia liczby znaków, zakresu lub formatu)."
        if "ORA-12899" in msg:
            return False, "Za długa wartość w jednym z pól tekstowych. Skróć dane."
        if "ORA-01400" in msg:
            return False, "Pole wymagane nie może być puste. Uzupełnij wszystkie wymagane pola."
        if "ORA-01438" in msg:
            return False, "Wartość liczby jest za duża dla tego pola."
        return False, f"Błąd: {msg.split(':')[-1].strip()}"
    finally:
        cursor.close()
        conn.close()

def execute_procedure(name, params):
    """Wywołuje procedurę składowaną"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.callproc(name, params)
        conn.commit()
        return True, "Operacja zakończona sukcesem."
    except Exception as e:
        msg = str(e)
        if "ORA-00001" in msg:
            return False, "Taki wpis już istnieje. Zmień dane lub wybierz inną nazwę."
        if "ORA-02292" in msg:
            return False, "Nie można usunąć, bo element jest powiązany z innymi danymi."
        if "ORA-02290" in msg:
            return False, "Wprowadzone dane nie spełniają wymagań (np. ograniczenia liczby znaków, zakresu lub formatu)."
        if "ORA-12899" in msg:
            return False, "Za długa wartość w jednym z pól tekstowych. Skróć dane."
        if "ORA-01400" in msg:
            return False, "Pole wymagane nie może być puste. Uzupełnij wszystkie wymagane pola."
        if "ORA-01438" in msg:
            return False, "Wartość liczby jest za duża dla tego pola."
        return False, f"Błąd: {msg.split(':')[-1].strip()}"
    finally:
        cursor.close()
        conn.close()

def execute_function(name, return_type, params):
    """Wywołuje funkcję składowaną"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        return cursor.callfunc(name, return_type, params)
    except Exception as e:
        msg = str(e)
        return None
    finally:
        cursor.close()
        conn.close()