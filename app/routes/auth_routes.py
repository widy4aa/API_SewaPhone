from flask import Blueprint, request, jsonify
from app.models.user_model import User
from werkzeug.security import check_password_hash 
from flask_jwt_extended import create_access_token

auth = Blueprint('auth_bp', __name__)

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('pass'):
        return jsonify({"msg": "Username dan password wajib diisi"}), 400

    username = data.get('username')
    password_candidate = data['pass']

    user = User.get_by_username(username)

    if user and check_password_hash(user['pass'], password_candidate):
        user_id_string = str(user['id'])
        access_token = create_access_token(
            identity=user_id_string,
            additional_claims={"role": user["role"]} 
            )

        return jsonify(access_token=access_token)
    
    return jsonify({"messege": "Username atau password salah"}), 401


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