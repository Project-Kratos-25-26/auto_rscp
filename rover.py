import time
import argparse
import rscp_pb2
from rscp_bridge import RSCPBridge

class Rover:
    def __init__(self, port):
        self.bridge = RSCPBridge(port)
        self.state = rscp_pb2.DISARMED
        self.last_telemetry = 0
        
        # Navigation State
        self.is_driving = False
        self.drive_start_time = 0
        self.drive_duration = 2.0

    def handle_request(self, request):
        req_type = request.WhichOneof('request')
        
        # 1. ALWAYS ACKNOWLEDGE IMMEDIATELY
        ack = rscp_pb2.ResponseEnvelope()
        ack.acknowledge.SetInParent()
        self.bridge.send(ack)

        if req_type == 'navigate_to_gps':
            print(f"Command: Navigate to {request.navigate_to_gps.coordinate.latitude}")
            self.is_driving = True
            self.drive_start_time = time.time()
            self.state = rscp_pb2.AUTONOMOUS

    def update(self):
        """Non-blocking updates for telemetry and tasks."""
        # 1. 1Hz Telemetry Loop
        if time.time() - self.last_telemetry >= 1.0:
            env = rscp_pb2.ResponseEnvelope()
            env.rover_status.state = self.state
            env.rover_status.coordinate.latitude = 39.8712
            env.rover_status.battery_state.state_of_charge = 0.85
            self.bridge.send(env)
            self.last_telemetry = time.time()

        # 2. Check Task Completion (Simulation)
        if self.is_driving and (time.time() - self.drive_start_time >= self.drive_duration):
            print("Target reached!")
            done = rscp_pb2.ResponseEnvelope()
            done.task_finished.SetInParent()
            self.bridge.send(done)
            self.is_driving = False
            self.state = rscp_pb2.DISARMED

    def run(self):
        while True:
            self.bridge.listen(rscp_pb2.RequestEnvelope, self.handle_request)
            self.update()
            time.sleep(0.01)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True)
    Rover(parser.parse_args().port).run()