import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv("/Users/preetam/Documents/AI/scholarpath/.env")

def bulk_import():
    dsn = os.getenv("DATABASE_URL").replace("+asyncpg", "")
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    # Mapping based on previous query
    # Paper 32 (Paper I): Section 45 (Marathi), Section 46 (Math)
    # Paper 33 (Paper II): Section 47 (English), Section 48 (Intelligence)
    
    sections = {
        "0801_S1": {"exam_id": 32, "section_id": 45, "topic_id": 274},
        "0802_S1": {"exam_id": 33, "section_id": 47, "topic_id": 276}
    }

    files = [
        ("/Users/preetam/Documents/AI/scholarpath/8th_2025_p1_marathi.json", "0801_S1"),
        ("/Users/preetam/Documents/AI/scholarpath/8th_2025_p2_english.json", "0802_S1")
    ]

    try:
        for filepath, key in files:
            with open(filepath, "r") as f:
                data = json.load(f)
            
            s_info = sections[key]
            print(f"Importing {len(data)} questions for {key}...")
            
            for item in data:
                q_no = item["q"]
                text_en = item.get("text_en")
                text_mr = item.get("text_mr")
                
                # Correct answers
                correct_option = item.get("correct_option")
                correct_options = item.get("correct_options")
                is_multi = True if correct_options and len(correct_options) > 1 else False
                
                # Insert Question
                cur.execute("""
                    INSERT INTO questions (
                        exam_id, section_id, topic_id, question_no, question_type, 
                        text_en, text_mr, correct_option, correct_options, is_multi_select
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    s_info["exam_id"], s_info["section_id"], s_info["topic_id"], q_no,
                    "bilingual" if (text_en and text_mr) else ("text" if text_en else "marathi_only"),
                    text_en, text_mr, correct_option, correct_options, is_multi
                ))
                q_id = cur.fetchone()[0]
                
                # Insert Options
                opts_en = item.get("opts_en", [])
                opts_mr = item.get("opts_mr", [])
                
                for i in range(4):
                    o_no = i + 1
                    o_en = opts_en[i] if i < len(opts_en) else None
                    o_mr = opts_mr[i] if i < len(opts_mr) else None
                    
                    cur.execute("""
                        INSERT INTO options (question_id, option_no, text_en, text_mr)
                        VALUES (%s, %s, %s, %s)
                    """, (q_id, o_no, o_en, o_mr))
        
        conn.commit()
        print("Bulk import complete.")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    bulk_import()
