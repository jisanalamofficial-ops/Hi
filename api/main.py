import requests
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        # Params Catch Karna
        access_token = query.get('access_token', [None])[0]
        email = query.get('email', [None])[0]
        otp = query.get('otp', [None])[0]
        
        # BD Server Details
        region = "BD"
        app_id = 100067 # Free Fire Official App ID

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # REAL GARENA HEADERS (Jo Game use karta hai)
        headers = {
            "Content-Type": "application/json",
            "X-Garena-Region": region,
            "User-Agent": "GarenaFreeFire/1.103.1 (Android; MSDK-Bind)",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }

        # --- STEP 1: REAL SEND OTP ---
        if "/api/send-otp" in path:
            if not access_token or not email:
                self.wfile.write(json.dumps({"success": False, "message": "Missing Token/Email"}).encode())
                return

            # Real Garena MSDK Binding OTP Endpoint
            otp_url = "https://account.garena.com/api/v1/bind/send_otp"
            
            payload = {
                "access_token": access_token,
                "email": email,
                "app_id": app_id,
                "region": region,
                "security_code": "123456" # Fixed Security Code
            }

            try:
                # Direct Request to Garena
                response = requests.post(otp_url, json=payload, headers=headers, timeout=15)
                garena_res = response.json()

                # REAL VALIDATION: Agar Garena ne 0 (Success) diya tabhi success dikhayega
                if garena_res.get("error") == 0 or garena_res.get("status") == "success":
                    res = {"success": True, "message": f"Real OTP Sent to {email}", "garena_data": garena_res}
                else:
                    # Garena jo asli error dega wahi dikhayega (Jaise Invalid Token)
                    error_msg = garena_res.get("error_msg") or garena_res.get("message") or "Garena Binding Error"
                    res = {"success": False, "message": error_msg}
                
                self.wfile.write(json.dumps(res).encode())
            except Exception as e:
                self.wfile.write(json.dumps({"success": False, "message": "Garena Timeout", "error": str(e)}).encode())

        # --- STEP 2: REAL CONFIRM BIND ---
        elif "/api/confirm" in path:
            if not access_token or not email or not otp:
                self.wfile.write(json.dumps({"success": False, "message": "Missing Token/Email/OTP"}).encode())
                return

            # Real Garena MSDK Confirmation Endpoint
            confirm_url = "https://account.garena.com/api/v1/bind/confirm"
            
            payload = {
                "access_token": access_token,
                "email": email,
                "otp": otp,
                "app_id": app_id,
                "region": region,
                "security_code": "123456"
            }

            try:
                response = requests.post(confirm_url, json=payload, headers=headers, timeout=15)
                garena_res = response.json()

                # REAL VALIDATION: Sahi pe Sahi, Galat pe Galat
                if garena_res.get("error") == 0 or garena_res.get("status") == "success":
                    res = {"success": True, "message": "Free Fire Account Binded!", "data": garena_res}
                else:
                    # Agar OTP galat hua toh Garena error bhejega aur ye wahi dikhayega
                    error_msg = garena_res.get("error_msg") or garena_res.get("message") or "Invalid OTP / Bind Failed"
                    res = {"success": False, "message": error_msg}
                
                self.wfile.write(json.dumps(res).encode())
            except Exception as e:
                self.wfile.write(json.dumps({"success": False, "message": "Verification Error", "error": str(e)}).encode())

        else:
            self.wfile.write(json.dumps({"success": False, "message": "Invalid API Endpoint"}).encode())
