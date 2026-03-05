import socketio
import requests
from requests.auth import HTTPDigestAuth
import time
import struct
from config import config  # Import our typed configuration

# --- DI-808 configuration ---
# loaded from "server_config.yaml" by config.py
SERVER_URL = config.server.url
USERNAME = config.auth.username
PASSWORD = config.auth.password

EVENT_NAME = 'apiChannel'

# --- InfluxDB configuration ---
# 1. Connection Settings
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "6tsJ1LgHRYhik5HdRkw2HO5ligoI1X-HOXw-SAsXi-fz5dOqxgX1agvRbrsYd_y_OQdIyj_npdD7V1ReUwJBtw=="  # sinclairgroup_influxdb's admin token
INFLUXDB_ORG = "sinclairgroup"     # The Organization name you set during initial setup
INFLUXDB_BUCKET = "test_data"    # Bucket reserved for testing purposes


def main():
    print(f"Target Device: {SERVER_URL}")
    print("1. Authenticating and extracting headers...")
    
    http_session = requests.Session()
    http_session.auth = HTTPDigestAuth(USERNAME, PASSWORD)
    
    # 1. Trigger HTTP Digest Auth to populate the session with nonce/cookies
    dummy_resp = http_session.get(f"{SERVER_URL}/") 
    if dummy_resp.status_code not in (200, 301, 302):
        print(f"Auth Failed: {dummy_resp.status_code}")
        return

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
        sio.emit(EVENT_NAME, start_req, callback=make_ack_handler("start"))

    @sio.event
    def disconnect():
        print(f"\n[{time.strftime('%X')}] DISCONNECTED from server.")

    @sio.on(EVENT_NAME)
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
                sio.emit(EVENT_NAME, stream_req, callback=make_ack_handler("streamData"))
        else:
            print(f"[{time.strftime('%X')}] ℹ️ UPDATE: {data}")

    # Dedicated handler for binary data stream
    @sio.on('sessionDataStream')
    def on_session_data_stream(data):
        if isinstance(data, bytes) and len(data) > 0:
            num_doubles = len(data) // 8
            try:
                # Unpack little-endian double precision floats
                values = struct.unpack(f'<{num_doubles}d', data)
                formatted_values = [f"{v:.4f}" for v in values]
                print(f"[{time.strftime('%X')}] 🌊 STREAM: {formatted_values}")
            except Exception as e:
                print(f"[{time.strftime('%X')}] Decode Error: {e}")

    try:
        sio.connect(SERVER_URL, transports=['websocket'], headers=custom_headers)
        sio.wait()
    except KeyboardInterrupt:
        print("\nStopping stream and closing connection...")
        if sio.connected:
            sio.disconnect()
    except Exception as e:
        print(f"\nConnection Error: {e}")

if __name__ == '__main__':
    main()