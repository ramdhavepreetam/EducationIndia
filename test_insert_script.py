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

if __name__ == "__main__":
    print("Testing extraction on English Paper 1 (Questions 1-5)")
    qs = extract_pdf_questions('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/5th/English_Paper1.pdf', 1, 5, 1)
    for q_no, data in qs.items():
        print(f"Q{q_no}: {data['text']}")
        print(f"Options: {data['options']}")
