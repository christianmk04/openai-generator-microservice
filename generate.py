from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai
import requests
import os 

app = Flask(__name__)
CORS(app)

# GENERATE CHAT COMPLETION
@app.route('/generate_chat_completion/<string:user_api_key>', methods=['POST'])
def generate_cs(user_api_key):

    request_data = request.get_json()

    openai.api_key = user_api_key
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=request_data['messages'],
        max_tokens=2048,
        temperature=1.1,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    return jsonify(
        {
            'response': completion,
            'code' : 200,
            'message' : 'Successfully generated prompt for chat completion'
        }
    )

# FLASK APP ROUTE
if __name__ == '__main__':
    app.run(port=5002, debug=True)