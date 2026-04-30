import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv("/Users/preetam/Documents/AI/scholarpath/.env")

def get_answer(answers_data, paper_code, q_no):
    ans_list = answers_data.get(paper_code, {}).get(str(q_no))
    multi_qs = answers_data.get("multi_select_questions", {}).get(paper_code, [])
    
    if not ans_list:
        return None, None, False
        
    is_multi = q_no in multi_qs
    
    if is_multi:
        return None, ans_list, True
    else:
        # It might have multiple OR options, but it's single select
        return ans_list[0], ans_list, False

def bulk_import_p2():
    dsn = os.getenv("DATABASE_URL").replace("+asyncpg", "")
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    # Mapping based on previous query
    # Paper 32 (Paper I): Section 45 (Marathi), Section 46 (Math)
    # Paper 33 (Paper II): Section 47 (English), Section 48 (Intelligence)
    
    sections = {
        "0801_S2": {"exam_id": 32, "section_id": 46, "topic_id": 275},
        "0802_S2": {"exam_id": 33, "section_id": 48, "topic_id": 277}
    }

    files = [
        ("/Users/preetam/Documents/AI/scholarpath/8th_2025_p1_math_extracted.json", "0801", "0801_S2"),
        ("/Users/preetam/Documents/AI/scholarpath/8th_2025_p2_intel_extracted.json", "0802", "0802_S2")
    ]
    
    with open("/Users/preetam/Documents/AI/scholarpath/answers_8th_2025.json", "r") as f:
        answers_data = json.load(f)

    try:
        for filepath, paper_code, key in files:
            with open(filepath, "r") as f:
                data = json.load(f)
            
            s_info = sections[key]
            print(f"Importing {len(data)} questions for {key}...")
            
            for item in data:
                q_no = item["q"]
                text_en = item.get("text_en")
                
                # Fetch answers
                correct_option, correct_options, is_multi = get_answer(answers_data, paper_code, q_no)
                
                # Insert Question
                cur.execute("""
                    INSERT INTO questions (
                        exam_id, section_id, topic_id, question_no, question_type, 
                        text_en, correct_option, correct_options, is_multi_select
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    s_info["exam_id"], s_info["section_id"], s_info["topic_id"], q_no,
                    "text", # English only for now
                    text_en, correct_option, correct_options, is_multi
                ))
                q_id = cur.fetchone()[0]
                
                # Insert Options
                opts_en = item.get("opts_en", [])
                
                for i in range(4):
                    o_no = i + 1
                    o_en = opts_en[i] if i < len(opts_en) else None
                    
                    cur.execute("""
                        INSERT INTO options (question_id, option_no, text_en)
                        VALUES (%s, %s, %s)
                    """, (q_id, o_no, o_en))
        
        conn.commit()
        print("Bulk import complete.")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    bulk_import_p2()
