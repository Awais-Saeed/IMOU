import requests
import json
import hashlib
import time
import uuid
import pprint
from datetime import datetime, timezone, timedelta
import os


APP_ID = "lc22adc6f7e89d43ab"
APP_SECRET = "f24b23a3b7814ce2bebd2e1730a996"
DATA_CENTER = "openapi-sg.easy4ip.com"          # East Asia region


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
    Create HTML page with status
"""
# Request addresses
# first for fetching all device IDs
# second for fetching Device Name, Status, Last Offline Time
DEVICE_LIST_URL = f"https://{DATA_CENTER}/openapi/deviceBaseList"
DEVICE_DETAILS_URL = f"https://{DATA_CENTER}/openapi/listDeviceDetailsByIds"

# Function to Convert Time (GMT+5)
def time_converter(time_str):
    try:
        utc_time = datetime.strptime(time_str, "%Y%m%dT%H%M%SZ")
        gmt_plus_5_time = utc_time.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=5)))
        return gmt_plus_5_time.strftime("%B %d, %Y %I:%M:%S %p")
    except ValueError:
        return ""

# Function to Generate Signature Parameters
def generate_signature():
    current_time = str(int(time.time()))
    nonce = str(uuid.uuid4())
    sign_string = f"time:{current_time},nonce:{nonce},appSecret:{APP_SECRET}"
    sign = hashlib.md5(sign_string.encode("utf-8")).hexdigest()
    return {"time": int(current_time), "nonce": nonce, "sign": sign}

# Step 1: Calling 1st request addresss
# Payload for 1st request address
signature = generate_signature()
payload_list = {
    "system": {
        "ver": "1.0",
        "appId": APP_ID,
        **signature  # dictionary unpacking. signature = {"sign": "your_generated_signature", "time": int(time.time()), "nonce": str(uuid.uuid4()) }
    },
    "id": str(uuid.uuid4()),
    "params": {
        "token": ACCESS_TOKEN,
        "bindId": -1,
        "limit": 128,
        "type": "bindAndShare",
        "needApInfo": True
    }
}

headers = {"Content-Type": "application/json"}
response = requests.post(DEVICE_LIST_URL, json=payload_list, headers=headers)
data = response.json()

device_ids = []
if response.status_code == 200 and data["result"]["code"] == "0":
    device_ids = [device["deviceId"] for device in data["result"]["data"]["deviceList"]]

# Step 2: Calling 2nd request addresss
devices = []
count = 1
online_count = offline_count = 0

# Payload for 2nd request address
signature = generate_signature()
if device_ids:
    payload_details = {
        "system": {
            "ver": "1.0",
            "appId": APP_ID,
            **signature  # dictionary unpacking. signature = {"sign": "your_generated_signature", "time": int(time.time()), "nonce": str(uuid.uuid4()) }
        },
        "id": str(uuid.uuid4()),
        "params": {
            "deviceList": [{"deviceId": device_id, "channelId": ["0"]} for device_id in device_ids],
            "token": ACCESS_TOKEN
        }
    }

    response = requests.post(DEVICE_DETAILS_URL, json=payload_details, headers=headers)
    data = response.json()
    # Extract Device Information
    if response.status_code == 200 and data["result"]["code"] == "0":
        for device in data["result"]["data"]["deviceList"]:
            devices.append({
                "count":count,
                "device_id": device["deviceId"],
                "device_name": device["deviceName"],
                "device_status": "🟢 Online" if device["deviceStatus"] == "online" else "🔴 Offline",
                "last_offline_time": time_converter(device["channelList"][0]["lastOffLineTime"])
            })
            count = count + 1

            # count online and offline cams
            is_online = device["deviceStatus"] == "online"
            online_count += is_online
            offline_count += not is_online

else:
    devices = []

# Step 3: Generate HTML
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Device Details</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            text-align: center;
        }}
        h2 {{
            color: #333;
        }}
        .device-list {{
            margin: 20px auto;
            padding: 20px;
            width: 60%;
            background: white;
            border-radius: 10px;
            box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 10px;
            border: 1px solid #ddd;
            text-align: left;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        .online {{
            color: green;
            font-weight: bold;
        }}
        .offline {{
            color: red;
            font-weight: bold;
        }}
    </style>
</head>
<body>

    <h2>Device Details</h2>
    <div class="device-list">
        <table>
            <tr>
                <th>Sr. No.</th>
                <th>Device ID</th>
                <th>Device Name</th>
                <th>Status</th>
                <th>Last Offline Time</th>
            </tr>

    <!-- Online & Offline Count Display -->
    <div class="device-list">
        <h3>Summary</h3>
        <p style="font-size: 18px;">
            <span style="color: green;">🟢 Online Cameras: <strong>""" + str(online_count) + """</strong></span> &nbsp;&nbsp;
            <span style="color: red;">🔴 Offline Cameras: <strong>""" + str(offline_count) + """</strong></span>
        </p>
    </div>
"""

if devices:
    for device in devices:
        status_class = "online" if "Online" in device["device_status"] else "offline"
        html_content += f"""
            <tr>
                <td>{device["count"]}</td>
                <td>{device["device_id"]}</td>
                <td>{device["device_name"]}</td>
                <td class="{status_class}">{device["device_status"]}</td>
                <td>{device["last_offline_time"]}</td>
            </tr>
        """
else:
    html_content += """
            <tr>
                <td colspan="4">No device data available.</td>
            </tr>
    """

html_content += """
        </table>
    </div>
</body>
</html>
"""

# Step 4: Save HTML File
with open("output.html", "w", encoding="utf-8") as file:
    file.write(html_content)

print("✅ HTML file generated successfully! Open 'output.html' in Chrome.")
