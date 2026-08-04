import fitz
import os

os.makedirs('rendered', exist_ok=True)
mat = fitz.Matrix(2, 2)

# Answer keys
doc1 = fitz.open('/Users/preetam/Desktop/Exam_Papers/Answer_Sheets/Feb_2025/5th/English_Paper1.pdf')
doc1[0].get_pixmap(matrix=mat).save('rendered/ans_p501.png')

doc2 = fitz.open('/Users/preetam/Desktop/Exam_Papers/Answer_Sheets/Feb_2025/5th/English_Paper2.pdf')
doc2[0].get_pixmap(matrix=mat).save('rendered/ans_p502.png')

# Marathi section from English Paper 2 (Pages 1 to 5, which are index 0 to 4... wait, page 0 is cover or instructions?)
p502 = fitz.open('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/5th/English_Paper2.pdf')
for i in range(1, 6):
    p502[i].get_pixmap(matrix=mat).save(f'rendered/marathi_{i}.png')

print("Rendered successfully.")
