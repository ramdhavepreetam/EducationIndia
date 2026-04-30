import pdfplumber
import re

def extract_qs(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        # Skip cover page
        for page in pdf.pages[1:]:
            full_text += page.extract_text() + "\n"
            
    # Regular expression to match questions: starts with 2 digits and a dot, followed by text and then options.
    # Note: Sometimes instructions appear. Let's just find "01. " or "1. " to "75. "
    q_matches = re.split(r'\n(0?[1-9]|[1-6][0-9]|7[0-5])\.\s', full_text)
    
    # regex split will give [pretext, '01', text_for_1, '02', text_for_2, ...]
    print("Found chunks:", len(q_matches))
    for i in range(1, len(q_matches), 2):
        q_no = int(q_matches[i])
        q_text = q_matches[i+1].strip()
        print(f"--- Q {q_no} ---")
        print(q_text[:200]) # only print first 200 chars

extract_qs('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/5th/English_Paper1.pdf')
