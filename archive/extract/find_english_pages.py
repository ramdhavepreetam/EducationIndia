import pdfplumber

def find_pages(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and ("Which" in text or "Solve" in text or "Choose" in text or "alternative" in text):
                print(f"Page {i}: English detected")
            else:
                print(f"Page {i}: Marathi or other")

if __name__ == "__main__":
    print("Paper 1:")
    find_pages('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/8th/Marathi_Paper1.pdf')
    print("\nPaper 2:")
    find_pages('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/8th/Marathi_Paper2.pdf')
