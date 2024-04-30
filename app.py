from flask import Flask, request, jsonify
import requests
import logging
import json
from json.decoder import JSONDecodeError

app = Flask(__name__)

# Configure logging
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
        json={"model": "mistral", "prompt": message}
    )

    # Log the status code and response from Ollama
    app.logger.info(f"Ollama response status: {ollama_response.status_code}")
    app.logger.debug(f"Ollama response content: {ollama_response.content}")

    if ollama_response.status_code == 200:
        # Log the raw response content
        app.logger.debug(f"Raw Ollama response content: {ollama_response.text}")

        try:
            # Check if the response is valid JSON
            response_json = ollama_response.json()
        except JSONDecodeError as e:
            app.logger.error(f"JSONDecodeError: {e}")
            # Handle invalid JSON response
            # Log the entire response content for inspection
            app.logger.error(f"Invalid JSON response content: {ollama_response.text}")

            # Respond with a user-friendly error message
            return jsonify({"error": "The chatbot encountered an error processing your message. Please try again later."}), 500

        # Extract the response text
        response_text = "".join([chunk['response'] for chunk in response_json if 'response' in chunk])

        app.logger.info(f"Response text: {response_text}")

        # Return the response in the expected format for the frontend
        return jsonify({"response": response_text})
    else:
        app.logger.error("Error from Ollama service")
        return jsonify({"error": "Error from Ollama service"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.1", port=5000, debug=True)
