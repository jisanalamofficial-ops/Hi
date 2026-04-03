import requests
import json
import hashlib
import hmac
import time
import urllib3
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# SSL Warnings ko band karne ke liye
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        # Parameters
        access_token = query.get('access_token', [None])[0]
        email = query.get('email', [None])[0]
        otp = query.get('otp', [None])[0]
        
        # Garena Config
        app_id = "100067"
        region = "BD"
        security_code = "123456"
        base_url = "https://msdk.garena.com"

        headers = {
            "Content-Type": "application/json",
            "X-Garena-Region": region,
            "X-Garena-App-Id": app_id,
            "User-Agent": "GarenaFreeFire/1.103.1 (Android; HMAC-Signature)",
            "X-Requested-With": "com.dts.freefireth"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            # --- [1. PLAYER INFO] ---
            if "/api/info" in path:
                if not access_token:
                    self.wfile.write(json.dumps({"success": False, "message": "Token missing"}).encode())
                    return
                
                info_url = f"{base_url}/game/get_mobile_info"
                # verify=False laga diya hai SSL fix ke liye
                res = requests.post(info_url, json={"access_token": access_token, "app_id": app_id, "region": region}, headers=headers, verify=False, timeout=15)
                self.wfile.write(json.dumps(res.json()).encode())

            # --- [2. SEND OTP BIND] ---
            elif "/api/send-otp" in path:
                if not access_token or not email:
                    self.wfile.write(json.dumps({"success": False, "message": "Details missing"}).encode())
                    return

                # A. Identity Token (Verifier)
                v_url = f"{base_url}/com.garena.msdk.account_security_verifier_token"
                v_res = requests.post(v_url, json={"access_token": access_token}, headers=headers, verify=False)
                v_data = v_res.json()
                identity_token = v_data.get("verifier_token") or hashlib.sha1(access_token.encode()).hexdigest()

                # B. HMAC Signature
                timestamp = str(int(time.time()))
                sig_data = f"{access_token}{identity_token}{timestamp}{security_code}"
                signature = hmac.new(security_code.encode(), sig_data.encode(), hashlib.sha256).hexdigest()

                # C. Send OTP Request
                otp_endpoint = f"{base_url}/game/account_security/bind:send_otp"
                payload = {
                    "access_token": access_token,
                    "identity_token": identity_token,
                    "email": email,
                    "region": region,
                    "signature": signature,
                    "timestamp": timestamp,
                    "security_code": security_code
                }

                response = requests.post(otp_endpoint, json=payload, headers=headers, verify=False, timeout=15)
                garena_data = response.json()

                if garena_data.get("error") == 0:
                    res = {"success": True, "message": "OTP sent to " + email, "token_used": identity_token}
                else:
                    res = {"success": False, "message": garena_data.get("message", "Garena Rejected Request"), "garena_error": garena_data}
                
                self.wfile.write(json.dumps(res).encode())

            # --- [3. CONFIRM BIND] ---
            elif "/api/confirm" in path:
                if not access_token or not email or not otp:
                    self.wfile.write(json.dumps({"success": False, "message": "Missing Params"}).encode())
                    return

                confirm_endpoint = f"{base_url}/game/account_security/bind:verify_otp"
                payload = {
                    "access_token": access_token,
                    "otp": otp,
                    "email": email,
                    "app_id": app_id,
                    "region": region,
                    "security_code": security_code
                }

                response = requests.post(confirm_endpoint, json=payload, headers=headers, verify=False, timeout=15)
                garena_res = response.json()

                if garena_res.get("error") == 200 or garena_res.get("status") == "success":
                    res = {"success": True, "message": "Bind Success!", "data": garena_res}
                else:
                    res = {"success": False, "message": garena_res.get("message", "Invalid OTP"), "garena_error": garena_res}
                
                self.wfile.write(json.dumps(res).encode())

        except Exception as e:
            self.wfile.write(json.dumps({"success": False, "message": "Final Connection Error", "error": str(e)}).encode())
