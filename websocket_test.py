import websocket
import threading
import ssl
import json

def on_message(ws, message):
    print(f"Received message: {message}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        # Send a message that prompts an interactive response from the chatbot
        message_data = {"message": "play with the code example"}
        ws.send(json.dumps(message_data))
        # Stop the timer after sending the message
        # threading.Timer(1, run).start()

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://d5b182dfa921.ngrok.app/socket.io/?EIO=4&transport=websocket",
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
