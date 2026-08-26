import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
cur = conn.cursor()

def create_exam_year(year):
    # 1. Create Exam Event
    cur.execute("""
        INSERT INTO exam_events (title_en, year, std_class) 
        VALUES (%s, %s, %s) RETURNING id
    """, (f"Pre-Upper Primary Scholarship Examination {year}", year, 5))
    event_id = cur.fetchone()[0]
    
    # 2. Create Paper 1
    cur.execute("""
        INSERT INTO exams (event_id, paper_code, paper_number, title_en, total_questions, total_marks, marks_per_question, duration_minutes) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (event_id, "501", 1, "Paper I — First Language & Mathematics", 75, 150, 2, 90))
    paper1_id = cur.fetchone()[0]
    
    # 3. Create Paper 2
    cur.execute("""
        INSERT INTO exams (event_id, paper_code, paper_number, title_en, total_questions, total_marks, marks_per_question, duration_minutes) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (event_id, "502", 2, "Paper II — Third Language & Intelligence Test", 75, 150, 2, 90))
    paper2_id = cur.fetchone()[0]
    
    # We also need to copy Sections and Topics for these newly created exams. 
    # For Paper 1: We can copy from exam_id 1
    cur.execute("SELECT id, subject_en, question_from, question_to, order_index, section_label FROM sections WHERE exam_id=1")
    for sec_old in cur.fetchall():
        cur.execute("""
            INSERT INTO sections (exam_id, section_label, subject_en, question_from, question_to, order_index)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (paper1_id, sec_old[5], sec_old[1], sec_old[2], sec_old[3], sec_old[4]))
        sec_new_id = cur.fetchone()[0]
        # Insert topics
        cur.execute("SELECT name_en, name_mr, order_index FROM topics WHERE section_id=%s", (sec_old[0],))
        for top_old in cur.fetchall():
            cur.execute("""
                INSERT INTO topics (section_id, name_en, name_mr, order_index)
                VALUES (%s, %s, %s, %s)
            """, (sec_new_id, top_old[0], top_old[1], top_old[2]))

    # For Paper 2: copy from exam_id 2
    cur.execute("SELECT id, subject_en, question_from, question_to, order_index, section_label FROM sections WHERE exam_id=2")
    for sec_old in cur.fetchall():
        cur.execute("""
            INSERT INTO sections (exam_id, section_label, subject_en, question_from, question_to, order_index)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (paper2_id, sec_old[5], sec_old[1], sec_old[2], sec_old[3], sec_old[4]))
        sec_new_id = cur.fetchone()[0]
        # Insert topics
        cur.execute("SELECT name_en, name_mr, order_index FROM topics WHERE section_id=%s", (sec_old[0],))
        for top_old in cur.fetchall():
            cur.execute("""
                INSERT INTO topics (section_id, name_en, name_mr, order_index)
                VALUES (%s, %s, %s, %s)
            """, (sec_new_id, top_old[0], top_old[1], top_old[2]))

    print(f"Created infrastructure for year {year}: Paper1 ID={paper1_id}, Paper2 ID={paper2_id}")

    return paper1_id, paper2_id

# Just running it for 2017 to test the logic
if __name__ == "__main__":
    try:
        p1, p2 = create_exam_year(2017)
        conn.commit()
        print("Successfully committed infrastructure for 2017.")
    except Exception as e:
        conn.rollback()
        print(e)
