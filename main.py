import requests
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # UID nikalne ke liye URL parse karna
        query = parse_qs(urlparse(self.path).query)
        uid = query.get('uid', [None])[0]

        if not uid:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "UID missing! Please add ?uid=NUMBER to URL"}).encode())
            return

        # Garena API settings
        url = "https://shop2game.com/api/auth/player_id_login"
        payload = {
            "app_id": 100067,
            "login_id": uid
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*') # Sab ke liye open
            self.end_headers()

            if "nickname" in data:
                result = {"success": True, "nickname": data["nickname"]}
            else:
                result = {"success": False, "message": "Player not found"}
            
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())