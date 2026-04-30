import fitz
import os

os.makedirs('rendered/2018', exist_ok=True)

# Render Marathi Paper 2 (Pages 1 to 5)  (sometimes Marathi text goes to page 5)
print("Rendering 2018 Marathi Paper 2 pages...")
doc_p2 = fitz.open('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2018/5th/English_Paper2.pdf')
mat = fitz.Matrix(2, 2)

for i in range(1, 6): # Usually index 1 to 4/5
    try:
        pix = doc_p2[i].get_pixmap(matrix=mat)
        pix.save(f'rendered/2018/marathi_p{i}.png')
        print(f"Saved rendered/2018/marathi_p{i}.png")
    except Exception as e:
        print(f"Skipping page {i}: {e}")
doc_p2.close()

# Render Answer Keys
print("Rendering 2018 Answer Keys...")
ans_p1 = fitz.open('/Users/preetam/Desktop/Exam_Papers/Answer_Sheets/Feb_2018/5th/English_Paper1.pdf')
ans_p1[0].get_pixmap(matrix=mat).save('rendered/2018/ans_p1.png')

ans_p2 = fitz.open('/Users/preetam/Desktop/Exam_Papers/Answer_Sheets/Feb_2018/5th/English_Paper2.pdf')
ans_p2[0].get_pixmap(matrix=mat).save('rendered/2018/ans_p2.png')

print("All 2018 renders complete.")
