import pyodbc

def fix_phone_column():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            'SERVER=localhost,1433;'
            'DATABASE=CinemaDB;'
            'UID=sa;'
            'PWD=reallyStrongPwd123;'
            'Encrypt=no;'
            'TrustServerCertificate=yes;'
        )
        cursor = conn.cursor()
        print("Connected to DB...")

        # 1. Drop Constraint
        print("Dropping constraint CK_Customer_PhoneNumber...")
        try:
            cursor.execute("ALTER TABLE Customer DROP CONSTRAINT CK_Customer_PhoneNumber")
        except Exception as e:
            print(f"Constraint might not exist or verify name: {e}")

        # 2. Alter Column to VARCHAR(20)
        # Note: If there is data that doesn't fit, this might fail, but currently DB is likely empty or has purely numeric data.
        print("Altering column to VARCHAR(20)...")
        # We might need to drop dependent indices if any, but usually none on phone yet.
        cursor.execute("ALTER TABLE Customer ALTER COLUMN phone_number VARCHAR(20)")

        # 3. Add Strict Constraint
        print("Adding strict 11-digit constraint...")
        pattern = "[0-9]" * 11
        sql = f"ALTER TABLE Customer ADD CONSTRAINT CK_Customer_PhoneNumber CHECK (phone_number IS NULL OR phone_number LIKE '{pattern}')"
        cursor.execute(sql)
        
        conn.commit()
        print("Success! Column altered and constraint re-applied.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_phone_column()
