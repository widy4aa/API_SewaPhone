from flask import jsonify
from app.models.user_model import User
from psycopg2 import errors

def read_all_user():
    try:
        users = User.get_all()
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

def read_user(id):
    try:
        users = User.get_by_id(id)
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

def create_user(data):
    try:
        new_user = User.create(data)
        
        if 'pass' in new_user:
            del new_user['pass']

        return jsonify(new_user), 201

    except errors.UniqueViolation as e:
        return jsonify({"error": "Username atau email sudah terdaftar."}), 409 # 

    except Exception as e:
        return jsonify({"error": "Terjadi kesalahan pada server", "details": str(e)}), 500
    
    
def read_user_from_jwt(jwt_identity):
    try:
        user = User.me(jwt_identity)
        user_data = {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "nama": user[3],
            "no_telp": user[4],
            "point": user[5],
            "status": user[6],
            "role": user[7],
        }
        return jsonify(user_data)
    except Exception as e:
        return jsonify({"error": "Terjadi kesalahan pada server", "details": str(e)}), 500
    
    
def update_user_profile(user_id,data):
    try:
        for field in ['pass', 'point', 'role', 'status', 'id']:
            if field in data:
                del data[field]
        
        if not data:
            return jsonify({"success": False, "error": "Tidak ada data valid untuk diperbarui."}), 400

        response, status_code = User.edit(user_id, data)

        if response.get("success") and 'user' in response and 'pass' in response['user']:
            del response['user']['pass']
            
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"success": False, "error": "Terjadi kesalahan internal pada server", "details": str(e)}), 500
