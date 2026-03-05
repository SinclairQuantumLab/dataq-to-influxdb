import socketio
import requests
from requests.auth import HTTPDigestAuth
import time

# --- Configuration ---
# DO NOT CHANGE THESE VALUES
SERVER_URL = r'http://dataq1'
USERNAME = 'user'
PASSWORD = 'user'
EVENT_NAME = 'apiChannel'

def main():
    print(f"Target Device: {SERVER_URL}")
    print("1. Authenticating and extracting headers...")
    
    http_session = requests.Session()
    http_session.auth = HTTPDigestAuth(USERNAME, PASSWORD)
    
    # Complete Digest challenge to get session cookies
    dummy_resp = http_session.get(f"{SERVER_URL}/configuration/current.general.json")
    if dummy_resp.status_code != 200:
        print(f"Auth Failed: {dummy_resp.status_code}")
        return
    print("=> Auth Success!")

    # Prepare WebSocket headers
    ws_path = "/socket.io/?transport=websocket&EIO=3"
    req = requests.Request('GET', f"{SERVER_URL}{ws_path}")
    prepared = http_session.prepare_request(req)
    custom_headers = {
        k: prepared.headers.get(k) for k in ['Authorization', 'Cookie'] if prepared.headers.get(k)
    }

    print("2. Connecting to WebSocket...")
    sio = socketio.Client(logger=False, engineio_logger=False)

    # ACK callback handler to verify server received the command
    def ack_handler(command):
        return lambda response: print(f"[{time.strftime('%X')}] 📩 ACK for '{command}': {response}")

    @sio.event
    def connect():
        print(f"\n[{time.strftime('%X')}] SUCCESS: Connected to Socket.IO!")
        
        # Test 1: Get current status with explicit ApiValue: None
        status_req = {"ApiCall": "getStatusState", "ApiValue": None}
        print(f"[{time.strftime('%X')}] Sending: {status_req}")
        
        # Re-implemented callback to see immediate response
        sio.emit(EVENT_NAME, status_req, callback=ack_handler("getStatusState"))

    @sio.event
    def connect_error(data):
        print(f"\n[{time.strftime('%X')}] CONNECTION ERROR: {data}")

    @sio.event
    def disconnect():
        print(f"\n[{time.strftime('%X')}] DISCONNECTED from server.")

    @sio.on(EVENT_NAME)
    def on_api_channel(data):
        # Handle asynchronous updates from the device
        print(f"[{time.strftime('%X')}] ℹ️ UPDATE ON '{EVENT_NAME}': {data}")

    @sio.on('sessionDataStream')
    def on_session_data_stream(data):
        # Detect if binary stream is active
        data_len = len(data) if isinstance(data, bytes) else "N/A"
        print(f"[{time.strftime('%X')}] 🌊 STREAM DETECTED: {data_len} bytes")

    try:
        sio.connect(SERVER_URL, transports=['websocket'], headers=custom_headers)
        sio.wait()
    except KeyboardInterrupt:
        print("\nStopping test...")
        if sio.connected:
            sio.disconnect()
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == '__main__':
    main()