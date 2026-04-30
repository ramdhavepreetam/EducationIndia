import pdfplumber
import re

def extract_qs(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        # The english intelligence section is from page 5 onwards (index 5)
        for page in pdf.pages[5:]:
            page_text = page.extract_text()
            # clean footer
            page_text = re.sub(r'SPACE FOR ROUGH WORK.*', '', page_text, flags=re.DOTALL)
            full_text += page_text + "\n"
            
    q_matches = re.split(r'\n(2[6-9]|[3-6][0-9]|7[0-5])\.\s', full_text)
    
    print("Found chunks:", len(q_matches))
    for i in range(1, len(q_matches), 2):
        q_no = int(q_matches[i])
        q_text = q_matches[i+1].strip()
        print(f"--- Q {q_no} ---")
        print(q_text[:150])

extract_qs('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/5th/English_Paper2.pdf')
