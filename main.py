import requests
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # URL se parameters nikalna (uid aur region)
        query = parse_qs(urlparse(self.path).query)
        uid = query.get('uid', [None])[0]
        # Agar region nahi diya to default 'ind' (India) rakhega
        region = query.get('region', ['ind'])[0]

        if not uid:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "UID missing! Please use ?uid=NUMBER&region=ind"}).encode())
            return

        # Aapka bataya hua API Endpoint
        target_url = f"https://info-ob49.vercel.app/api/account/?uid={uid}&region={region}"

        try:
            # External API se data fetch karna
            response = requests.get(target_url, timeout=10)
            data = response.json()

            # Browser ko response bhejna
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*') # Sab jagah chalega
            self.end_headers()

            # Jo bhi data milega wahi aapki site par dikhega
            self.wfile.write(json.dumps(data).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())