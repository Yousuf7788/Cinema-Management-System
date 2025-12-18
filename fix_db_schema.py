from database import Database
import pyodbc

def fix_schema():
    db = Database()
    # Use credentials from main.py
    server = "localhost,1433"
    database = "CinemaDB"
    username = "sa"
    password = "reallyStrongPwd123"
    
    if not db.connect(server, database, username, password):
        print("Failed to connect to database using explicit credentials")
        return

    cursor = db.connection.cursor()
    
    try:
        # Find the constraint name dynamically
        print("Finding constraint name...")
        cursor.execute("SELECT name FROM sys.check_constraints WHERE parent_object_id = OBJECT_ID('Booking') AND definition LIKE '%status%'")
        row = cursor.fetchone()
        
        if row:
            constraint_name = row[0]
            print(f"Found constraint: {constraint_name}")
            
            # Drop the old constraint
            print(f"Dropping constraint {constraint_name}...")
            cursor.execute(f"ALTER TABLE Booking DROP CONSTRAINT {constraint_name}")
            db.connection.commit()
            
            # Add new constraint with 'pending_refund', 'pending_approval', 'pending'
            print("Adding new constraint...")
            cursor.execute("ALTER TABLE Booking ADD CONSTRAINT CK_Booking_Status CHECK (status IN ('confirmed', 'cancelled', 'refunded', 'pending_refund', 'pending_approval', 'pending'))")
            db.connection.commit()
            print("Schema updated successfully!")
        else:
            print("No matching constraint found. It might have been already updated or has a different definition.")

            # Optional: Try to add it anyway if it doesn't exist
            try:
                print("Attempting to add constraint anyway...")
                # Updated allowed statuses to include 'pending_approval' and 'pending'
                cursor.execute("ALTER TABLE Booking ADD CONSTRAINT CK_Booking_Status CHECK (status IN ('confirmed', 'cancelled', 'refunded', 'pending_refund', 'pending_approval', 'pending'))")
                db.connection.commit()
                print("Added new constraint.")
            except Exception as e:
                print(f"Could not add constraint: {e}")

        # --- NEW: Update Default Value ---
        print("Finding default constraint for status...")
        cursor.execute("""
            SELECT name 
            FROM sys.default_constraints 
            WHERE parent_object_id = OBJECT_ID('Booking') 
            AND parent_column_id = (
                SELECT column_id 
                FROM sys.columns 
                WHERE object_id = OBJECT_ID('Booking') AND name = 'status'
            )
        """)
        row = cursor.fetchone()
        
        if row:
            default_constraint = row[0]
            print(f"Found default constraint: {default_constraint}")
            print("Dropping old default...")
            cursor.execute(f"ALTER TABLE Booking DROP CONSTRAINT {default_constraint}")
            db.connection.commit()
        
        print("Adding new default 'pending'...")
        cursor.execute("ALTER TABLE Booking ADD DEFAULT 'pending' FOR status")
        db.connection.commit()
        print("Default value updated to 'pending'.")


    except Exception as e:
        print(f"Error updating schema: {e}")
        db.connection.rollback()
    finally:
        db.connection.close()

if __name__ == "__main__":
    fix_schema()
