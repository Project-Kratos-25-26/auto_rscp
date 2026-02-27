import serial
from cobs import cobs
import rscp_pb2

class RSCPBridge:
    def __init__(self, port, baud=115200):
        # RS-232 Configuration
        self.ser = serial.Serial(port, baud, timeout=0.01)
        self.buffer = bytearray()

    def send(self, envelope):
        """Wraps and sends any RSCP envelope."""
        data = envelope.SerializeToString()
        encoded = cobs.encode(data)
        self.ser.write(encoded + b'\x00')
        self.ser.flush() # Ensure data is physically sent

    def listen(self, envelope_class, callback):
        """Non-blocking listener for incoming frames."""
        if self.ser.in_waiting > 0:
            data = self.ser.read(self.ser.in_waiting)
            for byte in data:
                if byte == 0x00:
                    try:
                        decoded = cobs.decode(self.buffer)
                        env = envelope_class()
                        env.ParseFromString(decoded)
                        callback(env)
                    except Exception as e:
                        print(f"Decode Error: {e}")
                    self.buffer = bytearray()
                else:
                    self.buffer.append(byte)