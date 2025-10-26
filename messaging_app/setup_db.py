# messaging_app/setup_db.py
import os
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv

def create_database():
    """
    Connects to the MySQL server and creates the database from .env if it doesn't exist.
    """
    # Load environment variables from .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=env_path)

    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")

    if not all([db_name, db_user, db_password, db_host, db_port]):
        print("Database configuration is missing in the .env file.")
        return

    try:
        # Connect to the MySQL server (without specifying a database)
        cnx = mysql.connector.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        cursor = cnx.cursor()

        # Check if the database exists
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        if cursor.fetchone():
            print(f"Database '{db_name}' already exists.")
        else:
            print(f"Database '{db_name}' not found. Creating it...")
            cursor.execute(
                f"CREATE DATABASE {db_name} CHARACTER SET 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'"
            )
            print(f"Database '{db_name}' created successfully.")

        cursor.close()
        cnx.close()

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_database()