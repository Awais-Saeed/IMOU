import requests
import json
import hashlib
import time
import uuid
import pprint
from datetime import datetime, timedelta
import os


APP_ID = "lc22adc6f7e89d43ab"
APP_SECRET = "f24b23a3b7814ce2bebd2e1730a996"
DATA_CENTER = "openapi-sg.easy4ip.com"          # East Asia region


"""
    Get/check access token
"""
TOKEN_FILE = "token.json"           # json file containing token and expire time

def generate_token():
    # Request address
    TOKEN_URL = f"https://{DATA_CENTER}/openapi/accessToken"

    # Generate timestamp & nonce
    timestamp = str(int(time.time()))  # Convert to string
    nonce = str(uuid.uuid4())  # Unique request ID

    # create the sign using sequence: "time:<timestamp>,nonce:<nonce>,appSecret:<appSecret>"
    sign_string = f"time:{timestamp},nonce:{nonce},appSecret:{APP_SECRET}"
    sign = hashlib.md5(sign_string.encode("utf-8")).hexdigest()

    # Create request payload
    payload = {
        "system": {
            "ver": "1.0",
            "appId": APP_ID,
            "sign": sign,
            "time": timestamp,
            "nonce": nonce
        },
        "id": str(uuid.uuid4()),  # Unique request ID
        "params": {}  # Required empty params
    }

    # Headers
    headers = {
        "Content-Type": "application/json"
    }

    # Send request
    response = requests.post(TOKEN_URL, json=payload, headers=headers)

    # Process response

    if response.status_code == 200:
        data = response.json()
        print("✅ Status: " +str(response.status_code))
        pprint.pprint(data)

        if data["result"]["code"] == "0":   # code is Request return code. 0 means successfull operation
            access_token = data["result"]["data"]["accessToken"]
            expire_time = data["result"]["data"]["expireTime"]
            print(f"Access Token: {access_token}")
            print(f"⏳ Expires in: {expire_time} seconds")

            token_data = {
                "accessToken": access_token,
                # expiry date = current date + fetched seconds
                "expireTime" : str(datetime.now() + timedelta(seconds=expire_time))
            }

            # save access token and expiry date
            with open(TOKEN_FILE, "w") as f:
                json.dump(token_data, f, indent=4)
            
            print("Token saved successfully!")

        else:
            print("❌ Error:", data["result"]["msg"])
    else:
        print("❌ Request failed with status:", response.status_code, response.text)

    return access_token, expire_time



if os.path.exists(TOKEN_FILE):
    # if token.json exists
    # Read the token.json file
    with open("token.json", "r") as file:
        token_data = json.load(file)

    # Extract values
    access_token = token_data["accessToken"]
    expire_time = token_data["expireTime"]

    if datetime.now() >= datetime.strptime(expire_time, "%Y-%m-%d %H:%M:%S.%f"):
        print("Token expired, getting a fresh one...")
        access_token, expire_time = generate_token()

else:
    access_token, expire_time = generate_token()

