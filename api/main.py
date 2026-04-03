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

        # Common Parameters
        access_token = query.get('access_token', [None])[0]
        email = query.get('email', [None])[0]
        otp = query.get('otp', [None])[0]
        
        # Garena Internal Config
        app_id = "100067"
        region = "BD"
        security_code = "123456" # Fixed Security Code
        base_url = "https://msdk.garena.com"

        # Headers: Bilkul asali Free Fire game jaise
        headers = {
            "Content-Type": "application/json",
            "X-Garena-Region": region,
            "X-Garena-App-Id": app_id,
            "User-Agent": "GarenaFreeFire/1.103.1 (Android; MSDK-Binding-System)",
            "X-Requested-With": "com.dts.freefireth",
            "Connection": "keep-alive"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            # --- [FUNCTION 1: GET PLAYER INFO] ---
            if "/api/info" in path:
                if not access_token:
                    self.wfile.write(json.dumps({"success": False, "message": "Access Token missing"}).encode())
                    return
                
                # API Endpoint from your file: /game/get_mobile_info
                info_endpoint = f"{base_url}/game/get_mobile_info"
                payload = {"access_token": access_token, "app_id": app_id, "region": region}
                
                res = requests.post(info_endpoint, json=payload, headers=headers, timeout=15)
                self.wfile.write(json.dumps(res.json()).encode())

            # --- [FUNCTION 2: SEND REAL OTP (BIND)] ---
            elif "/api/send-otp" in path:
                if not access_token or not email:
                    self.wfile.write(json.dumps({"success": False, "message": "Token/Email missing"}).encode())
                    return

                # A. Identity/Verifier Token Generation
                # API Endpoint: /com.garena.msdk.account_security_verifier_token
                verifier_url = f"{base_url}/com.garena.msdk.account_security_verifier_token"
                v_res = requests.post(verifier_url, json={"access_token": access_token}, headers=headers)
                v_data = v_res.json()
                identity_token = v_data.get("verifier_token") or hashlib.sha1(access_token.encode()).hexdigest()

                # B. HMAC Signature Generation
                timestamp = str(int(time.time()))
                sig_data = f"{access_token}{identity_token}{timestamp}{security_code}"
                signature = hmac.new(security_code.encode(), sig_data.encode(), hashlib.sha256).hexdigest()

                # C. Send OTP Request
                # API Endpoint: /game/account_security/bind:send_otp
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

                response = requests.post(otp_endpoint, json=payload, headers=headers, timeout=15)
                garena_data = response.json()

                # Strictly check for error code 0 (Garena's success code)
                if garena_data.get("error") == 0:
                    result = {"success": True, "message": "Real OTP sent to " + email, "garena": garena_data}
                else:
                    result = {"success": False, "message": garena_data.get("message", "Garena Rejected"), "error_code": garena_data.get("error")}
                
                self.wfile.write(json.dumps(result).encode())

            # --- [FUNCTION 3: CONFIRM BIND (VERIFY OTP)] ---
            elif "/api/confirm" in path:
                if not access_token or not email or not otp:
                    self.wfile.write(json.dumps({"success": False, "message": "Details Missing"}).encode())
                    return

                # API Endpoint: /game/account_security/bind:verify_otp
                confirm_endpoint = f"{base_url}/game/account_security/bind:verify_otp"
                payload = {
                    "access_token": access_token,
                    "otp": otp,
                    "email": email,
                    "app_id": app_id,
                    "region": region,
                    "security_code": security_code
                }

                response = requests.post(confirm_endpoint, json=payload, headers=headers, timeout=15)
                garena_data = response.json()

                # Check Garena's real validation
                if garena_data.get("error") == 0 and garena_data.get("status") == "success":
                    result = {"success": True, "message": "Account Successfully Binded!", "data": garena_data}
                else:
                    # Galat OTP par Garena ka asali error dikhayega
                    msg = garena_data.get("message") or "Invalid OTP / Verification Failed"
                    result = {"success": False, "message": msg, "error_code": garena_data.get("error")}
                
                self.wfile.write(json.dumps(result).encode())

            else:
                self.wfile.write(json.dumps({"success": False, "message": "Path Not Found"}).encode())

        except Exception as e:
            self.wfile.write(json.dumps({"success": False, "message": "Connection Error", "error": str(e)}).encode())
