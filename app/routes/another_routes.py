from flask import Blueprint, request, jsonify
from app.controllers.helper_controller import process_otp_request, process_otp_verification

another = Blueprint('another', __name__)

@another.route('/otp/request', methods=['POST'])
def request_otp_route():
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({"error": "username diperlukan"}), 400

    username = data['username']
    
    success, message, status_code = process_otp_request(username)
    
    if success:
        return message, status_code
    else:
        return message, status_code

@another.route('/otp/verify', methods=['POST'])
def verify_otp_route():
    data = request.get_json()
    if not data or 'email' not in data or 'otp' not in data:
        return jsonify({"error": "Email dan OTP diperlukan"}), 400

    email = data['email']
    user_otp = data['otp']

    success, message, status_code = process_otp_verification(email, user_otp)
    
    if success:
        return message, status_code
    else:
        return message, status_code
