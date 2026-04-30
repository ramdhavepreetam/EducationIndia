import os
import psycopg2

from dotenv import load_dotenv
load_dotenv('.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
cur = conn.cursor()

def dump_exam(exam_id):
    print(f"\nEXAM {exam_id}")
    cur.execute("SELECT id, subject_en FROM sections WHERE exam_id=%s ORDER BY order_index", (exam_id,))
    secs = cur.fetchall()
    for sec in secs:
        print(f"  Section {sec[0]}: {sec[1]}")
        cur.execute("SELECT id, name_en FROM topics WHERE section_id=%s ORDER BY order_index", (sec[0],))
        for top in cur.fetchall():
            print(f"    Topic {top[0]}: {top[1]}")

dump_exam(1)
dump_exam(2)
