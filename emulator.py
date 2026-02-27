import argparse
import time
import rscp_pb2
from rscp_bridge import RSCPBridge
from cobs import cobs

# Overriding the listener for the Emulator specifically
def emulator_listen(bridge, callback):
    if bridge.ser.in_waiting > 0:
        data = bridge.ser.read(bridge.ser.in_waiting)
        for byte in data:
            if byte == 0x00:
                try:
                    decoded = cobs.decode(bridge.buffer)
                    # Emulator expects ResponseEnvelope from Rover
                    res = rscp_pb2.ResponseEnvelope() 
                    res.ParseFromString(decoded)
                    callback(res)
                except Exception as e:
                    print(f"Emulator parse error: {e}")
                bridge.buffer = bytearray()
            else:
                bridge.buffer.append(byte)

def on_response(response):
    res_type = response.WhichOneof('response')
    print(f"[FROM ROVER] Received: {res_type}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True)
    args = parser.parse_args()
    
    bridge = RSCPBridge(args.port)
    
    # 1. Send Command (RequestEnvelope)
    print("JUDGE: Sending NavigateToGPS command...")
    cmd = rscp_pb2.RequestEnvelope()
    cmd.navigate_to_gps.coordinate.latitude = 38.4237
    cmd.navigate_to_gps.coordinate.longitude = 27.1428
    
    # We use a custom send for the emulator to send a REQUEST
    data = cmd.SerializeToString()
    bridge.ser.write(cobs.encode(data) + b'\x00')

    # 2. Listen for Rover feedback
    while True:
        emulator_listen(bridge, on_response)
        time.sleep(0.01)