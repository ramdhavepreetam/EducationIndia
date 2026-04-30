import fitz

def render_marathi():
    doc = fitz.open('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/5th/Marathi_Paper2.pdf')
    mat = fitz.Matrix(2, 2)  # 2x zoom
    pix = doc[1].get_pixmap(matrix=mat)
    pix.save('marathi_page.png')
    print("Saved to marathi_page.png")

render_marathi()
