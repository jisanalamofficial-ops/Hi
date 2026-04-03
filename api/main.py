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

        # Parameters
        access_token = query.get('access_token', [None])[0]
        email = query.get('email', [None])[0]
        otp = query.get('otp', [None])[0]
        
        # Garena Internal Config
        app_id = 100067
        region = "BD"
        security_code = "123456"
        # Garena Official MSDK Base URL
        base_url = "https://msdk.garena.com"

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Real Mobile Headers (Jisne mobile signature kaha tha)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "GarenaFreeFire/1.103.1 (Android; MSDK-Bind)",
            "X-Garena-Region": region,
            "X-Garena-App-Id": str(app_id),
            "X-Requested-With": "com.dts.freefireth"
        }

        # --- STEP 1: IDENTITY TOKEN & SEND OTP ---
        if "/api/send-otp" in path:
            if not access_token or not email:
                self.wfile.write(json.dumps({"success": False, "message": "Access Token/Email missing"}).encode())
                return

            # AUTO IDENTITY TOKEN GENERATION (Real Logic)
            # Garena identity token usually uses a hash of the access token
            identity_token = hashlib.sha1(access_token.encode()).hexdigest()

            # HMAC SIGNATURE GENERATION
            # Payload data ko sign karna taaki Garena accept kare
            timestamp = str(int(time.time()))
            sig_data = f"{access_token}{identity_token}{timestamp}{security_code}"
            signature = hmac.new(security_code.encode(), sig_data.encode(), hashlib.sha256).hexdigest()

            # Endpoints extracted from your file
            otp_endpoint = f"{base_url}/game/account_security/bind:send_otp"
            
            payload = {
                "access_token": access_token,
                "identity_token": identity_token,
                "email": email,
                "app_id": app_id,
                "region": region,
                "signature": signature,
                "timestamp": timestamp,
                "security_code": security_code
            }

            try:
                response = requests.post(otp_endpoint, json=payload, headers=headers, timeout=15)
                garena_res = response.json()

                # Agar Garena ne request accept karli
                if garena_res.get("error") == 0:
                    res = {"success": True, "message": f"OTP sent to {email}", "id_token": identity_token}
                else:
                    res = {"success": False, "message": garena_res.get("message", "Garena Refused OTP Request")}
                
                self.wfile.write(json.dumps(res).encode())
            except:
                self.wfile.write(json.dumps({"success": False, "message": "MSDK Server Error"}).encode())

        # --- STEP 2: VERIFY OTP & CONFIRM BIND ---
        elif "/api/confirm" in path:
            if not access_token or not otp or not email:
                self.wfile.write(json.dumps({"success": False, "message": "Token/Email/OTP Missing"}).encode())
                return

            # Verification Endpoint from your file
            verify_endpoint = f"{base_url}/game/account_security/bind:verify_otp"

            payload = {
                "access_token": access_token,
                "otp": otp,
                "email": email,
                "app_id": app_id,
                "region": region,
                "security_code": security_code
            }

            try:
                response = requests.post(verify_endpoint, json=payload, headers=headers, timeout=15)
                garena_res = response.json()

                # Strict Validation: Sahi pe Sahi, Galat pe Galat
                if garena_res.get("error") == 0 and garena_res.get("status") == "success":
                    res = {
                        "success": True, 
                        "message": "Account Bind Successful",
                        "data": garena_res
                    }
                else:
                    # Garena jo asli error dega (Invalid OTP) wahi yahan dikhega
                    res = {
                        "success": False, 
                        "message": garena_res.get("message", "Invalid OTP or Binding Failed")
                    }
                
                self.wfile.write(json.dumps(res).encode())
            except:
                self.wfile.write(json.dumps({"success": False, "message": "Verification Timeout"}).encode())

        else:
            self.wfile.write(json.dumps({"error": "Invalid API Path. Use /api/send-otp or /api/confirm"}).encode())
