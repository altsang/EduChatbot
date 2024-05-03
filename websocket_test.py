import socketio

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print("Connected to the server.")
    sio.emit('message', {'message': 'play with the code example'})

@sio.event
def message(data):
    print(f"Received message: {data}")
    sio.disconnect()

@sio.event
def disconnect():
    print("Disconnected from the server.")

if __name__ == "__main__":
    sio.connect("https://d5b182dfa921.ngrok.app")
