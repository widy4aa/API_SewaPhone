from flask import jsonify
from app.models.user_model import User
from psycopg2 import errors
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, jsonify
import os
import requests
import base64
from werkzeug.utils import secure_filename
from datetime import datetime

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = 'widy4aa' 
REPO_NAME = 'dump_image' 
BRANCH = 'main'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

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



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_github(file):
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"profile_pictures/{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        content = base64.b64encode(file.read()).decode('utf-8')
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{unique_filename}"       
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }
        data = {
            "message": f"Upload profile picture: {filename}",
            "content": content,
            "branch": BRANCH
        }
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        return f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{unique_filename}"
    except requests.exceptions.RequestException as e:
        error_details = e.response.json().get('message', 'Unknown API error')
        print(f"GitHub API error: {error_details}")
        raise Exception(f"Gagal mengunggah ke GitHub: {error_details}")
    except Exception as e:
        print(f"An unexpected error occurred during upload: {e}")
        raise e
    
def get_user_profile_picture(user_id):
    try:
        result, status_code = User.get_profile_picture(user_id)
        return jsonify(result), status_code
    except Exception as e:
        print(f"Controller error in get_user_profile_picture: {e}")
        return jsonify({"success": False, "error": "Terjadi kesalahan pada server."}), 500


@jwt_required()
def update_my_profile_picture():
    try:
        current_user_id = get_jwt_identity()
        if 'profile_picture' not in request.files:
            return jsonify({"success": False, "error": "Tidak ada file gambar yang diunggah. Gunakan key 'profile_picture'."}), 400            
        file = request.files['profile_picture']
        if file.filename == '':
            return jsonify({"success": False, "error": "Nama file tidak boleh kosong."}), 400
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": f"Tipe file tidak valid. Pilihan yang diizinkan: {list(ALLOWED_EXTENSIONS)}"}), 400
        image_url = upload_to_github(file)
        result, status_code = User.update_profile_picture(current_user_id, image_url)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"success": False, "error": f"Gagal memperbarui foto profil: {str(e)}"}), 500


@jwt_required()
def update_user_point_by_id(user_id):
    try:
        data = request.get_json()

        if not data or 'point' not in data:
            return jsonify({"success": False, "error": "Field 'point' wajib dikirim."}), 400

        new_point = data['point']
        if not isinstance(new_point, int):
            return jsonify({"success": False, "error": "Field 'point' harus berupa angka (integer)."}), 400

        result, status_code = User.edit_point_only(user_id, new_point)
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"success": False, "error": f"Gagal memperbarui poin: {str(e)}"}), 500