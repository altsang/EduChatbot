from flask import Flask, request, jsonify
from langchain.llms import OpenAI

app = Flask(__name__)
llm = OpenAI()

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    user_message = data.get('message', '')
    
    # Use Langchain to process the message and generate a response
    response = llm.complete(prompt=user_message, max_tokens=150)

    return jsonify({'response': response, 'user_message': user_message})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
