from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import json

app = Flask(__name__, static_folder='.')

API_KEY = "xai-ztjeUtzA8YSWZZdKtmVAoWNKFTiRu2Dwnq6pIelIDbof183tF0NZJWIOPBLaHjHY1emIRQwxUxZYcJm5"
API_URL = "https://api.x.ai/v1/chat/completions"
KNOWLEDGE_FILE = "knowledge.json"
PRODUCTS_FILE = "products.json"

# Load or initialize knowledge base
def load_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save knowledge base
def save_knowledge(knowledge):
    with open(KNOWLEDGE_FILE, 'w') as f:
        json.dump(knowledge, f, indent=4)

# Load products
def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            return json.load(f)
    return {}

knowledge_base = load_knowledge()
products = load_products()

@app.route('/')
def serve_index():
    print("Root route accessed!")
    print("Current directory:", os.getcwd())
    print("Looking for index.html in:", os.path.join(os.getcwd(), 'index.html'))
    try:
        return send_from_directory('.', 'index.html')
    except FileNotFoundError:
        print("FileNotFoundError: index.html not found")
        return "index.html not found", 404
    except Exception as e:
        print(f"Error serving index.html: {e}")
        return str(e), 500

@app.route('/chat', methods=['POST'])
def chat():
    print("Chat route accessed!")
    try:
        user_message = request.json.get('message')
        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Check product questions
        for product, details in products.items():
            if product in user_message.lower():
                response = f"The {product.replace('-', ' ')} costs {details['price']} with features: {', '.join(details['features'])}."
                return jsonify({"response": response})

        # Check knowledge base
        if user_message.lower() in knowledge_base:
            return jsonify({"response": knowledge_base[user_message.lower()]})

        # Use xAI API if no match
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        data = {"model": "grok-beta", "messages": [{"role": "user", "content": user_message}]}
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        print(f"API Response: {response.status_code} {response.text}")

        if response.status_code == 200:
            grok_response = response.json()['choices'][0]['message']['content']
            knowledge_base[user_message.lower()] = grok_response
            save_knowledge(knowledge_base)
            return jsonify({"response": grok_response})
        else:
            return jsonify({"error": f"API failed with status {response.status_code}: {response.text}"}), response.status_code

    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {e}")
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/train', methods=['POST'])
def train():
    print("Train route accessed!")
    try:
        data = request.json
        question = data.get('question')
        answer = data.get('answer')
        if not question or not answer:
            return jsonify({"error": "Question and answer are required"}), 400
        knowledge_base[question.lower()] = answer
        save_knowledge(knowledge_base)
        return jsonify({"status": "trained", "question": question, "answer": answer})
    except Exception as e:
        print(f"Training error: {e}")
        return jsonify({"error": f"Training failed: {str(e)}"}), 500

@app.route('/test')
def test():
    print("Test route accessed!")
    return "Test route works!"

if __name__ == '__main__':
    app.run(debug=True)