import os
import json
import urllib.request
import urllib.error
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

app_url = "https://scholarpath-backend-470258820905.us-central1.run.app"
url = ""
key = ""

with open(".env") as f:
    for line in f:
        line = line.strip()
        if line.startswith("SUPABASE_URL="):
            url = line.split("=", 1)[1].strip()
        elif line.startswith("SUPABASE_ANON_KEY="):
            key = line.split("=", 1)[1].strip()

# 1. Login to get JWT
data = json.dumps({"email": "admin@scholarpath.com", "password": "Password123!"}).encode('utf-8')
req = urllib.request.Request(f"{url}/auth/v1/token?grant_type=password", data=data, headers={"apikey": key, "Content-type": "application/json"}, method="POST")

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        res_data = json.loads(response.read().decode())
        token = res_data["access_token"]
except urllib.error.HTTPError as e:
    print("Login failed:", e.read().decode())
    exit(1)

headers = {"Authorization": f"Bearer {token}", "Content-type": "application/json"}

# 2. Get Exams and Sections
req = urllib.request.Request(f"{app_url}/api/admin/catalog/exams", headers=headers)
with urllib.request.urlopen(req, context=ctx) as response:
    exams = json.loads(response.read().decode())

for exam in exams:
    exam_id = exam["id"]
    print(f"Processing Exam {exam_id}: {exam['title_en']}")
    
    # Publish exam first so we can fetch its details (which requires is_active=True)
    pub_req = urllib.request.Request(f"{app_url}/api/admin/catalog/exams/{exam_id}/publish", data=json.dumps({}).encode('utf-8'), headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(pub_req, context=ctx) as response:
            print(f"Published Exam {exam_id}")
    except urllib.error.HTTPError as e:
        print("Publish failed:", e.read().decode())
        continue

    # Get details
    req = urllib.request.Request(f"{app_url}/api/catalog/exams/{exam_id}", headers=headers)
    with urllib.request.urlopen(req, context=ctx) as response:
        detail = json.loads(response.read().decode())
    
    questions = []
    q_no = 1
    
    for section in detail["sections"]:
        section_id = section["id"]
        for topic in section["topics"]:
            topic_id = topic["id"]
            
            # Generate 2 questions per topic
            for i in range(2):
                if q_no > exam["total_questions"]:
                    break
                    
                questions.append({
                    "section_id": section_id,
                    "topic_id": topic_id,
                    "question_no": q_no,
                    "question_type": "text",
                    "text_en": f"Sample question {q_no} for topic {topic['name_en']}",
                    "correct_option": 1,
                    "explanation_en": f"Explanation for question {q_no}",
                    "marks": 2,
                    "difficulty": "medium",
                    "options": [
                        {"option_no": 1, "text_en": "Correct option"},
                        {"option_no": 2, "text_en": "Wrong option"},
                        {"option_no": 3, "text_en": "Wrong option"},
                        {"option_no": 4, "text_en": "Wrong option"}
                    ]
                })
                q_no += 1

    payload = json.dumps({
        "exam_id": exam_id,
        "contexts": [],
        "questions": questions
    }).encode('utf-8')
    
    print(f"Importing {len(questions)} questions for exam {exam_id}")
    import_req = urllib.request.Request(f"{app_url}/api/admin/questions/bulk-import", data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(import_req, context=ctx) as response:
            print("Import success:", json.loads(response.read().decode()))
    except urllib.error.HTTPError as e:
        print("Import failed:", e.read().decode())
        continue
        

    print("-" * 20)
