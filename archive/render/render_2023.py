import fitz
import os

os.makedirs('rendered/2023', exist_ok=True)

# Render Marathi Paper 2 (Pages 1 to 4)
print("Rendering 2023 Marathi Paper 2 pages...")
doc_p2 = fitz.open('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2023/5th/English_Paper2.pdf')
mat = fitz.Matrix(2, 2)

for i in range(1, 5):
    pix = doc_p2[i].get_pixmap(matrix=mat)
    pix.save(f'rendered/2023/marathi_p{i}.png')
    print(f"Saved rendered/2023/marathi_p{i}.png")
doc_p2.close()

# Render Answer Keys
print("Rendering 2023 Answer Keys...")
ans_p1 = fitz.open('/Users/preetam/Desktop/Exam_Papers/Answer_Sheets/Feb_2023/5th/English_Paper1.pdf')
ans_p1[0].get_pixmap(matrix=mat).save('rendered/2023/ans_p1.png')
ans_p1.close()

ans_p2 = fitz.open('/Users/preetam/Desktop/Exam_Papers/Answer_Sheets/Feb_2023/5th/English_Paper2.pdf')
ans_p2[0].get_pixmap(matrix=mat).save('rendered/2023/ans_p2.png')
ans_p2.close()

print("All 2023 renders complete.")
