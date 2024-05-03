from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
import requests
import logging
import json
import subprocess
import uuid

app = Flask(__name__)
# Set CORS to allow requests from any origin
cors = CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging to display info messages and output them to a file
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('app.log', 'a')])

# Configure SocketIO with CORS headers explicitly set for all routes and custom ping settings
socketio = SocketIO(app, cors_allowed_origins="*", cors_credentials=True, logger=True, engineio_logger=True, manage_session=False, ping_timeout=120, ping_interval=60)

# URLs for educational content
image_url = "https://scratch.mit.edu/projects/10128407/"  # An example Scratch project image
video_url = "https://www.youtube.com/watch?v=_j4Lj-BT00g"  # A YouTube video explaining programming basics for kids
audio_url = "/audio/placeholder_audio.mp3"  # URL path for chatbot audio response demonstration
interactive_url = "https://scratch.mit.edu/projects/10128407/"  # An example Scratch project for interactive coding

def generate_audio_response(text_response):
    # Generate a unique filename for the audio response
    filename = f"{uuid.uuid4()}.mp3"
    filepath = f"audio/{filename}"

    # Use espeak to generate the audio file from the text response
    subprocess.run(['espeak', text_response, '--stdout'], stdout=open(filepath, 'wb'))

    # Return the relative path to the audio file
    return f"/audio/{filename}"

@socketio.on('message')
def handle_message(data):
    app.logger.info(f"Received data: {data}")

    if not isinstance(data, dict):
        app.logger.error("Received data is not a dictionary")
        return

    message = data.get("message", "")
    app.logger.info(f"Received message: {message}")

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

@socketio.on('pong')
def handle_pong():
    app.logger.info('Pong sent to client')

# Log the response headers for debugging CORS issues
@app.after_request
def after_request_func(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    app.logger.info(f"Headers set: {response.headers}")
    return response
@app.route("/chatbot", methods=["POST"])
def chatbot():
    app.logger.info("POST /chatbot called")
    json_content = request.json
    message = json_content.get("message", "")

    app.logger.info(f"Received message: {message}")

    # Ensure video_url is defined before using it
    if 'video_url' not in globals():
        video_url = "https://www.youtube.com/watch?v=_j4Lj-BT00g"  # A YouTube video explaining programming basics for kids

    # Determine the type of response needed based on the message
    response_type = "text"  # Default response type
    child_friendly = "explain like I'm 10" if "for kids" in message.lower() else ""
    if "picture" in message.lower():
        response_type = "image"
    elif "explain" in message.lower() or "what is" in message.lower():
        response_type = "video"
    elif "listen" in message.lower():
        response_type = "audio"
    elif "play" in message.lower():
        response_type = "interactive"

    # Construct the prompt for the Ollama service
    prompt = f"{child_friendly} {message}"

    # Make a POST request to the Ollama service
    try:
        ollama_response = requests.post(
            "http://172.17.0.1:11434/api/generate",
            json={"model": "mistral:latest", "prompt": prompt},
            stream=True
        )
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request to Ollama service failed: {e}")
        return jsonify({"error": "Request to Ollama service failed"}), 500

    # Check if the request was successful
    if ollama_response.status_code != 200:
        app.logger.error(f"Non-200 status code received from Ollama service: {ollama_response.status_code}")
        return jsonify({"error": "Error from Ollama service"}), ollama_response.status_code

    # Process the successful response from Ollama
    # Log the status code and response from Ollama
    app.logger.info(f"Ollama response status: {ollama_response.status_code}")
    app.logger.debug(f"Ollama response headers: {ollama_response.headers}")

    try:
        # Read the response line by line and process each line as a separate JSON object
        response_lines = ollama_response.iter_lines()
        full_response_text = ""
        done = False
        for line in response_lines:
            if line:  # filter out keep-alive new lines
                # Decode each line as a separate JSON object
                response_data = json.loads(line.decode('utf-8'))
                app.logger.debug(f"Ollama response data: {response_data}")

                # Extract the 'response' field from the JSON data
                if 'response' in response_data:
                    response_text = response_data['response']
                    full_response_text += response_text
                    app.logger.debug(f"Ollama response text: {response_text}")

                    # Check if the response is complete
                    if response_data.get('done', False):
                        done = True
                        break

        # If no 'response' field is present in any line, log an error and return an error message
        if not full_response_text:
            app.logger.error("No 'response' field in any line of Ollama response")
            return jsonify({"error": "No 'response' field in Ollama response JSON"}), 500

        # If the response is not marked as done, log an error and return an error message
        if not done:
            app.logger.error("Ollama response not marked as done")
            return jsonify({"error": "Incomplete response from Ollama"}), 500

        # Based on the response type, return the appropriate content
        if response_type == "text":
            response = jsonify({"response": full_response_text, "type": "text"})
        elif response_type == "image":
            response = jsonify({"response": image_url, "type": "image"})
        elif response_type == "video":
            response = jsonify({"response": video_url, "type": "video"})
        elif response_type == "audio":
            # Generate the audio response and update the audio_url
            audio_url = generate_audio_response(full_response_text)
            response = jsonify({"response": audio_url, "type": "audio"})
        elif response_type == "interactive":
            response = jsonify({"response": interactive_url, "type": "interactive"})
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

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
