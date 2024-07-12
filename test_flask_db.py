from datetime import datetime
from flask import Flask, request, jsonify
import os
from openai import OpenAI

from memory.ai_db import get_information

app = Flask(__name__)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_API_BASE"),
)

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('query')
    if user_input is None:
        return jsonify({'error': 'No query provided'}), 400

    time_start = datetime.now()
    
    ai_response = get_information(client, message=user_input)
    
    time_end = datetime.now()
    duration = round((time_end - time_start).total_seconds(), 2)
    
    return jsonify({'response': ai_response, 'duration': f"{duration}s"})

if __name__ == '__main__':
    app.run(port=5001)
