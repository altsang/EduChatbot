from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import json

app = Flask(__name__)
# Set CORS to allow requests from the specific frontend origin
CORS(app, resources={r"/chatbot": {"origins": "http://localhost:3000"}})

# Configure logging to display debug messages
logging.basicConfig(level=logging.DEBUG)

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

    # URLs for educational content
    image_url = "https://scratch.mit.edu/projects/10128407/"  # An example Scratch project image
    video_url = "https://www.youtube.com/watch?v=khXVGYi6gqE"  # A YouTube video explaining programming basics
    audio_url = "https://placeholder-audio-for-educhatbot.com/audio.mp3"  # Placeholder for text-to-speech audio explaining a programming concept
    interactive_url = "https://scratch.mit.edu/projects/10128407/"  # An example Scratch project for interactive coding

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
                        # Return the full response in the expected format for the frontend
                        app.logger.debug(f"Full Ollama response text: {full_response_text}")
                        break

        # If no 'response' field is present in any line, log an error and return an error message
        if not full_response_text:
            app.logger.error("No 'response' field in any line of Ollama response")
            return jsonify({"error": "No 'response' field in Ollama response JSON"}), 500
        else:
            # Based on the response type, return the appropriate content
            if response_type == "text":
                return jsonify({"response": full_response_text, "type": "text"})
            elif response_type == "image":
                return jsonify({"response": image_url, "type": "image"})
            elif response_type == "video":
                return jsonify({"response": video_url, "type": "video"})
            elif response_type == "audio":
                return jsonify({"response": audio_url, "type": "audio"})
            elif response_type == "interactive":
                return jsonify({"response": interactive_url, "type": "interactive"})
    except json.JSONDecodeError as e:
        app.logger.error(f"JSONDecodeError: {e}")
        return jsonify({"error": "JSON decode error in Ollama response"}), 500
    except Exception as e:
        app.logger.error(f"Error processing Ollama response: {e}")
        # Handle any other errors
        return jsonify({"error": "The chatbot encountered an error processing your message. Please try again later."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
