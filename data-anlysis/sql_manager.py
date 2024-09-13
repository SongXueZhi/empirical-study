import mysql.connector
from mysql.connector import Error

class MySQLDatabase:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        """Establish a connection to the MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("Connected to MySQL database")
        except Error as e:
            print(f"Error: {e}")
            self.connection = None

    def disconnect(self):
        """Close the connection to the MySQL database."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Disconnected from MySQL database")

    def execute_query(self, query, params=None):
        """Execute a single query."""
        if self.connection is None or not self.connection.is_connected():
            print("Not connected to the database")
            return None

        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            self.connection.commit()
            print("Query executed successfully")
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()

    def fetch_query(self, query, params=None):
        """Execute a query and fetch all results."""
        if self.connection is None or not self.connection.is_connected():
            print("Not connected to the database")
            return None

        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Error: {e}")
            return None
        finally:
            cursor.close()

    def fetch_query_one(self, query, params=None):
        """Execute a query and fetch one result."""
        if self.connection is None or not self.connection.is_connected():
            print("Not connected to the database")
            return None

        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error: {e}")
            return None
        finally:
            cursor.close()

# 使用示例
if __name__ == "__main__":
    db = MySQLDatabase("localhost", "root", "password", "test_db")
    db.connect()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        age INT NOT NULL
    )
    """
    db.execute_query(create_table_query)

    insert_query = "INSERT INTO users (name, age) VALUES (%s, %s)"
    db.execute_query(insert_query, ("John Doe", 28))

    select_query = "SELECT * FROM users"
    users = db.fetch_query(select_query)
    for user in users:
        print(user)

    db.disconnect()