import socketio
import requests
from requests.auth import HTTPDigestAuth
import time
import struct

# --- Configuration ---
SERVER_URL = r'http://192.168.50.83'
USERNAME = 'admin'           # Default username is usually 'admin'
PASSWORD = 'admin'        # Replace with your actual password

EVENT_NAME = 'apiChannel'

def main():
    print(f"Target Device: {SERVER_URL}")
    print("1. Authenticating and extracting headers...")
    
    http_session = requests.Session()
    auth_obj = HTTPDigestAuth(USERNAME, PASSWORD)
    http_session.auth = auth_obj
    
    dummy_resp = http_session.get(f"{SERVER_URL}/configuration/current.general.json")
    if dummy_resp.status_code != 200:
        print(f"Auth Failed: {dummy_resp.status_code}")
        return

    ws_path = "/socket.io/?transport=websocket&EIO=3"
    req = requests.Request('GET', f"{SERVER_URL}{ws_path}")
    prepared = http_session.prepare_request(req)
    
    custom_headers = {}
    if prepared.headers.get('Authorization'): 
        custom_headers['Authorization'] = prepared.headers.get('Authorization')
    if prepared.headers.get('Cookie'): 
        custom_headers['Cookie'] = prepared.headers.get('Cookie')

    print("2. Connecting to WebSocket...")
    # 통신이 안정적인 것을 확인했으니, 이제 지저분한 내부 로그는 끕니다.
    sio = socketio.Client(logger=False, engineio_logger=False)

    # @sio.event
    # def connect():
    #     print(f"\n[{time.strftime('%X')}] SUCCESS: Connected!")
    #     print(f"[{time.strftime('%X')}] Sending 'streamData' request to start streaming...\n")
        
    #     # 기기에게 데이터 스트림을 보내달라고 신호를 줍니다.
    #     stream_request = {"ApiCall": "streamData", "ApiValue": None}
    #     sio.emit(EVENT_NAME, stream_request)

    # @sio.event
    # def connect():
    #     print(f"\n[{time.strftime('%X')}] SUCCESS: Connected!")
        
    #     # 1. 기기 상태 확인 명령 (ApiValue 항목 아예 삭제)
    #     status_request = {"ApiCall": "getStatusState"}
    #     sio.emit(EVENT_NAME, status_request)
    #     print(f"[{time.strftime('%X')}] Sent: {status_request}")

    #     # 2. 스트리밍 데이터 요청 (ApiValue 항목 아예 삭제)
    #     stream_request = {"ApiCall": "streamData"}
    #     sio.emit(EVENT_NAME, stream_request)
    #     print(f"[{time.strftime('%X')}] Sent: {stream_request}")

    # 콜백(ACK) 핸들러 (위치 유지)
    def ack_handler(command_name):
        def handler(response):
            print(f"[{time.strftime('%X')}] 📩 ACK for '{command_name}': {response}")
        return handler

    @sio.event
    def connect():
        print(f"\n[{time.strftime('%X')}] SUCCESS: Connected!")
        
        # 연결되자마자는 start 명령만 보냅니다. (streamData는 여기서 빼버립니다)
        start_req = {"ApiCall": "start"}
        print(f"[{time.strftime('%X')}] Sent: {start_req}")
        sio.emit(EVENT_NAME, start_req, callback=ack_handler("start"))

    @sio.event
    def disconnect():
        print(f"\n[{time.strftime('%X')}] DISCONNECTED from server.")

    @sio.on(EVENT_NAME)
    def on_api_channel(data):
        if isinstance(data, dict):
            update_type = data.get("ApiUpdate")
            update_value = data.get("ApiValue")
            
            # 1. 기기 상태가 변할 때마다 체크합니다.
            if update_type == "statusState":
                print(f"[{time.strftime('%X')}] ℹ️ STATE CHANGED TO: {update_value}")
                
                # 핵심! 기기가 완벽하게 Recording 상태에 돌입했을 때 스트리밍을 요청합니다.
                if update_value == "Recording":
                    print(f"[{time.strftime('%X')}] 🚀 Device is now Recording! Requesting Data Stream...")
                    stream_req = {"ApiCall": "streamData", "ApiValue": True}
                    sio.emit(EVENT_NAME, stream_req, callback=ack_handler("streamData"))

            # 2. 고대하던 실시간 데이터 스트림이 도착했을 때
            elif update_type == "sessionDataStream":
                raw_buffer = update_value
                if isinstance(raw_buffer, bytes) and len(raw_buffer) > 0:
                    num_doubles = len(raw_buffer) // 8
                    try:
                        values = struct.unpack(f'<{num_doubles}d', raw_buffer)
                        formatted_values = [f"{v:.4f}" for v in values]
                        print(f"[{time.strftime('%X')}] 📈 STREAM: {formatted_values}")
                    except Exception as e:
                        print(f"[{time.strftime('%X')}] Decode Error: {e}")
                else:
                    print(f"[{time.strftime('%X')}] ⚠️ Stream update empty or not bytes.")
            
            # 그 외의 알림들
            else:
                print(f"[{time.strftime('%X')}] ℹ️ UPDATE: {data}")
    
    # ---------------------------------------------------------
    # 🎉 드디어 찾은 데이터 수신 전용 주파수!
    # ---------------------------------------------------------
    @sio.on('sessionDataStream')
    def on_session_data_stream(data):
        # Socket.IO가 알아서 바이너리 메시지를 data 변수에 넣어줍니다.
        if isinstance(data, bytes) and len(data) > 0:
            num_doubles = len(data) // 8  # 8바이트(Double) 단위로 쪼갭니다.
            try:
                # '<'는 리틀 엔디안(Little-endian), 'd'는 Double을 의미합니다.
                values = struct.unpack(f'<{num_doubles}d', data)
                formatted_values = [f"{v:.4f}" for v in values]
                print(f"[{time.strftime('%X')}] 🌊 STREAM: {formatted_values}")
            except Exception as e:
                print(f"[{time.strftime('%X')}] Decode Error: {e}")
        else:
            # 바이너리가 아니라 텍스트나 다른 형태가 오면 출력해 봅니다.
            print(f"[{time.strftime('%X')}] ⚠️ 알 수 없는 스트림 데이터: {data}")

    # 혹시 모를 다른 이벤트들을 캡처하기 위한 리스너
    @sio.on('message')
    def on_message(data):
        print(f"[{time.strftime('%X')}] MSG: {data}")

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