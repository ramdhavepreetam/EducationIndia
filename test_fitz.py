import fitz

def extract_fitz(path):
    print(f"Testing {path}")
    doc = fitz.open(path)
    page = doc[0]
    print(page.get_text()[:500])

extract_fitz("/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/5th/English_Paper1.pdf")
