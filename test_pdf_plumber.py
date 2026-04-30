import pdfplumber
import sys

def extract_answer_key(path):
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        print("--- TEXT ---")
        print(text)
        print("--- TABLES ---")
        tables = page.extract_tables()
        for i, table in enumerate(tables):
            print(f"Table {i+1}:")
            for row in table:
                print(row)

extract_answer_key("/Users/preetam/Desktop/Exam_Papers/Answer_Sheets/Feb_2025/5th/English_Paper1.pdf")
