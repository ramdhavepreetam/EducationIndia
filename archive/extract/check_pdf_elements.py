import fitz

def check_pdf(path):
    print(f"Checking {path}")
    doc = fitz.open(path)
    page = doc[0]
    
    print("Number of images:", len(page.get_images()))
    text = page.get_text("text")
    print("Text length:", len(text))
    print("Drawings (lines/curves):", len(page.get_drawings()))

check_pdf("/Users/preetam/Desktop/Exam_Papers/Answer_Sheets/Feb_2025/5th/English_Paper1.pdf")
