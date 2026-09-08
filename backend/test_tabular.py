import requests

BASE = 'http://localhost:8000'

# Login
login = requests.post(f'{BASE}/api/auth/login', json={
    'email': 'test2@example.com',
    'password': 'password123'
})
token = login.json()['access_token']

# Test tabular prediction
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
print(f'Predict Status: {r.status_code}')
print(f'Predict Response: {r.text}')

if r.status_code == 200:
    pred_id = r.json()['id']
    print(f'Prediction ID: {pred_id}')
    
    # Create report
    r2 = requests.post(f'{BASE}/api/reports/{pred_id}/report', headers={'Authorization': f'Bearer {token}'})
    print(f'Report Status: {r2.status_code}')
    print(f'Report Response: {r2.text}')
    
    # The download URL
    if r2.status_code == 200:
        dl = r2.json()
        dl_url = dl.get('download_url', 'none')
        print(f'Download URL: {dl_url}')