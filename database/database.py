import mysql.connector
from mysql.connector import Error

from config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD
)


class Database:
    """
    Database connection and query manager
    for the Intelligent CV Screening System.
    """

    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """Create a connection to MySQL/MariaDB."""

        try:
            self.connection = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )

            if self.connection.is_connected():
                print("Database connected successfully.")

        except Error as error:
            print(f"Database connection failed: {error}")
            self.connection = None

    def reconnect(self):
        """Reconnect if the connection has been lost."""

        try:
            if self.connection is None or not self.connection.is_connected():
                self.connect()
        except Error:
            self.connect()

    def execute_query(self, query, params=None):
        """
        Execute INSERT, UPDATE or DELETE queries.
        Returns True when successful.
        """

        self.reconnect()

        if self.connection is None:
            return False

        cursor = None

        try:
            cursor = self.connection.cursor()

            cursor.execute(query, params or ())
            self.connection.commit()

            return True

        except Error as error:
            print(f"Query execution failed: {error}")

            if self.connection:
                self.connection.rollback()

            return False

        finally:
            if cursor:
                cursor.close()

    def fetch_one(self, query, params=None):
        """Return one database record."""

        self.reconnect()

        if self.connection is None:
            return None

        cursor = None

        try:
            cursor = self.connection.cursor(dictionary=True)

            cursor.execute(query, params or ())

            return cursor.fetchone()

        except Error as error:
            print(f"Fetch operation failed: {error}")
            return None

        finally:
            if cursor:
                cursor.close()

    def fetch_all(self, query, params=None):
        """Return all records from a query."""

        self.reconnect()

        if self.connection is None:
            return []

        cursor = None

        try:
            cursor = self.connection.cursor(dictionary=True)

            cursor.execute(query, params or ())

            return cursor.fetchall()

        except Error as error:
            print(f"Fetch operation failed: {error}")
            return []

        finally:
            if cursor:
                cursor.close()

    def insert(self, query, params=None):
        """
        Insert a record and return the generated ID.
        """

        self.reconnect()

        if self.connection is None:
            return None

        cursor = None

        try:
            cursor = self.connection.cursor()

            cursor.execute(query, params or ())
            self.connection.commit()

            return cursor.lastrowid

        except Error as error:
            print(f"Insert operation failed: {error}")

            if self.connection:
                self.connection.rollback()

            return None

        finally:
            if cursor:
                cursor.close()

    def update(self, query, params=None):
        """
        Update records and return the number of affected rows.
        """

        self.reconnect()

        if self.connection is None:
            return 0

        cursor = None

        try:
            cursor = self.connection.cursor()

            cursor.execute(query, params or ())
            self.connection.commit()

            return cursor.rowcount

        except Error as error:
            print(f"Update operation failed: {error}")

            if self.connection:
                self.connection.rollback()

            return 0

        finally:
            if cursor:
                cursor.close()

    def delete(self, query, params=None):
        """
        Delete records and return the number of affected rows.
        """

        self.reconnect()

        if self.connection is None:
            return 0

        cursor = None

        try:
            cursor = self.connection.cursor()

            cursor.execute(query, params or ())
            self.connection.commit()

            return cursor.rowcount

        except Error as error:
            print(f"Delete operation failed: {error}")

            if self.connection:
                self.connection.rollback()

            return 0

        finally:
            if cursor:
                cursor.close()

    def close(self):
        """Close the database connection."""

        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                print("Database connection closed.")
        except Error as error:
            print(f"Error closing database connection: {error}")


# Create a reusable database instance
db = Database()


def get_db():
    """
    Return the shared database instance.
    """

    return db


if __name__ == "__main__":
    print("----------------------------------------")
    print("CV SCREENING SYSTEM DATABASE TEST")
    print("----------------------------------------")

    database = Database()

    if database.connection:
        print("Database object created successfully.")
    else:
        print("Database is currently unavailable.")

    database.close()