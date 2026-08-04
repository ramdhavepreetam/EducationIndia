import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("/Users/preetam/Documents/AI/scholarpath/.env")
dsn = os.getenv("DATABASE_URL").replace("+asyncpg", "")
conn = psycopg2.connect(dsn)
cur = conn.cursor()

# Paper 2 (0802) Intelligence
exam_id = 33
section_id = 48
topic_id = 277

missing_qs = [
    {
        "q_no": 26,
        "text": "Below given are two statements and two conclusions. Select the correct alternative depending on it.\nStatement - I) Organic fertilizers are used for fruit-plants.\nII) Productivity increases by using organic fertilizers.\nConclusions - A) Fruit bearing capacity of plants increases because of the use of organic fertilizers.\nB) Plants cannot bear fruits without the use of organic fertilizers.",
        "opts": [
            "Conclusion B is correct",
            "Both conclusions A and B are correct",
            "Both conclusions A and B are incorrect",
            "Conclusion A is correct"
        ],
        "ans": 4,
        "ans_list": [4],
        "is_multi": False
    },
    {
        "q_no": 27,
        "text": "Find the correct alternative to complete the given question figure.",
        "opts": ["Figure 1", "Figure 2", "Figure 3", "Figure 4"],
        "ans": 4,
        "ans_list": [4],
        "is_multi": False
    },
    {
        "q_no": 28,
        "text": "Find the incorrect term from the given series:\n420, 462, 506, 554, 600, 650, 702",
        "opts": ["600", "554", "420", "702"],
        "ans": 2,
        "ans_list": [2],
        "is_multi": False
    },
    {
        "q_no": 58,
        "text": "Observe the pyramid given below. Find the relation between the numbers and alphabets order and find the term in place of question mark.",
        "opts": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "ans": 3,
        "ans_list": [3],
        "is_multi": False
    },
    {
        "q_no": 72,
        "text": "Complete the number series:\n116 ? 262\n3 5 8 6 9 7",
        "opts": ["208", "476", "125", "152"],
        "ans": 4,
        "ans_list": [4],
        "is_multi": False
    }
]

try:
    for q in missing_qs:
        cur.execute("""
            INSERT INTO questions (
                exam_id, section_id, topic_id, question_no, question_type, 
                text_en, correct_option, correct_options, is_multi_select
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            exam_id, section_id, topic_id, q["q_no"], "text",
            q["text"], q["ans"], q["ans_list"], q["is_multi"]
        ))
        q_id = cur.fetchone()[0]
        
        for i, opt_text in enumerate(q["opts"]):
            cur.execute("""
                INSERT INTO options (question_id, option_no, text_en)
                VALUES (%s, %s, %s)
            """, (q_id, i+1, opt_text))
            
    conn.commit()
    print("Missing questions successfully inserted.")
except Exception as e:
    conn.rollback()
    print("Error:", e)
finally:
    cur.close()
    conn.close()
