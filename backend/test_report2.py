import requests

BASE = 'http://localhost:8000'

# Login
login = requests.post(f'{BASE}/api/auth/login', json={
    'email': 'test2@example.com',
    'password': 'password123'
})
token = login.json()['access_token']

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
pred_id = r.json()['id']
print(f'Prediction ID: {pred_id}')

# Check prediction details
r2 = requests.get(f'{BASE}/api/predictions/{pred_id}', headers={'Authorization': f'Bearer {token}'})
p = r2.json()
print(f'Prediction heatmap_path: {p.get("heatmap_url")}')
print(f'Prediction input_image_url: {p.get("input_image_url")}')

# Try to create report
r3 = requests.post(f'{BASE}/api/reports/{pred_id}/report', headers={'Authorization': f'Bearer {token}'})
print(f'Report Status: {r3.status_code}')
print(f'Report Response: {r3.text}')

# Try downloading
if r3.status_code == 200:
    dl = r3.json()
    dl_url = dl.get('download_url', 'none')
    print(f'Download URL: {dl_url}')