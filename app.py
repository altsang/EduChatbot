from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging

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
            # Read the entire response text
            response_text = ollama_response.text
            app.logger.debug(f"Ollama full response text: {response_text}")

            # Split the response by new lines and parse each line as a separate JSON object
            response_lines = response_text.strip().split('\n')
            for line in response_lines:
                app.logger.debug(f"Processing line: {line}")
                response_object = json.loads(line)
                if 'response' in response_object:
                    response_text = response_object['response']
                    app.logger.debug(f"Ollama response text: {response_text}")
                    # Return the response in the expected format for the frontend
                    return jsonify({"response": response_text})

            # If no valid 'response' found, return an error message
            return jsonify({"error": "No valid response found in Ollama service output."}), 500
        except Exception as e:
            app.logger.error(f"Error processing Ollama response: {e}")
            # Handle any other errors
            return jsonify({"error": "The chatbot encountered an error processing your message. Please try again later."}), 500
    else:
        app.logger.error("Error from Ollama service")
        return jsonify({"error": "Error from Ollama service"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.1", port=5000, debug=True)
