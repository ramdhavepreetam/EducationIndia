import os
from supabase import create_client, Client

url = ""
key = ""

with open(".env") as f:
    for line in f:
        if line.startswith("SUPABASE_URL="):
            url = line.split("=", 1)[1].strip()
        elif line.startswith("SUPABASE_SERVICE_KEY="):
            key = line.split("=", 1)[1].strip()

supabase: Client = create_client(url, key)

try:
    res = supabase.auth.admin.create_user({
        "email": "admin@scholarpath.com",
        "password": "Password123!",
        "email_confirm": True,
        "user_metadata": {
            "full_name": "System Admin",
            "role": "exam_admin"
        }
    })
    print("Created user:", res.user.email)
except Exception as e:
    print("Error creating user:", e)
