import os
import psycopg2

from dotenv import load_dotenv
load_dotenv('.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
cur = conn.cursor()

cur.execute("SELECT id, title_en, year FROM exam_events ORDER BY year DESC;")
events = cur.fetchall()
print("Exam Events:")
for e in events:
    print(f"ID: {e[0]}, Year: {e[2]}, Title: {e[1]}")

cur.execute("SELECT id, event_id, title_en FROM exams;")
exams = cur.fetchall()
print("\nExams:")
for ex in exams:
    print(f"ID: {ex[0]}, Event ID: {ex[1]}, Title: {ex[2]}")
