import pdfplumber

def extract_qs(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Page 2 usually contains the first questions
        print(pdf.pages[2].extract_text())

extract_qs('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/5th/English_Paper1.pdf')
