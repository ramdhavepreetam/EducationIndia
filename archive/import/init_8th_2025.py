import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("/Users/preetam/Documents/AI/scholarpath/.env")

def init_8th_grade():
    dsn = os.getenv("DATABASE_URL").replace("+asyncpg", "")
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    try:
        # 1. Ensure Exam Board exists (MSCE)
        board_id = 1 # We know this from earlier query

        # 2. Create Category for 8th Grade (Pre-Secondary Scholarship)
        cur.execute("""
            INSERT INTO exam_categories (board_id, name_en, name_mr, description_en, is_active)
            VALUES (%s, %s, %s, %s, true)
            ON CONFLICT (id) DO NOTHING
            RETURNING id
        """, (board_id, "Pre-Secondary Scholarship", "पूर्व माध्यमिक शिष्यवृत्ती परीक्षा", "Maharashtra Scholarship Exam for 8th Standard"))
        
        result = cur.fetchone()
        if result:
            category_id = result[0]
        else:
            cur.execute("SELECT id FROM exam_categories WHERE name_en = 'Pre-Secondary Scholarship'")
            category_id = cur.fetchone()[0]
        
        print(f"Category ID: {category_id}")

        # 3. Create Exam Event for 2025
        cur.execute("""
            INSERT INTO exam_events (board_id, category_id, title_en, title_mr, std_class, year, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, true)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (board_id, category_id, "MSCE 8th Std 2025", "म.शा.प.प. ८ वी शिष्यवृत्ती २०२५", 8, 2025))
        
        result = cur.fetchone()
        if result:
            event_id = result[0]
        else:
            cur.execute("SELECT id FROM exam_events WHERE title_en = 'MSCE 8th Std 2025'")
            event_id = cur.fetchone()[0]
            
        print(f"Event ID: {event_id}")

        # 4. Create Exams (Paper I and Paper II)
        # Paper I
        cur.execute("""
            INSERT INTO exams (event_id, paper_code, paper_number, title_en, title_mr, medium, total_questions, total_marks, is_active)
            VALUES (%s, %s, 1, 'Paper I: Marathi & Mathematics', 'पेपर १: मराठी व गणित', 'marathi', 75, 150, true)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (event_id, "0801"))
        result = cur.fetchone()
        paper1_id = result[0] if result else None
        if not paper1_id:
            cur.execute("SELECT id FROM exams WHERE paper_code = '0801'")
            paper1_id = cur.fetchone()[0]

        # Paper II
        cur.execute("""
            INSERT INTO exams (event_id, paper_code, paper_number, title_en, title_mr, medium, total_questions, total_marks, is_active)
            VALUES (%s, %s, 2, 'Paper II: English & Intelligence Test', 'पेपर २: इंग्रजी व बुद्धिमत्ता चाचणी', 'marathi', 75, 150, true)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (event_id, "0802"))
        result = cur.fetchone()
        paper2_id = result[0] if result else None
        if not paper2_id:
            cur.execute("SELECT id FROM exams WHERE paper_code = '0802'")
            paper2_id = cur.fetchone()[0]

        print(f"Paper I ID: {paper1_id}, Paper II ID: {paper2_id}")

        # 5. Create Sections
        # Paper 1 Sections
        sections = [
            (paper1_id, "I", "First Language (Marathi)", "प्रथम भाषा (मराठी)", 1, 25, 1, "#3B82F6"),
            (paper1_id, "II", "Mathematics", "गणित", 26, 75, 2, "#10B981"),
            (paper2_id, "I", "Third Language (English)", "तृतीय भाषा (इंग्रजी)", 1, 25, 1, "#F59E0B"),
            (paper2_id, "II", "Intelligence Test", "बुद्धिमत्ता चाचणी", 26, 75, 2, "#8B5CF6")
        ]
        
        for s in sections:
            cur.execute("""
                INSERT INTO sections (exam_id, section_label, subject_en, subject_mr, question_from, question_to, order_index, color_hex)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, s)
            result = cur.fetchone()
            if result:
                section_id = result[0]
                cur.execute("""
                    INSERT INTO topics (section_id, name_en, name_mr, order_index)
                    VALUES (%s, 'General', 'सामान्य', 1)
                    ON CONFLICT DO NOTHING
                """, (section_id,))

        conn.commit()
        print("Initialization complete.")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    init_8th_grade()
