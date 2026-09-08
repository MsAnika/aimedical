import requests

BASE = 'http://localhost:8000'

# Login
login = requests.post(f'{BASE}/api/auth/login', json={
    'email': 'test2@example.com',
    'password': 'password123'
})
token = login.json()['access_token']
user_info = login.json()
print(f'User ID from login: {user_info.get("id")}')
print(f'User role: {user_info.get("role")}')

# Create a new prediction
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
print(f'Prediction ID: {pred["id"]}')
print(f'Prediction user_id: {pred["user_id"]}')

# Check ownership
r2 = requests.get(f'{BASE}/api/predictions/{pred["id"]}', headers={'Authorization': f'Bearer {token}'})
p2 = r2.json()
print(f'Prediction from GET user_id: {p2["user_id"]}')