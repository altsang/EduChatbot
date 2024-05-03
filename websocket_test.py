import socketio
import time

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print("Connected to the server.")
    sio.emit('message', {'message': 'play with the code example'})

@sio.event
def message(data):
    print(f"Received message: {data}")

@sio.event
def response(data):
    print(f"Received response: {data}")
    # Wait for a bit before disconnecting to ensure all messages are received
    time.sleep(5)
    sio.disconnect()

@sio.event
def disconnect():
    print("Disconnected from the server.")

if __name__ == "__main__":
    sio.connect("https://fceb70a59f1d.ngrok.app")
