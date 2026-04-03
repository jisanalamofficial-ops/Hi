import requests
import json
import hashlib
import hmac
import time
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
        security_code = "123456" # Fixed Security Code

        # Response Headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Real Garena Headers (Mobile Signature Simulation)
        headers = {
            "Content-Type": "application/json",
            "X-Garena-Region": "BD",
            "X-Garena-App-Id": "100067",
            "User-Agent": "GarenaFreeFire/1.103.1 (Android; HMAC-Signature)"
        }

        # --- STEP 1: OTP BHEJNA ---
        if "/api/send-otp" in path:
            if not access_token or not email:
                self.wfile.write(json.dumps({"success": False, "message": "Token aur Email zaroori hai"}).encode())
                return

            # Garena Real OTP Request Link
            otp_url = "https://auth.garena.com/api/v2/bind/send_otp"
            payload = {
                "access_token": access_token,
                "email": email,
                "region": "BD",
                "security_code": security_code
            }

            try:
                # Garena ko request bhej rahe hain
                response = requests.post(otp_url, json=payload, headers=headers, timeout=10)
                res_data = response.json()

                # CHECK: Agar Garena ne success code (200) diya aur koi error nahi hai
                if response.status_code == 200 and "error" not in res_data:
                    final_res = {"success": True, "message": "Real OTP sent to " + email}
                else:
                    # Agar token expire hai ya koi aur galti hai
                    error_msg = res_data.get("error_description") or res_data.get("error") or "Garena Rejected Request"
                    final_res = {"success": False, "message": error_msg}
                
                self.wfile.write(json.dumps(final_res).encode())
            except:
                self.wfile.write(json.dumps({"success": False, "message": "Garena Server Busy"}).encode())

        # --- STEP 2: OTP CONFIRM KARNA (STRICT CHECK) ---
        elif "/api/confirm" in path:
            if not access_token or not email or not otp:
                self.wfile.write(json.dumps({"success": False, "message": "Sabhi details daalein (Token, Email, OTP)"}).encode())
                return

            # Garena Real Confirmation Link
            confirm_url = "https://auth.garena.com/api/v2/bind/confirm"
            payload = {
                "access_token": access_token,
                "otp": otp,
                "email": email,
                "security_code": security_code
            }

            try:
                response = requests.post(confirm_url, json=payload, headers=headers, timeout=10)
                res_data = response.json()

                # ASLI VALIDATION: Yahan check ho raha hai sahi ya galat
                # Agar Garena ne 'success' status diya hai toh hi True hoga
                if response.status_code == 200 and res_data.get("status") == "success":
                    final_res = {
                        "success": True, 
                        "message": "FF Account Successfully Binded!",
                        "account": email
                    }
                else:
                    # AGAR OTP GALAT HUA TOH GARENA YE ERROR BHEJEGA
                    error_info = res_data.get("error_description") or res_data.get("error") or "Invalid OTP / Code Expired"
                    final_res = {
                        "success": False, 
                        "message": error_info # Yahan "Invalid OTP" dikhayega
                    }
                
                self.wfile.write(json.dumps(final_res).encode())
            except:
                self.wfile.write(json.dumps({"success": False, "message": "Verification Timeout"}).encode())

        else:
            self.wfile.write(json.dumps({"success": False, "message": "Invalid Path"}).encode())
