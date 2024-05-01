from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import json

app = Flask(__name__)
# Set CORS to allow all origins
CORS(app, resources={r"/chatbot": {"origins": "*"}})

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
    if "picture" in message.lower():
        response_type = "image"
    elif "explain" in message.lower():
        response_type = "video"
    elif "listen" in message.lower():
        response_type = "audio"
    elif "play" in message.lower():
        response_type = "interactive"

    # Make a POST request to the Ollama service
    try:
        ollama_response = requests.post(
            "http://172.17.0.1:11434/api/generate",
            json={"model": "mistral:latest", "prompt": message},
            stream=True
        )
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request to Ollama service failed: {e}")
        return jsonify({"error": "Request to Ollama service failed"}), 500

    # Log the status code and response from Ollama
    app.logger.info(f"Ollama response status: {ollama_response.status_code}")
    app.logger.debug(f"Ollama response headers: {ollama_response.headers}")

    if ollama_response.status_code == 200:
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
                    # For demonstration, return a placeholder image URL
                    return jsonify({"response": "https://via.placeholder.com/150", "type": "image"})
                elif response_type == "video":
                    # For demonstration, return a placeholder video URL
                    return jsonify({"response": "https://www.example.com/placeholder-video.mp4", "type": "video"})
                elif response_type == "audio":
                    # For demonstration, return a placeholder audio URL
                    return jsonify({"response": "https://www.example.com/placeholder-audio.mp3", "type": "audio"})
                elif response_type == "interactive":
                    # For demonstration, return a placeholder interactive URL
                    return jsonify({"response": "https://www.example.com/placeholder-interactive", "type": "interactive"})
        except json.JSONDecodeError as e:
            app.logger.error(f"JSONDecodeError: {e}")
            return jsonify({"error": "JSON decode error in Ollama response"}), 500
        except Exception as e:
            app.logger.error(f"Error processing Ollama response: {e}")
            # Handle any other errors
            return jsonify({"error": "The chatbot encountered an error processing your message. Please try again later."}), 500
    else:
        app.logger.error(f"Non-200 status code received from Ollama service: {ollama_response.status_code}")
        app.logger.debug(f"Non-200 response content: {ollama_response.content}")
        # Add detailed error logging for non-200 status code responses
        try:
            error_content = ollama_response.json()
            app.logger.error(f"Ollama error response content: {error_content}")
        except json.JSONDecodeError:
            app.logger.error("Failed to decode Ollama error response as JSON")
        return jsonify({"error": "Error from Ollama service"}), ollama_response.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
