from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route("/chatbot", methods=["POST"])
def chatbot():
    print("POST /chatbot called")
    json_content = request.json
    message = json_content.get("message", "")

    print(f"Message: {message}")

    # Make a POST request to the Ollama service
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "mistral", "prompt": message}
    ).json()

    # Extract the response text
    response_text = "".join([chunk['response'] for chunk in response if 'response' in chunk])

    print(f"Response: {response_text}")

    return jsonify({"answer": response_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
