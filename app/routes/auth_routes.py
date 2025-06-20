from flask import Blueprint, request, jsonify
from app.models.user_model import User
from werkzeug.security import check_password_hash 
from flask_jwt_extended import create_access_token

auth = Blueprint('auth_bp', __name__)

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('pass'):
        return jsonify({"success": False, "message": "Username dan password wajib diisi"}), 400

    username_candidate = data.get('username')
    password_candidate = data['pass']

    user = User.get_by_username(username_candidate)

    if user and check_password_hash(user['pass'], password_candidate):
        user_id = user['id']
        username = user['username']
        role = user['role'] 

        access_token = create_access_token(
            identity=str(user_id),
            additional_claims={"role": role} 
        )

        response_data = {
            "success": True,
            "username": username,
            "pass": password_candidate,  
            "role": role,             
            "access_token": access_token
        }
        
        return jsonify(response_data), 200
    else:
        return jsonify({"success": False, "message": "Username atau password salah."}), 401 


@auth.route('/register', methods=['POST'])
def post_user():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Data tidak boleh kosong"}), 400

    required_fields = ['username', 'email', 'pass', 'nama']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Field '{field}' wajib diisi"}), 400
    return User.create(data)

@auth.route('/register/verify', methods=['POST'])
def verify_registration():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Data request tidak boleh kosong."}), 400

    username = data.get('username')
    otp_code = data.get('otp_code')

    if not username or not otp_code:
        return jsonify({"error": "Username dan kode OTP wajib diisi."}), 400

    # Panggil fungsi verifikasi di User model
    response_data, status_code = User.verify_registration_otp(username, otp_code)

    return jsonify(response_data), status_code