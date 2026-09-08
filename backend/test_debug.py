import requests
import json

BASE = 'http://localhost:8000'

# Login
login = requests.post(f'{BASE}/api/auth/login', json={
    'email': 'test2@example.com',
    'password': 'password123'
})
token = login.json()['access_token']

# Create prediction
payload = {
    'disease': 'diabetes',
    'features': {
        'pregnancies': 1,
        'glucose': 100,
        'blood_pressure': 70,
        'skin_thickness': 20,
        'insulin': 80,
        'bmi': 25,
        'diabetes_pedigree': 0.3,
        'age': 30,
    },
}
r = requests.post(f'{BASE}/api/predictions/tabular', json=payload, headers={'Authorization': f'Bearer {token}'})
pred = r.json()
pid = pred['id']
print(f'Created prediction ID: {pid}')

# Immediately check it
r2 = requests.get(f'{BASE}/api/predictions/{pid}', headers={'Authorization': f'Bearer {token}'})
print(f'Check prediction: status={r2.status_code}')
if r2.status_code == 200:
    p = r2.json()
    print(f'  user_id={p.get("user_id")}, disease={p.get("disease")}')

# Now try report
r3 = requests.post(f'{BASE}/api/reports/{pid}/report', headers={'Authorization': f'Bearer {token}'})
print(f'Create report: status={r3.status_code}')
print(f'Create report: body={r3.text}')