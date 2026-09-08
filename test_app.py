import requests
import json

BASE = "http://localhost:8000"

# Test health
print("Test health:")
r = requests.get(f"{BASE}/api/health")
print(f"  Status: {r.json()}")

# Register a test user
print("\nRegister test user:")
reg = requests.post(f"{BASE}/api/auth/register", json={
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "password123",
    "role": "patient"
})
print(f"  Register Status: {reg.status_code}")

# Login
print("\nLogin:")
login = requests.post(f"{BASE}/api/auth/login", json={
    "email": "test@example.com",
    "password": "password123"
})
token = login.json()["access_token"]
print(f"  Token: {token[:20]}...")

# Test diseases with auth
print("\nTest diseases (authenticated):")
r = requests.get(f"{BASE}/api/diseases", headers={"Authorization": f"Bearer {token}"})
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    print(f"  Diseases: {r.json()}")

# Test predictions (image - pneumonia demo)
print("\nTest image prediction (pneumonia demo):")
files = {"file": ("test.png", b"\\x89PNG\\r\\n\\x1a\\n", "image/png")}
data = {"disease": "pneumonia"}
r = requests.post(f"{BASE}/api/predictions/image", files=files, data=data, headers={"Authorization": f"Bearer {token}"})
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    print(f"  Response: {r.json()}")
else:
    print(f"  Error: {r.text}")

# Test predictions (tabular - diabetes demo)
print("\nTest tabular prediction (diabetes demo):")
payload = {
    "disease": "diabetes",
    "features": {
        "pregnancies": 1,
        "glucose": 100,
        "blood_pressure": 70,
        "skin_thickness": 20,
        "insulin": 80,
        "bmi": 25,
        "diabetes_pedigree": 0.3,
        "age": 30,
    },
}
r = requests.post(f"{BASE}/api/predictions/tabular", json=payload, headers={"Authorization": f"Bearer {token}"})
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    print(f"  Response: {r.json()}")
else:
    print(f"  Error: {r.text}")