import requests

url = 'http://localhost:5000/input'
files = {'file': ('demo.pdf', open('./tests/handbuch.pdf', 'r'),
                  'application/pdf', {'Expires': '0'})}

r = requests.post(url, files=files)
print r.text
