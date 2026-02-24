#!/usr/bin/env python3
"""
Day 7 Verification Script
Runs all 5 verification steps against the running ScholarPath API.
"""

import hmac
import hashlib
import base64
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import sys

BASE = "http://localhost:8000"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhtem5rcW9qY3hxb3J3ZmN1aXZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzODgyMjcsImV4cCI6MjA4Njk2NDIyN30.pCtM99XKmqloFMjK8P02SrbJ92OawnUZ1-Lzjy5cheA"
JWT_SECRET_B64 = "DQhgcdkU2O4bqIos1iwUEDlRySopo+rX6l9l2mi9Nvxc4O0HGmPw1ZiYkj1mHJaAbCqUUu/jCBpFNwdHxGqDLA=="
STUDENT_UUID = "ac2132de-cb08-4655-92e6-7645e70c20c4"

# ── Generate HS256 JWT ────────────────────────────────────────────────────────
def b64url_encode(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def make_token(sub, email, role="student"):
    """Generate an HS256 JWT using python-jose (same library the server uses)."""
    from jose import jwt as josejwt
    now = int(time.time())
    payload = {
        "iss": "supabase",
        "ref": "hmznkqojcxqorwfcuivl",
        "sub": sub,
        "aud": "authenticated",
        "role": "authenticated",
        "email": email,
        "user_metadata": {"role": role},   # verify_token reads user_metadata.role
        "app_metadata": {"provider": "email"},
        "iat": now,
        "exp": now + 7200,
    }
    return josejwt.encode(payload, JWT_SECRET_B64, algorithm="HS256")

# ── HTTP helpers ──────────────────────────────────────────────────────────────
def api(method, path, token=None, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            body = {"error": str(e)}
        return e.code, body

def sep(title):
    print(f"\n{'━'*60}")
    print(f"  {title}")
    print('━'*60)

def ok(label, val):
    print(f"  ✅ {label}: {val}")

def fail(label, val):
    print(f"  ❌ {label}: {val}")
    sys.exit(1)

# ── Main verification ─────────────────────────────────────────────────────────
print("\n🎓 ScholarPath — Day 7 Live Verification")
print(f"   Base URL : {BASE}")
print(f"   Student  : {STUDENT_UUID}")

# 0. Health
sep("0. Health check")
status, data = api("GET", "/health")
assert status == 200 and data.get("status") == "ok", f"Health failed: {data}"
ok("status", data)

# Generate student token
TOKEN = make_token(STUDENT_UUID, "ramdhavepreetam@gmail.com")
print(f"\n  🔑 Token generated (HS256, exp +2h)")
print(f"  Token prefix: {TOKEN[:40]}...")

# 1. Start exam
sep("1. POST /api/attempts/start  — start exam_id=1")
status, data = api("POST", "/api/attempts/start", TOKEN, {"exam_id": 1})
print(f"  HTTP {status}")
print(f"  Response: {json.dumps(data, indent=2)[:600]}")
if status == 201:
    ATTEMPT_ID = data["attempt_id"]
    ok("attempt_id", ATTEMPT_ID)
    ok("status", data.get("status"))
    ok("time_remaining_seconds", data.get("time_remaining_seconds"))
elif status == 409:
    # Already has an ongoing attempt — try to get its ID from the error
    print("  ⚠️  409 Conflict — student already has an ongoing attempt")
    # fetch the attempt list instead
    s2, d2 = api("GET", "/api/attempts/?exam_id=1", TOKEN)
    print(f"  Listing attempts: HTTP {s2}: {json.dumps(d2)[:300]}")
    if s2 == 200 and d2:
        ATTEMPT_ID = d2[0]["attempt_id"]
        ok("Reusing existing attempt_id", ATTEMPT_ID)
    else:
        fail("Could not get attempt_id", d2)
else:
    fail("start exam", data)

# 2. Save response
sep("2. POST /api/attempts/{attempt_id}/responses  — save Q1=option2")
status, data = api(
    "POST", f"/api/attempts/{ATTEMPT_ID}/responses", TOKEN,
    {"question_id": 1, "question_no": 1, "selected_option": 2, "time_taken_seconds": 45}
)
print(f"  HTTP {status}")
print(f"  Response: {json.dumps(data, indent=2)[:400]}")
if status == 200:
    ok("selected_option", data.get("selected_option"))
    ok("visit_count", data.get("visit_count"))
else:
    fail("save response", data)

# 3. Restore state
sep("3. GET /api/attempts/{attempt_id}/state  — restore after page refresh")
status, data = api("GET", f"/api/attempts/{ATTEMPT_ID}/state", TOKEN)
print(f"  HTTP {status}")
print(f"  Response: {json.dumps(data, indent=2)[:600]}")
if status == 200:
    responses = data.get("responses", [])
    ok("responses count", len(responses))
    q1 = next((r for r in responses if r.get("question_id") == 1), None)
    if q1:
        ok("Q1 selected_option persisted", q1.get("selected_option"))
    ok("time_remaining_seconds", data.get("time_remaining_seconds"))
else:
    fail("get state", data)

# 4. Submit
sep("4. POST /api/attempts/{attempt_id}/submit  — submit exam")
status, data = api("POST", f"/api/attempts/{ATTEMPT_ID}/submit", TOKEN)
print(f"  HTTP {status}")
print(f"  Response: {json.dumps(data, indent=2)[:600]}")
if status == 200:
    ok("status", data.get("status"))
    ok("total_score", data.get("total_score"))
    ok("percentage", data.get("percentage"))
    ok("grade", data.get("grade"))
    if "correct_option" in data:
        fail("SECURITY BREACH — correct_option exposed!", data.get("correct_option"))
    else:
        ok("correct_option NOT in response (security ✅)", "OK")
else:
    fail("submit exam", data)

# 5. Try starting same exam again → 201 (new attempt)
sep("5. POST /api/attempts/start again  — must return 201 Created (Attempt #2)")
status, data = api("POST", "/api/attempts/start", TOKEN, {"exam_id": 1})
print(f"  HTTP {status}")
print(f"  Response: {json.dumps(data)[:300]}")
if status == 201:
    ok("attempt_number", data.get("attempt_number"))
    ok("201 Created returned (successfully started new attempt)", "✅")
else:
    fail("expected 201, got", status)

print(f"\n{'━'*60}")
print("  🎉 ALL VERIFICATION STEPS PASSED")
print(f"{'━'*60}\n")
