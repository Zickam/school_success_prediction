import sqlite3

print("do 'chown user ../../example.db' before dropping")

conn = sqlite3.connect("../../example.db")
conn.execute("PRAGMA foreign_keys = OFF")
conn.execute("DROP TABLE IF EXISTS users")
conn.commit()
conn.close()
