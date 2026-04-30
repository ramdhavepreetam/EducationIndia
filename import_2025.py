import os
import psycopg2
import json
import pdfplumber
import fitz

from dotenv import load_dotenv
load_dotenv('.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
cur = conn.cursor()

def reset_db_state(exam_id):
    print(f"Reseting state for exam {exam_id}...")
    # Delete options for questions belonging to this exam
    cur.execute("""
        DELETE FROM options 
        WHERE question_id IN (
            SELECT id FROM questions WHERE exam_id = %s
        )
    """, (exam_id,))
    
    # Delete questions
    cur.execute("DELETE FROM questions WHERE exam_id = %s", (exam_id,))
    
    # Delete contexts
    cur.execute("DELETE FROM question_contexts WHERE exam_id = %s", (exam_id,))
    
    print(f"Deleted old questions and contexts for exam {exam_id}")

if __name__ == "__main__":
    try:
        reset_db_state(1)
        reset_db_state(2)
        conn.commit()
        print("Database reset successful.")
    except Exception as e:
        conn.rollback()
        print(f"Error reseting DB: {e}")
    finally:
        conn.close()
