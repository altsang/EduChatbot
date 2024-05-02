from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import requests
import logging
import json

app = Flask(__name__)
# Set CORS to allow requests from any origin
cors = CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging to display info messages and output them to a file
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('app.log', 'a')])

# Configure SocketIO with explicit CORS policy to match Flask-CORS
socketio = SocketIO(app, cors_allowed_origins="*")

# URLs for educational content
image_url = "https://scratch.mit.edu/projects/10128407/"  # An example Scratch project image
video_url = "https://www.youtube.com/watch?v=khXVGYi6gqE"  # A YouTube video explaining programming basics
audio_url = "https://placeholder-audio-for-educhatbot.com/audio.mp3"  # Placeholder for text-to-speech audio explaining a programming concept
interactive_url = "https://scratch.mit.edu/projects/10128407/"  # An example Scratch project for interactive coding

@socketio.on('message')
def handle_message(data):
    global video_url, image_url, audio_url, interactive_url
    app.logger.info(f"Received data: {data}")

    if not isinstance(data, dict):
        app.logger.error("Received data is not a dictionary")
        return

    app.logger.info(f"Received message: {data}")
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

    app.logger.info(f"Response type determined: {response_type}")

    # Log the current value of content_url
    app.logger.info(f"Current value of content_url: {content_url}")

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
        socketio.emit('message', {"error": "Request to Ollama service failed"})
        return
    except Exception as e:
        app.logger.error(f"Unexpected error when making request to Ollama service: {e}")
        socketio.emit('message', {"error": "Unexpected error when making request to Ollama service"})

    # Check if the request was successful
    if ollama_response.status_code != 200:
        app.logger.error(f"Non-200 status code received from Ollama service: {ollama_response.status_code}")
        socketio.emit('message', {"error": "Error from Ollama service"})
        return

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

                app.logger.info(f"Ollama response data received: {response_data}")

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
            socketio.emit('message', {"error": "No 'response' field in Ollama response JSON"})
            return

        # If the response is not marked as done, log an error and return an error message
        if not done:
            app.logger.error("Ollama response not marked as done")
            socketio.emit('message', {"error": "Incomplete response from Ollama"})
            return

        # Based on the response type, emit the appropriate content
        if response_type == "text":
            print(f"Emitting message to frontend: type={response_type}, response={full_response_text}")
            socketio.emit('message', {"response": full_response_text, "type": "text"})
        elif response_type == "image":
            print(f"Emitting message to frontend: type={response_type}, response={content_url}")
            socketio.emit('message', {"response": image_url, "type": "image"})
        elif response_type == "video":
            # Global declaration of the video_url variable
            global video_url
            # Ensure the global video_url is used
            if video_url is None:
                app.logger.error("video_url is not defined")
                socketio.emit('message', {"error": "Video URL is not defined"})
                return
            print(f"Emitting message to frontend: type={response_type}, response={video_url}")
            socketio.emit('message', {"response": video_url, "type": "video"})
        elif response_type == "audio":
            print(f"Emitting message to frontend: type={response_type}, response={content_url}")
            socketio.emit('message', {"response": audio_url, "type": "audio"})
        elif response_type == "interactive":
            print(f"Emitting message to frontend: type={response_type}, response={content_url}")
            socketio.emit('message', {"response": interactive_url, "type": "interactive"})
    except json.JSONDecodeError as e:
        app.logger.error(f"JSONDecodeError: {e}")
        socketio.emit('message', {"error": "JSON decode error in Ollama response"})
    except Exception as e:
        app.logger.error(f"Error processing Ollama response: {e}")
        socketio.emit('message', {"error": "The chatbot encountered an error processing your message. Please try again later."})

# Log the response headers for debugging CORS issues
@app.after_request
def after_request_func(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
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

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
