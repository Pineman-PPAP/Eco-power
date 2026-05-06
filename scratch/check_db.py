import sqlite3
import pandas as pd

con = sqlite3.connect('data/karnataka_solar.db')
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

for table in tables:
    table_name = table[0]
    print(f"\nSchema for {table_name}:")
    df = pd.read_sql_query(f"PRAGMA table_info({table_name})", con)
    print(df)
    print(f"\nSample data for {table_name}:")
    sample = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", con)
    print(sample)

con.close()
