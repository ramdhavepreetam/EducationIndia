import psycopg2
import os

from dotenv import load_dotenv
load_dotenv('.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("SELECT e.id, ev.year, ev.grade, e.paper_no, e.title_en FROM exams e JOIN exam_events ev ON e.event_id = ev.id;")
print(cur.fetchall())
