import pyodbc
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


from sqlalchemy import create_engine, text
import pyodbc
from urllib.parse import quote_plus

# =====================================================
# KONFIGURACIJA – MENJAŠ SAMO OVAJ DEO
# =====================================================

SERVER = ".\\SQLEXPRESS"
DATABASE = "ElPatron"
LOGIN = "bane"
PASSWORD = "Administrator.11"
ODBC_DRIVER = "ODBC Driver 17 for SQL Server"

# =====================================================
# TEST 1 – PYODBC (SQL AUTHENTICATION)
# =====================================================

def test_pyodbc_sql_auth():
    print(f"\n🔹 TEST 1: pyodbc (SQL Auth - User: {LOGIN})")
    try:
        # Kod SQL autentifikacije koristimo UID i PWD umesto Trusted_Connection
        conn_str = (
            f"DRIVER={{{ODBC_DRIVER}}};"
            f"SERVER={SERVER};"
            f"DATABASE={DATABASE};"
            f"UID={LOGIN};"
            f"PWD={PASSWORD};"
            f"Encrypt=no;"
            f"TrustServerCertificate=yes;"
        )
        
        # Popravljeno: conn_str (bilo je con_str)
        conn = pyodbc.connect(conn_str, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT SYSTEM_USER, DB_NAME()")
        user, db_name = cursor.fetchone()
        conn.close()

        print(f"✅ pyodbc konekcija OK (User: {user}, DB: {db_name})")

    except Exception as e:
        print(f"❌ pyodbc konekcija FAIL\n   {e}")


# =====================================================
# TEST 2 – SQLALCHEMY (SQL AUTHENTICATION)
# =====================================================

def test_sqlalchemy_sql_auth():
    print(f"\n🔹 TEST 2: SQLAlchemy (SQL Auth - User: {LOGIN})")
    try:
        # Format za SQLAlchemy sa kredencijalima: mssql+pyodbc://user:password@server/database
        uri = (
            f"mssql+pyodbc://{LOGIN}:{quote_plus(PASSWORD)}@{SERVER}/{DATABASE}"
            f"?driver={quote_plus(ODBC_DRIVER)}"
            f"&Encrypt=no"
            f"&TrustServerCertificate=yes"
        )

        engine = create_engine(uri, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT SYSTEM_USER, DB_NAME()"))
            user, db_name = result.fetchone()

        print(f"✅ SQLAlchemy konekcija OK (User: {user}, DB: {db_name})")

    except Exception as e:
        print(f"❌ SQLAlchemy konekcija FAIL\n   {e}")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    print("========================================")
    print("   SQL SERVER SQL AUTHENTICATION TEST")
    print("========================================")

   

    test_pyodbc_sql_auth()
    test_sqlalchemy_sql_auth()

    print("\n✔ Testiranje završeno.")