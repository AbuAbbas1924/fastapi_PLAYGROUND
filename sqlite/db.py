import sqlite3

connection = sqlite3.connect("sqlite/s3.db")
cursor = connection.cursor()

cursor.execute(
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)"
)
cursor.execute("CREATE TABLE todo (id INTEGER, task TEXT, complete BOOLEAN)")

connection.close()
