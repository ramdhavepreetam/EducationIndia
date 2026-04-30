import pdfplumber
import re
import json

def extract_questions(pdf_path, start_q, end_q, english_pages):
    questions = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_no in english_pages:
            page = pdf.pages[page_no]
            text = page.extract_text()
            if not text: continue
            
            # Find Q. No. patterns like "26. text" or "Q. 26 text"
            # This is a simple split-based approach since 8th std layout is relatively clean
            lines = text.split('\n')
            current_q = None
            
            for line in lines:
                # Match question number at start of line
                match = re.match(r'^(\d{1,2})\.\s+(.*)', line)
                if match:
                    q_no = int(match.group(1))
                    if start_q <= q_no <= end_q:
                        if current_q: questions.append(current_q)
                        current_q = {
                            "q": q_no,
                            "text_en": match.group(2),
                            "opts_en": [],
                            "correct_option": None,
                            "correct_options": None
                        }
                        continue
                
                # Match options line like "(1) opt1 (2) opt2"
                if current_q:
                    opt_match = re.findall(r'\((\d)\)\s+([^\(]+)', line)
                    if opt_match:
                        for o_no, o_text in opt_match:
                            current_q["opts_en"].append(o_text.strip())
                    elif not line.startswith('(') and not line.startswith('SPACE'):
                        # Append to question text if it's not a number or space for rough work
                        if not re.match(r'^\d{4}-', line): # Page footer
                            current_q["text_en"] += " " + line.strip()
            
            if current_q: questions.append(current_q)

    # De-duplicate and sort
    seen = set()
    final_qs = []
    for q in sorted(questions, key=lambda x: x["q"]):
        if q["q"] not in seen:
            final_qs.append(q)
            seen.add(q["q"])
            
    return final_qs

if __name__ == "__main__":
    # Paper 1 Math (Q26-75)
    # English pages detected: 11, 13, 15, 17, 19, 27... wait I need a more complete list
    # I'll just check all odd pages from 7 to 31
    p1_pages = [i for i in range(7, 32) if i % 2 != 0]
    math_qs = extract_questions('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/8th/Marathi_Paper1.pdf', 26, 75, p1_pages)
    
    with open('/Users/preetam/Documents/AI/scholarpath/8th_2025_p1_math_extracted.json', 'w') as f:
        json.dump(math_qs, f, indent=2)
    
    # Paper 2 Intelligence (Q26-75)
    # English pages for Section II usually start after Section I English (Page 7)
    p2_pages = [i for i in range(9, 32) if i % 2 != 0]
    intel_qs = extract_questions('/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/8th/Marathi_Paper2.pdf', 26, 75, p2_pages)
    
    with open('/Users/preetam/Documents/AI/scholarpath/8th_2025_p2_intel_extracted.json', 'w') as f:
        json.dump(intel_qs, f, indent=2)

    print(f"Extracted {len(math_qs)} Math questions and {len(intel_qs)} Intelligence questions.")
