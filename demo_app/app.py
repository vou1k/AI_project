"""
Demo Flask application for testing
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

# Test database
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"}
}

items = [
    {"id": 1, "name": "Item 1", "price": 100},
    {"id": 2, "name": "Item 2", "price": 200},
    {"id": 3, "name": "Item 3", "price": 300}
]

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({"status": "ok", "message": "API is working"})

@app.route('/api/login', methods=['POST'])
def login():
    """User authentication"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing credentials"}), 400
    
    username = data['username']
    password = data['password']
    
    if username in users and users[username]['password'] == password:
        return jsonify({
            "token": f"token_{username}",
            "role": users[username]['role']
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/items', methods=['GET'])
def get_items():
    """Get list of items"""
    auth = request.headers.get('Authorization')
    
    if not auth or not auth.startswith('token_'):
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify(items), 200

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get item by ID"""
    auth = request.headers.get('Authorization')
    
    if not auth or not auth.startswith('token_'):
        return jsonify({"error": "Unauthorized"}), 401
    
    item = next((i for i in items if i['id'] == item_id), None)
    
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify(item), 200

@app.route('/api/items', methods=['POST'])
def create_item():
    """Create new item (admin only)"""
    auth = request.headers.get('Authorization')
    
    if not auth or not auth.startswith('token_'):
        return jsonify({"error": "Unauthorized"}), 401
    
    # Check admin rights
    username = auth.replace('token_', '')
    if users.get(username, {}).get('role') != 'admin':
        return jsonify({"error": "Forbidden"}), 403
    
    data = request.get_json()
    
    if not data or 'name' not in data or 'price' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    new_item = {
        "id": len(items) + 1,
        "name": data['name'],
        "price": data['price']
    }
    items.append(new_item)
    
    return jsonify(new_item), 201

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("Demo application started at http://localhost:5000")
    print("Available endpoints:")
    print("  GET  /api/test - API check")
    print("  POST /api/login - authentication")
    print("  GET  /api/items - list items")
    print("  GET  /api/items/<id> - item by ID")
    print("  POST /api/items - create item (admin only)")
    print("=" * 50)
    app.run(debug=True, port=5000)