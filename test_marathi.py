import fitz

def check_pdf(path):
    print(f"Checking {path}")
    doc = fitz.open(path)
    page = doc[0]
        
    print("Number of images:", len(page.get_images()))
    text = page.get_text("text")
    print("Text length:", len(text))
    print("Drawings (lines/curves):", len(page.get_drawings()))
    print("Sample text:", repr(text[:100]))

check_pdf("/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/5th/Marathi_Paper2.pdf")
