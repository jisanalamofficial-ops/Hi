import requests
import json
import hashlib
import hmac
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # URL Parse karna
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        # Common Parameters nikalna
        access_token = query.get('access_token', [None])[0]
        email = query.get('email', [None])[0]
        otp = query.get('otp', [None])[0]
        security_code = "123456" # Fixed Security Code

        # Response Headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Check karna ki kaunsa endpoint hit hua hai
        
        # --- PEHLA STEP: SEND OTP ---
        if "/api/send-otp" in path:
            if not access_token or not email:
                self.wfile.write(json.dumps({"error": "Missing access_token or email"}).encode())
                return

            # AUTO IDENTITY TOKEN & HMAC SIGNATURE (Simulated)
            # Mobile Signature hmac logic: hmac(key, data)
            timestamp = str(int(time.time()))
            msg = f"{access_token}{email}{timestamp}".encode()
            sig = hmac.new(security_code.encode(), msg, hashlib.sha256).hexdigest()

            # Garena BD Server Simulation Response
            res = {
                "status": "success",
                "message": f"OTP verification code sent to {email}",
                "data": {
                    "identity_token": f"ID_{hashlib.md5(access_token.encode()).hexdigest()}",
                    "signature": sig,
                    "region": "BD",
                    "security_code": security_code
                }
            }
            self.wfile.write(json.dumps(res).encode())

        # --- DUSRA STEP: CONFIRM BIND ---
        elif "/api/confirm" in path:
            if not access_token or not email or not otp:
                self.wfile.write(json.dumps({"error": "Missing token, email or otp"}).encode())
                return

            # Garena Confirmation Simulation
            res = {
                "status": "success",
                "message": "Free Fire Account Bind Successfully",
                "details": {
                    "account": email,
                    "otp_verified": otp,
                    "region": "BD",
                    "security_code": security_code
                }
            }
            self.wfile.write(json.dumps(res).encode())

        else:
            self.wfile.write(json.dumps({"error": "Invalid endpoint. Use /api/send-otp or /api/confirm"}).encode())
