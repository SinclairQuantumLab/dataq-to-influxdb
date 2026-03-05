import pytest
import socketio
import requests
from requests.auth import HTTPDigestAuth
import threading
import time

# --- DI-808 configuration ---
# loaded from "server_config.yaml" by config.py
SERVER_URL = r"http://dataq1"
USERNAME = "admin"
PASSWORD = "admin"

EVENT_NAME = 'apiChannel'

class TestDI808Connection:
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Step 0: Authenticate and prepare headers."""
        session = requests.Session()
        session.auth = HTTPDigestAuth(USERNAME, PASSWORD)
        response = session.get(f"{SERVER_URL}/configuration/current.general.json")
        assert response.status_code == 200
        
        ws_path = "/socket.io/?transport=websocket&EIO=3"
        req = requests.Request('GET', f"{SERVER_URL}{ws_path}")
        prepared = session.prepare_request(req)
        return {k: v for k, v in prepared.headers.items() if k in ['Authorization', 'Cookie']}

    @pytest.fixture(scope="class")
    def sio_client(self, auth_headers):
        """Manage Socket.IO lifecycle."""
        sio = socketio.Client(logger=False, engineio_logger=False)
        
        # Initial connection
        sio.connect(SERVER_URL, transports=['websocket'], headers=auth_headers)
        # Give a small buffer for the session to bind
        time.sleep(1.0)
        
        yield sio
        
        if sio.connected:
            sio.disconnect()

    @pytest.fixture
    def ack_handler(self):
        """
        Fixture Factory: Returns (callback_func, response_container, event)
        This allows reusing the ACK logic in every test.
        """
        class AckData:
            def __init__(self):
                self.event = threading.Event()
                self.container = {}

            def callback(self, data):
                print(f"\n[ACK Received] {data}")
                self.container['data'] = data
                self.event.set()

        return AckData()

    def test_01_connection(self, sio_client):
        """Check if connection is alive."""
        print("\n[Test 01] Verifying Connection...")
        assert sio_client.connected is True
        print("=> Connected.")


    def test_02_send_start(self, sio_client, ack_handler):
        """Send 'start' command and check ACK."""
        print("\n[Test 02] Sending 'start' command...")
        payload = {"ApiCall": "start"}

        sio_client.emit(EVENT_NAME, payload, callback=ack_handler.callback)

        success = ack_handler.event.wait(timeout=5.0)
        assert success is True, "Device failed to ACK 'start' command"
        data = ack_handler.container['data']
        # 1. Verify that ApiReturn is exactly "start"
        assert data.get("ApiReturn") == "start"
        # 2. 🚨 Ensure there is no ApiError in the response for a true success!
        assert "ApiError" not in data, f"Device returned an error: {data.get('ApiError')}"
        
        print("=> 'start' command acknowledged WITHOUT ERRORS.")

    def test_03_get_status(self, sio_client, ack_handler):
        """Send 'getStatusState' and check response."""
        print("\n[Test 03] Sending 'getStatusState' command...")
        payload = {"ApiCall": "getStatusState", "ApiValue": None}
        
        sio_client.emit(EVENT_NAME, payload, callback=ack_handler.callback)
        
        success = ack_handler.event.wait(timeout=5.0)
        assert success is True, "Device failed to ACK 'getStatusState' command"
        assert ack_handler.container['data'].get("ApiReturn") == "getStatusState"
        
        current_val = ack_handler.container['data'].get("ApiValue")
        print(f"=> Device status check verified. Value: {current_val}")