from pprint import pprint

import socketio
import requests
from requests.auth import HTTPDigestAuth
import time
import struct

# >>> InfluxDB configuration >>>
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
# Connection Settings
INFLUXDB_URL = "http://synology-nas:8086"
INFLUXDB_TOKEN = "xixuoRzjm51D2WQh5uHnqjd0H28NJuaKpiHAmmSzEUlqgUhxRl0A01Na6-a_gX6BENlP3xx8FEoGP-qMx0Xrow=="  # sinclairgroup_influxdb's admin token


INFLUXDB_ORG = "sinclairgroup"     # The Organization name you set during initial setup
INFLUXDB_BUCKET = "imaq"    # main bucket for IMAQ lab
# Initialize the InfluxDB Client and the Write API
INFLUXDB_CLIENT = influxdb_client.InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
INFLUXDB_WRITE_API = INFLUXDB_CLIENT.write_api(write_options=SYNCHRONOUS)
# <<< InfluxDB configuration <<<



# --- DI-808 configuration ---
# measurement equipment info
EQUIPMENT = "DATAQ DI-808-32 (SN: 691B1B09)"
# server and auth
SERVER_URL = r"http://dataq1"
USERNAME = "admin"
PASSWORD = "admin"
# channel configuration
NUM_CHANNELS = 8
CHANNEL_CONFIG = {
        # "channel name": "description"
        "Ch1": "Gaussmeter 1 Vx",
        "Ch2": "Gaussmeter 1 Vy",
        "Ch3": "Gaussmeter 1 Vz",
        # "Ch4": "", # not in use
        "Ch5": "Gaussmeter 2 Vx",
        "Ch6": "Gaussmeter 2 Vy",
        "Ch7": "Gaussmeter 2 Vz",
        # "Ch8": "", # not in use
    }




print(f"Target Device: {SERVER_URL}")
print("1. Authenticating and extracting headers...")

http_session = requests.Session()
http_session.auth = HTTPDigestAuth(USERNAME, PASSWORD)

# 1. Trigger HTTP Digest Auth to populate the session with nonce/cookies
dummy_resp = http_session.get(f"{SERVER_URL}/") 
if dummy_resp.status_code not in (200, 301, 302):
    # print(f"Auth Failed: {dummy_resp.status_code}")
    raise ConnectionError(f"Authentication failed: {dummy_resp.status_code}. Check credentials and server status.")

# 2. Simulate a WebSocket GET request to extract the generated headers
ws_path = "/socket.io/?transport=websocket&EIO=3"
req = requests.Request('GET', f"{SERVER_URL}{ws_path}")
prepared = http_session.prepare_request(req)

# 3. Filter and store only the required headers for the Socket.IO connection
custom_headers = {
    k: v for k, v in prepared.headers.items() if k in ['Authorization', 'Cookie']
}

print("2. Connecting to WebSocket...")
sio = socketio.Client(logger=False, engineio_logger=False)

# Reusable ACK callback handler
def make_ack_handler(command_name):
    return lambda response: print(f"[{time.strftime('%X')}] 📩 ACK for '{command_name}': {response}")

@sio.event
def connect():
    print(f"\n[{time.strftime('%X')}] SUCCESS: Connected!")
    start_req = {"ApiCall": "start"}
    sio.emit('apiChannel', start_req, callback=make_ack_handler("start"))

@sio.event
def disconnect():
    print(f"\n[{time.strftime('%X')}] DISCONNECTED from server.")

@sio.on('apiChannel')
def on_api_channel(data):
    if not isinstance(data, dict):
        print(f"[{time.strftime('%X')}] ℹ️ UPDATE: {data}")
        return

    update_type = data.get("ApiUpdate")
    update_value = data.get("ApiValue")
    
    # Monitor device status and trigger data stream when Recording
    if update_type == "statusState":
        print(f"[{time.strftime('%X')}] ℹ️ STATE CHANGED TO: {update_value}")
        if update_value == "Recording":
            print(f"[{time.strftime('%X')}] 🚀 Requesting Data Stream...")
            stream_req = {"ApiCall": "streamData", "ApiValue": True}
            sio.emit('apiChannel', stream_req, callback=make_ack_handler("streamData"))
    else:
        print(f"[{time.strftime('%X')}] ℹ️ UPDATE: {data}")


# Dedicated handler for binary data stream
# raise error if exceptions happen three times
ex_threshold = 3
ex_count = 0
@sio.on('sessionDataStream')
def on_session_data_stream(data):
    # "data" variable is expected to be a binary blob containing interleaved channel data as little-endian doubles.
    if isinstance(data, bytes) and len(data) > 0:
        try:
            num_doubles = len(data) // 8 # 8 bytes per double precision float
            if num_doubles != NUM_CHANNELS:
                raise ValueError(f"Expected {NUM_CHANNELS} channels, but received data for {num_doubles} channels. Data length: {len(data)} bytes.")
            # Unpack little-endian double precision floats
            values = struct.unpack(f'<{num_doubles}d', data)

            print(f"[{time.strftime('%X')}] 🌊 STREAM: " + ", ".join(f"{value:>10.6f}" for value in values))


            # upload to InfluxDB
            influxdb_records = [
                {
                    "measurement": "dataq_data",  
                    "tags": {
                        "equipment": EQUIPMENT,
                        "Channel": f"Ch{ich+1}",
                        "source": "API Stream",
                        "Description": CHANNEL_CONFIG.get(f"Ch{ich+1}", "N/A"),
                    },
                    "fields": {
                        "Voltage[V]": values[ich],
                    },
                } for ich in range(NUM_CHANNELS) if f"Ch{ich+1}" in CHANNEL_CONFIG
            ]

            # pprint(influxdb_records)
            INFLUXDB_WRITE_API.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=influxdb_records)

        except Exception as ex:
            print(f"[{time.strftime('%X')}] Error occured: {ex}")
            global ex_count, ex_threshold
            if ex_count >= ex_threshold:
                raise
            ex_count += 1

try:
    sio.connect(SERVER_URL, transports=['websocket'], headers=custom_headers)
    sio.wait()
except KeyboardInterrupt:
    print("\n[INFO] KeyboardInterrupt received.")
finally:
    print("\n[INFO] Shutting down gracefully...", end=" ")
    try:
        sio.disconnect()
    except:
        pass
    print("Done")