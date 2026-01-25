import oracledb
import pandas as pd
import warnings
import os

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')
# Wylaczamy ostrzezenia Pandas dotyczace SQLAlchemy, ktore nie sa istotne w tym kontekscie.

os.environ["NLS_LANG"] = "POLISH_POLAND.AL32UTF8"

# Konfiguracja Docker
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
    except oracledb.IntegrityError as e:
        error_obj = e.args[0]
        if "ORA-00001" in error_obj.message:
            return False, "Błąd: Taki wpis już istnieje."
        elif "ORA-02292" in error_obj.message:
            return False, "Błąd: Element jest używany w innej tabeli."
        elif "ORA-02290" in error_obj.message:
            return False, f"Błąd walidacji (Check Constraint): {error_obj.message}"
        else:
            return False, f"Błąd bazy: {error_obj.message}"
    except Exception as e:
        return False, f"Błąd systemowy: {str(e)}"
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
        return True, "Procedura wykonana pomyślnie."
    except Exception as e:
        return False, f"Błąd procedury: {str(e)}"
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
        return None
    finally:
        cursor.close()
        conn.close()