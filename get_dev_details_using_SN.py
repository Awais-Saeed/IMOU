import requests
import json
import uuid
import time
import hashlib
import pprint
from datetime import datetime, timezone, timedelta
import os


# Replace with your actual values
APP_ID = "lc22adc6f7e89d43ab"
APP_SECRET = "f24b23a3b7814ce2bebd2e1730a996"
DATA_CENTER = "openapi-sg.easy4ip.com"              # East Asia region

# offline time conversion into readable format
def time_converter(time_str):
    """
    Converts UTC time (ISO format) to GMT+5 in 12-hour format with AM/PM.
    
    :param time_str: UTC time string in format 'YYYYMMDDTHHMMSSZ'
    :return: Formatted time string in GMT+5 (e.g., 'July 02, 2024 03:47:36 PM')
    """
    try:
        # Step 1: Convert to datetime object
        utc_time = datetime.strptime(time_str, "%Y%m%dT%H%M%SZ")
        
        # Step 2: Convert to GMT+5
        gmt_plus_5_time = utc_time.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=5)))
        
        # Step 3: Format the output in 12-hour format with AM/PM
        return gmt_plus_5_time.strftime("%B %d, %Y %I:%M:%S %p")
    
    except ValueError:
        return "NA"

"""
    Step 1:
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

ACCESS_TOKEN = str(access_token)


"""
    Step 2:
    Fetch device details
"""
# Device ID(s) - Replace with actual device serial numbers
DEVICE_IDS = ["9B04AC0PAZ48C71", "9B04AC0PAZA6FF4"]

# Request address
DEVICE_DETAILS_URL = f"https://{DATA_CENTER}/openapi/listDeviceDetailsByIds"

# Generate required signature parameters
current_time = str(int(time.time()))
nonce = str(uuid.uuid4())  # Random string
sign_string = f"time:{current_time},nonce:{nonce},appSecret:{APP_SECRET}"
sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()

# Create request payload
payload = {
    "system": {
        "ver": "1.0",
        "appId": APP_ID,
        "sign": sign,
        "time": int(current_time),
        "nonce": nonce
    },
    "id": str(uuid.uuid4()),  # Unique request ID
    "params": {
        "deviceList": [{"deviceId": device_id, "channelId": ["0"]} for device_id in DEVICE_IDS],
        "token": ACCESS_TOKEN
    }
}

# Headers
headers = {
    "Content-Type": "application/json"
}

# Send request
response = requests.post(DEVICE_DETAILS_URL, json=payload, headers=headers)

pprint.pprint(response.json())

# Process response
if response.status_code == 200:
    data = response.json()
    if data["result"]["code"] == "0":  # code is Request return code. 0 means successful operation
        for device in data["result"]["data"]["deviceList"]:
            dev_name = device['deviceName']
            dev_status = device['deviceStatus']
            last_offline_time = time_converter(device["channelList"][0]['lastOffLineTime'])
            print(f"✅ Device ID: {device['deviceId']}, Name: {dev_name}, Status: {dev_status}, OFL time: {last_offline_time} ")
    else:
        print("❌ Error:", data["result"]["msg"])
else:
    print("❌ Request failed with status:", response.status_code, response.text)
