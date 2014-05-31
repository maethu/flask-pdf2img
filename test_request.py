import requests

url = 'http://localhost:5000/input'
files = {'file': ('demo.pdf', open('./tests/handbuch.pdf', 'r'),
                  'application/pdf', {'Expires': '0'})}

payload = {'apikey': '12345'}

r = requests.post(url, data=payload, files=files)
print r.text
