import requests
import io
from PIL import Image

BASE = 'http://localhost:8000'

# Login
login = requests.post(f'{BASE}/api/auth/login', json={
    'email': 'test2@example.com',
    'password': 'password123'
})
token = login.json()['access_token']

# Create test image
img = Image.new('RGB', (100, 100), color='red')
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)

# Test image prediction
files = {'file': ('test.png', img_bytes.getvalue(), 'image/png')}
data = {'disease': 'pneumonia'}
r = requests.post(f'{BASE}/api/predictions/image', files=files, data=data, headers={'Authorization': f'Bearer {token}'})
print(f'Predict Status: {r.status_code}')
print(f'Predict Response: {r.text}')

if r.status_code == 200:
    pred_id = r.json()['id']
    print(f'Prediction ID: {pred_id}')
    
    # Create report
    r2 = requests.post(f'{BASE}/api/reports/{pred_id}/report', headers={'Authorization': f'Bearer {token}'})
    print(f'Report Status: {r2.status_code}')
    print(f'Report Response: {r2.text}')
    
    # Download report
    if r2.status_code == 200:
        download_data = r2.json()
        dl_url = download_data.get('download_url', 'none')
        print(f'Download URL: {dl_url}')