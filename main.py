import socketio
import requests
from requests.auth import HTTPDigestAuth
import time
import struct

# --- Configuration ---
SERVER_URL = r'http://192.168.50.83'
USERNAME = 'admin'
PASSWORD = 'admin'
EVENT_NAME = 'apiChannel'

def main():
    print(f"Target Device: {SERVER_URL}")
    print("1. Authenticating and extracting headers...")
    
    http_session = requests.Session()
    http_session.auth = HTTPDigestAuth(USERNAME, PASSWORD)
    
    dummy_resp = http_session.get(f"{SERVER_URL}/configuration/current.general.json")
    if dummy_resp.status_code != 200:
        print(f"Auth Failed: {dummy_resp.status_code}")
        return

    ws_path = "/socket.io/?transport=websocket&EIO=3"
    req = requests.Request('GET', f"{SERVER_URL}{ws_path}")
    prepared = http_session.prepare_request(req)
    
    # Extract required headers for WebSocket handshake
    custom_headers = {
        k: prepared.headers.get(k) for k in ['Authorization', 'Cookie'] if prepared.headers.get(k)
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