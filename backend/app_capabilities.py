import requests
import json

BASE = 'http://127.0.0.1:8000'

print("=" * 60)
print("AI MEDICAL DIAGNOSTIC SYSTEM - CAPABILITIES TEST")
print("=" * 60)

# 1. Health check
print("\n1. Health Check:")
r = requests.get(f'{BASE}/api/health')
print(f"   Status: {r.status_code} - {r.json()}")

# 2. Diseases list
print("\n2. Available Disease Modules:")
r = requests.get(f'{BASE}/api/diseases')
if r.status_code == 200:
    diseases = r.json()
    for d in diseases:
        print(f"   - {d['name']} (Type: {d['type']}, Classes: {d['classes']}, Model Status: {d['model_status']})")
else:
    print(f"   Status: {r.status_code}")

# 3. Login
print("\n3. Authentication:")
r = requests.post(f'{BASE}/api/auth/login', json={'email': 'test2@example.com', 'password': 'password123'})
token = r.json()['access_token']
print(f"   Login successful, token received")

# 4. Tabular prediction (diabetes)
print("\n4. Tabular Prediction (Diabetes Risk):")
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
    }
}
r = requests.post(f'{BASE}/api/predictions/tabular', json=payload, headers={'Authorization': f'Bearer {token}'})
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    p = r.json()
    print(f"   Label: {p['label']}")
    print(f"   Confidence: {p['confidence']}")
    print(f"   Probabilities: {p['probabilities']}")
    print(f"   Is Demo Mode: {p['is_demo']}")
    print(f"   Explanation Type: {p['explanation']['type']}")
    print(f"   SHAP Values Available: {len(p['explanation'].get('shap_values', [])) > 0}")
    print(f"   Model Version: {p['model_version']}")

# 5. Image prediction (pneumonia)
print("\n5. Image Prediction (Pneumonia from Chest X-Ray):")
from PIL import Image
import io
img = Image.new('RGB', (100, 100), 'red')
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
files = {'file': ('test.png', img_bytes.getvalue(), 'image/png')}
r = requests.post(f'{BASE}/api/predictions/image', files=files, data={'disease': 'pneumonia'}, headers={'Authorization': f'Bearer {token}'})
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    p = r.json()
    print(f"   Label: {p['label']}")
    print(f"   Confidence: {p['confidence']}")
    print(f"   Probabilities: {p['probabilities']}")
    print(f"   Is Demo Mode: {p['is_demo']}")
    print(f"   Explanation Type: {p['explanation']['type']}")
    print(f"   Heatmap URL: {p.get('heatmap_url')}")
    print(f"   Model Version: {p['model_version']}")

# 6. Report generation
if r.status_code == 200:
    pid = r.json()['id']
    print(f"\n6. PDF Report Generation:")
    r2 = requests.post(f'{BASE}/api/reports/{pid}/report', headers={'Authorization': f'Bearer {token}'})
    print(f"   Report Status: {r2.status_code}")
    if r2.status_code == 200:
        dl = r2.json()
        print(f"   Report Generated: Yes")
        print(f"   Download URL: {dl.get('download_url', 'none')}")
        print(f"   Report ID: {dl.get('report_id')}")
    else:
        print(f"   Report Error: {r2.text}")

# 7. Report download
if r2.status_code == 200:
    dl_url = r2.json().get('download_url', '')
    print(f"\n7. Report Download:")
    if dl_url != 'none':
        r3 = requests.get(dl_url, headers={'Authorization': f'Bearer {token}'})
        print(f"   Download Status: {r3.status_code}")
        print(f"   Download Size: {len(r3.content)} bytes")
        print(f"   Filename: {r3.headers.get('Content-Disposition', 'unknown')}")

# 8. Patient history
print("\n8. Patient History:")
r = requests.get(f'{BASE}/api/history', headers={'Authorization': f'Bearer {token}'})
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    h = r.json()
    print(f"   Total Predictions: {h['total']}")
    for item in h['items'][:3]:
        print(f"   - {item['disease']}: {item['label']} (Confidence: {item['confidence']})")

# 9. Specific disease details
print("\n9. Disease Module Details:")
for disease in ['pneumonia', 'skin', 'diabetes', 'heart']:
    r = requests.get(f'{BASE}/api/diseases', headers={'Authorization': f'Bearer {token}'})
    if r.status_code == 200:
        diseases = r.json()
        d = next((x for x in diseases if x['id'] == disease), None)
        if d:
            print(f"   {d['name']}:")
            print(f"     Type: {d['type']}")
            print(f"     Classes: {d['classes']}")
            print(f"     Fields count: {len(d.get('fields', []))}")
            print(f"     Model Status: {d['model_status']}")
            print(f"     Model Version: {d['model_version']}")

print("\n" + "=" * 60)
print("CAPABILITIES SUMMARY COMPLETE")
print("=" * 60)