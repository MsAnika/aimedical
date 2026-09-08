import requests
import json

BASE = 'http://127.0.0.1:8000'

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

# Check the prediction
r2 = requests.get(f'{BASE}/api/predictions/{pid}', headers={'Authorization': f'Bearer {token}'})
p = r2.json()
print(f'Prediction user_id from API: {p.get("user_id")}')
print(f'Prediction disease: {p.get("disease")}')
print(f'Full prediction: {json.dumps(p, indent=2)}')