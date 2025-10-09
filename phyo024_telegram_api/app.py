from flask import Flask, jsonify, abort, request
from functools import wraps

app = Flask(__name__)

# Save a secret API Key 
API_KEY = "MMDT-SECRET-TELEGRAM-BOT-KEY"

# Storing sample users data using dictionary format
users = {
    1: {"name": "Aung Aung", "email": "aung@mmdt.com", "registered_date": "2025-10-01"},
    2: {"name": "Ma Ma", "email": "mama@mmdt.com", "registered_date": "2025-10-03"},
    3: {"name": "Ko Ko", "email": "koko@mmdt.com", "registered_date": "2025-10-05"},
    4: {"name": "Aries", "email": "aries87@mmdt.com", "registered_date": "2025-10-10"},
    5: {"name": "Phyo", "email": "phyo024@mmdt.com", "registered_date": "2025-10-08"},
}

# --- Authentication Decorator ---
# Write a function to check token before running API endpoint 
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check request header whether 'Authorization' include or not!
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # 'Bearer <token>' : extract token from the format 
                token = auth_header.split(" ")[1]
            except IndexError:
                abort(401, description="Bearer token malformed.")

        # Show 401 Unauthorized error if the token does not include or wrong token
        if not token or token != API_KEY:
            abort(401, description="Unauthorized access. Invalid or missing token.")
        
        # Run the endpoint function if the token is correct 
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def home():
    return "Welcome to MMDT User API!"

# GET /api/users/<user_id> endpoint
@app.route('/api/users/<int:user_id>', methods=['GET'])
@token_required  # protect endpoint with token_required decorator
def get_user(user_id):
    user = users.get(user_id)
    if not user:
        abort(404, description=f"User with ID {user_id} not found.")
    return jsonify(user)


if __name__ == '__main__':
    app.run(debug=True)