from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/chatbot', methods=['POST'])
def chatbot():
    # Placeholder for chatbot logic
    data = request.get_json()
    user_message = data.get('message', '')
    # Placeholder response
    return jsonify({'response': 'Hello, I am the EduChatbot. How can I help you learn programming today?', 'user_message': user_message})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
