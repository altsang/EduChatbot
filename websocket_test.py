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
    # Wait indefinitely until a response is received
    # time.sleep(10)
    # sio.disconnect()

@sio.event
def disconnect():
    print("Disconnected from the server.")

if __name__ == "__main__":
    sio.connect("https://6340ace5b863.ngrok.app")  # Updated to the correct ngrok URL for the backend service
    # Keep the client running to listen for the response
    sio.wait()
