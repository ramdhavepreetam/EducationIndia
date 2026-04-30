import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

dsn = os.getenv("DATABASE_URL").replace("+asyncpg", "")
conn = psycopg2.connect(dsn)
conn.autocommit = True
cur = conn.cursor()

with open("database/migration_multi_select.sql", "r") as f:
    sql = f.read()
    cur.execute(sql)

print("Migration applied successfully.")
cur.close()
conn.close()
