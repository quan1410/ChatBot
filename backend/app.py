from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    question = data.get('question', '')
    # Mocked legal answer
    answer = f"Bạn hỏi: '{question}'. Đây là câu trả lời mẫu về luật."
    return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(debug=True)