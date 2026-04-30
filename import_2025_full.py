import os
import psycopg2
import json
import pdfplumber
import fitz
import re

from dotenv import load_dotenv
load_dotenv('.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
cur = conn.cursor()

# Pre-extracted JSON files
with open('answers_2025.json') as f:
    answers = json.load(f)

with open('marathi_2025.json') as f:
    marathi_qs = json.load(f)

def clean_footer(text):
    return re.sub(r'SPACE FOR ROUGH WORK.*', '', text, flags=re.DOTALL)
    
def clean_header(text):
    text = re.sub(r'050[1-2]-English Set-A.*', '', text, flags=re.DOTALL)
    text = re.sub(r'CCC_050[1-2].*', '', text, flags=re.DOTALL)
    return text

def extract_pdf_questions(pdf_path, q_start, q_end, page_start=1):
    questions_data = {}
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages[page_start:]:
            page_text = page.extract_text()
            if page_text:
                page_text = clean_footer(page_text)
                page_text = clean_header(page_text)
                full_text += page_text + "\n"
                
    q_matches = re.split(r'\n0?([1-9]|[1-6][0-9]|7[0-5])\.\s', "\n" + full_text)
    
    for i in range(1, len(q_matches), 2):
        q_no = int(q_matches[i])
        if q_start <= q_no <= q_end:
            q_text = q_matches[i+1].strip()
            
            opts = ["", "", "", ""]
            m = re.search(r'\(1\)\s*(.*?)\s*(?=\(2\)|\(3\)|\(4\)|$)', q_text, re.DOTALL)
            m2 = re.search(r'\(2\)\s*(.*?)\s*(?=\(3\)|\(4\)|$)', q_text, re.DOTALL)
            m3 = re.search(r'\(3\)\s*(.*?)\s*(?=\(4\)|$)', q_text, re.DOTALL)
            m4 = re.search(r'\(4\)\s*(.*)', q_text, re.DOTALL)
            
            if m: opts[0] = m.group(1).strip()
            if m2: opts[1] = m2.group(1).strip()
            if m3: opts[2] = m3.group(1).strip()
            if m4: opts[3] = m4.group(1).strip()
            
            if m:
                q_text = q_text[:m.start()].strip()
                
            questions_data[q_no] = {
                "text": q_text,
                "options": opts
            }
            
    return questions_data

def insert_question(exam_id, section_id, topic_id, q_no, q_text_en, q_text_mr, opts_data, correct_option_idx):
    if not q_text_en and not q_text_mr:
        q_text_en = "[IMAGE BASED QUESTION - PENDING CROP]"
        
    q_text_en_safe = q_text_en if q_text_en else ""
    q_type = 'image_only' if ("[IMAGE BASED QUESTION" in q_text_en_safe or not any(opts_data)) else 'text'
    
    # 1. Insert Question
    cur.execute("""
        INSERT INTO questions 
        (exam_id, section_id, topic_id, question_no, question_type, text_en, text_mr, correct_option, marks, difficulty)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (exam_id, section_id, topic_id, q_no, q_type, q_text_en, q_text_mr, correct_option_idx, 2, 'medium'))
    q_db_id = cur.fetchone()[0]
    
    # 2. Insert Options
    # If no options, it might be entirely image-options too. We insert 4 options anyway.
    for i in range(4):
        txt_en = opts_data[i] if len(opts_data) > i else ""
        txt_mr = None
        if q_text_mr: # from marathi json
            txt_en = None
            txt_mr = opts_data[i] if len(opts_data) > i else ""
            
        cur.execute("""
            INSERT INTO options
            (question_id, option_no, text_en, text_mr, is_correct)
            VALUES (%s, %s, %s, %s, %s)
        """, (q_db_id, i+1, txt_en, txt_mr, (i+1) == correct_option_idx))

if __name__ == "__main__":
    try:
        print("Extracting Paper 1...")
        p1 = extract_pdf_questions('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/5th/English_Paper1.pdf', 1, 75, 1)
        
        print("Extracting Paper 2 (Intelligence)...")
        p2_intel = extract_pdf_questions('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/5th/English_Paper2.pdf', 26, 75, 5)
        
        # INSERT EXAM 1
        print("Inserting Paper 1 questions...")
        for i in range(1, 76):
            if i in p1:
                q_text = p1[i]['text']
                opts = p1[i]['options']
            else:
                q_text = ""
                opts = ["", "", "", ""]
                
            correct = answers["501"][i-1]
            if i <= 25:
                insert_question(1, 1, 1, i, q_text, None, opts, correct)
            else:
                insert_question(1, 2, 7, i, q_text, None, opts, correct)
                
        # INSERT EXAM 2
        print("Inserting Paper 2 questions...")
        for i in range(1, 76):
            correct = answers["502"][i-1]
            if i <= 25:
                # Marathi
                q_dict = marathi_qs[i-1]
                ctx = q_dict.get('context_mr', "")
                full_text = ctx + "\n\n" + q_dict['text_mr'] if ctx else q_dict['text_mr']
                opts = q_dict['options']
                insert_question(2, 3, 18, i, None, full_text.strip(), opts, correct)
            else:
                if i in p2_intel:
                    q_text = p2_intel[i]['text']
                    opts = p2_intel[i]['options']
                else:
                    q_text = ""
                    opts = ["", "", "", ""]
                insert_question(2, 4, 23, i, q_text, None, opts, correct)
                
        conn.commit()
        print("Successfully imported all 150 questions!")
    except Exception as e:
        conn.rollback()
        print(f"Error during import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
