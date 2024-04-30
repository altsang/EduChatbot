from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import json

app = Flask(__name__)
CORS(app)

# Configure logging to display debug messages
logging.basicConfig(level=logging.DEBUG)

@app.route("/chatbot", methods=["POST"])
def chatbot():
    app.logger.info("POST /chatbot called")
    json_content = request.json
    message = json_content.get("message", "")

    app.logger.info(f"Received message: {message}")

    # Make a POST request to the Ollama service
    ollama_response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "mistral:latest", "prompt": message},
        stream=True
    )

    # Log the status code and response from Ollama
    app.logger.info(f"Ollama response status: {ollama_response.status_code}")
    app.logger.debug(f"Ollama response headers: {ollama_response.headers}")

    if ollama_response.status_code == 200:
        try:
            # Read the response line by line and process each line as a separate JSON object
            response_lines = ollama_response.iter_lines()
            full_response_text = ""
            json_buffer = ""
            for line in response_lines:
                if line:  # filter out keep-alive new lines
                    json_buffer += line.decode('utf-8')
                    # Check if the buffer has a complete JSON object
                    if json_buffer.strip().endswith('}'):
                        try:
                            response_data = json.loads(json_buffer)
                            app.logger.debug(f"Ollama response data: {response_data}")

                            # Extract the 'response' field from the JSON data
                            if 'response' in response_data:
                                response_text = response_data['response']
                                full_response_text += response_text
                                app.logger.debug(f"Ollama response text: {response_text}")

                                # Check if the response is complete
                                if response_data.get('done', False):
                                    # Return the full response in the expected format for the frontend
                                    return jsonify({"response": full_response_text})
                            # Clear the buffer after successfully decoding a JSON object
                            json_buffer = ""
                        except json.JSONDecodeError as e:
                            # Log the error and the state of json_buffer
                            app.logger.error(f"JSONDecodeError: {e}")
                            app.logger.debug(f"Current json_buffer: {json_buffer}")
                            # If JSON is incomplete, continue accumulating
                            continue

            # If no 'response' field is present in any line, log an error and return an error message
            app.logger.error("No 'response' field in any line of Ollama response")
            return jsonify({"error": "No 'response' field in Ollama response JSON"}), 500

        except Exception as e:
            app.logger.error(f"Error processing Ollama response: {e}")
            # Handle any other errors
            return jsonify({"error": "The chatbot encountered an error processing your message. Please try again later."}), 500
    else:
        app.logger.error("Error from Ollama service")
        return jsonify({"error": "Error from Ollama service"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.1", port=5000, debug=True)
