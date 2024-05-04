from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import requests
import logging
import json
import subprocess
import uuid

app = Flask(__name__)

# Configure SocketIO with CORS headers explicitly set for all origins
socketio = SocketIO(app, cors_allowed_origins="*", cors_credentials=True, logger=True, engineio_logger=True, manage_session=False, ping_timeout=120, ping_interval=60)

# Configure logging to display info messages and output them to a file
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('app.log', 'a')])

# URLs for educational content
image_url = "https://scratch.mit.edu/projects/10128407/"  # An example Scratch project image
video_url = "https://www.youtube.com/watch?v=_j4Lj-BT00g"  # A YouTube video explaining programming basics for kids
audio_url = "/audio/placeholder_audio.mp3"  # URL path for chatbot audio response demonstration
interactive_url = "https://scratch.mit.edu/projects/10128407/"  # An example Scratch project for interactive coding

import os
import uuid
import subprocess

def generate_audio_response(text_response):
    # Generate a unique filename for the audio response
    filename = f"{uuid.uuid4()}.mp3"
    filepath = f"audio/{filename}"

    # Use espeak to generate the audio file from the text response
    subprocess.run(['espeak', text_response, '--stdout'], stdout=open(filepath, 'wb'))

    # Retrieve the current ngrok URL from an environment variable
    ngrok_url = os.getenv('NGROK_URL')

    # Construct the full URL path for the audio file using the current ngrok URL
    full_audio_url = f"{ngrok_url}/audio/{filename}"

    # Return the full URL path to the audio file
    return full_audio_url

@socketio.on('message')
def handle_message(data):
    app.logger.info(f"Received data: {data}")  # Log the received data

    if not isinstance(data, dict):
        app.logger.info("Received data is not a dictionary")  # Log if data is not a dictionary
        return

    message = data.get("message", "")
    app.logger.info(f"Received message: {message}")  # Log the received message

    # Determine the type of response needed based on the message
    response_type = "text"  # Default response type
    content_url = None  # Initialize content URL to None
    child_friendly = "explain like I'm 10" if "for kids" in message.lower() else ""
    if "picture" in message.lower():
        response_type = "image"
        content_url = image_url
    elif "explain" in message.lower() or "what is" in message.lower():
        response_type = "video"
        content_url = video_url
    elif "listen" in message.lower():
        response_type = "audio"
        content_url = audio_url
    elif "play" in message.lower():
        response_type = "interactive"
        content_url = interactive_url
    elif "example of a python program" in message.lower() or "show me python code" in message.lower():
        response_type = "text"
        content_url = "Here is a simple Python program: \n\n```python\nprint('Hello, World!')\n```"

    app.logger.info(f"Determined response type: {response_type}")  # Log the determined response type
    app.logger.info(f"Content URL or message to send: {content_url or message}")  # Log the content URL or message to send

    # Log the value of video_url before using it
    app.logger.info(f"video_url value before emit: {video_url}")

    # Emit the response back to the client
    socketio.emit('response', {'response': content_url or message, 'type': response_type})
    app.logger.info(f"Emitted response: {content_url or message}, Type: {response_type}")  # Log the emitted response

    # Rest of the function code remains unchanged...

@socketio.on('connect')
def handle_connect():
    app.logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    app.logger.info(f"Client disconnected: {request.sid}")

@socketio.on('ping')
def handle_ping():
    app.logger.info('Ping received from client')
    # Respond with a pong to keep the connection alive
    socketio.emit('pong')

@socketio.on('pong')
def handle_pong():
    app.logger.info('Pong received from client')

@socketio.on('pong')
def handle_pong():
    app.logger.info('Pong sent to client')

@app.after_request
def after_request_func(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin') or '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'

    app.logger.info(f"Setting CORS headers for origin: {request.headers.get('Origin') or '*'}")
    app.logger.info(f"Access-Control-Allow-Methods: {response.headers['Access-Control-Allow-Methods']}")
    app.logger.info(f"Access-Control-Allow-Headers: {response.headers['Access-Control-Allow-Headers']}")
    app.logger.info(f"Access-Control-Allow-Credentials: {response.headers['Access-Control-Allow-Credentials']}")

    return response

@app.route("/chatbot", methods=["POST"])
def chatbot():
    app.logger.info("POST /chatbot called")
    json_content = request.json
    message = json_content.get("message", "")

    app.logger.info(f"Received message: {message}")

    # Determine the type of response needed based on the message
    response_type = "text"  # Default response type
    child_friendly = "explain like I'm 10" if "for kids" in message.lower() else ""
    if "picture" in message.lower():
        response_type = "image"
    elif "explain" in message.lower() or "what is" in message.lower():
        response_type = "video"
    elif "listen" in message.lower() or "audio explanation" in message.lower():
        response_type = "audio"
    elif "play" in message.lower():
        response_type = "interactive"

    app.logger.info(f"Determined response type: {response_type}")

    # Construct the prompt for the Ollama service
    prompt = f"{child_friendly} {message}"
    app.logger.info(f"Constructed prompt for Ollama: {prompt}")

    # Make a POST request to the Ollama service
    try:
        ollama_response = requests.post(
            "http://172.17.0.1:11434/api/generate",
            json={"model": "mistral:latest", "prompt": prompt},
            stream=True
        )
        app.logger.info(f"Ollama response status code: {ollama_response.status_code}")
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request to Ollama service failed: {e}")
        return jsonify({"error": "Request to Ollama service failed"}), 500

    # Check if the request was successful
    if ollama_response.status_code != 200:
        app.logger.error(f"Non-200 status code received from Ollama service: {ollama_response.status_code}")
        return jsonify({"error": "Error from Ollama service"}), ollama_response.status_code

    # Process the successful response from Ollama
    try:
        # Read the response content and decode as JSON
        response_content = ollama_response.content.decode('utf-8')
        app.logger.info(f"Ollama response content received: {response_content}")

        # Find the end of the first JSON object and slice the content
        end_of_first_json_object = response_content.find('}') + 1
        response_data = json.loads(response_content[:end_of_first_json_object])
        app.logger.info(f"Ollama response data: {response_data}")

        # Check if the response is complete
        if not response_data.get('done', False):
            app.logger.error("Ollama response not marked as done")
            return jsonify({"error": "Incomplete response from Ollama"}), 500

        # Extract the 'response' field from the JSON data
        response_text = response_data.get('response', "")
        app.logger.info(f"Ollama response text: {response_text}")

        # Based on the response type, return the appropriate content
        if response_type == "text":
            response = jsonify({"response": response_text, "type": "text"})
        elif response_type == "image":
            response = jsonify({"response": image_url, "type": "image"})
        elif response_type == "video":
            response = jsonify({"response": video_url, "type": "video"})
        elif response_type == "audio":
            # Generate the audio response and update the audio_url with the full URL path
            audio_url = generate_audio_response(response_text)
            response = jsonify({"response": audio_url, "type": "audio"})
        elif response_type == "interactive":
            response = jsonify({"response": interactive_url, "type": "interactive"})
        app.logger.info(f"Sending response: {response.get_json()}")
        return response
    except json.JSONDecodeError as e:
        app.logger.error(f"JSONDecodeError: {e}")
        response = jsonify({"error": "JSON decode error in Ollama response"})
        return response, 500
    except Exception as e:
        app.logger.error(f"Error processing Ollama response: {e}")
        response = jsonify({"error": "The chatbot encountered an error processing your message. Please try again later."})
        return response, 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    app.logger.info(f"Serving audio file: {filename}")
    try:
        # Attempt to serve the file from the 'audio' directory
        response = send_from_directory('audio', filename)
        app.logger.info(f"Audio file served: {filename}")
        return response
    except FileNotFoundError:
        # Log an error message if the file is not found
        app.logger.error(f"Audio file not found: {filename}")
        return jsonify({"error": "Audio file not found"}), 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists("frontend/build/" + path):
        return send_from_directory('frontend/build', path)
    else:
        return send_from_directory('frontend/build', 'index.html')

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
