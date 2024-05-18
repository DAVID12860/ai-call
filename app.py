from flask import Flask, request, jsonify
import sqlite3
import requests

app = Flask(__name__)

DATABASE = 'conversations.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (user_id TEXT, role TEXT, content TEXT)''')
    conn.commit()
    conn.close()

@app.route('/v1/gpt-4o', methods=['POST'])
def gpt_4o():
    try:
        data = request.json
        user_id = data.get('user_id')
        message_content = data.get('message_content')

        # Retrieve past conversations
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT role, content FROM conversations WHERE user_id = ?", (user_id,))
        past_conversations = c.fetchall()
        conn.close()

        # Prepare messages payload
        messages = [{"role": role, "content": content} for role, content in past_conversations]
        messages.append({"role": "user", "content": message_content})

        # Send POST request to Global LLM API
        payload = {
            "messages": messages,
            "model": "gpt-4o"
        }
        response = requests.post('http://api.discord.rocks/ask', json=payload)
        response_data = response.json()

        # Store the new user message and assistant response
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
                  (user_id, 'user', message_content))
        c.execute("INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
                  (user_id, 'assistant', response_data['response']))
        conn.commit()
        conn.close()

        # Return the response from Global LLM API
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
