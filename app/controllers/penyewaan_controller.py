from app.models.penyewaan_model import Penyewaan
from flask import jsonify, request
from psycopg2 import errors
import os
import base64
from werkzeug.utils import secure_filename
from datetime import datetime
import requests
from koneksi import get_db
from flask_jwt_extended import jwt_required, get_jwt_identity


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = 'widy4aa'
REPO_NAME = 'dump_image'
BRANCH = 'main'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def read_all_penyewaan():
    try:
        penyewaans = Penyewaan.get_all()
        return jsonify({
            "status": "success",
            "message": "Data penyewaan berhasil diambil",
            "data": penyewaans,
            "count": len(penyewaans)
        }), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

def read_penyewaan(id):
    try:
        penyewaan = Penyewaan.get_by_id(id)
        if not penyewaan:
            return jsonify({"error": "Penyewaan tidak ditemukan"}), 404
        
        return jsonify({
            "status": "success",
            "message": "Data penyewaan berhasil diambil",
            "data": penyewaan
        }), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

def search_penyewaan_by_user():
    try:
        nama_user = request.args.get('nama_user', '')
        if not nama_user:
            return jsonify({"error": "Parameter nama_user diperlukan"}), 400
        
        penyewaans = Penyewaan.search_by_user_name(nama_user)
        return jsonify({
            "status": "success",
            "message": f"Pencarian penyewaan untuk '{nama_user}' berhasil",
            "data": penyewaans,
            "count": len(penyewaans)
        }), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

def read_penyewaan_by_status():
    try:
        status = request.args.get('status', '')
        if not status:
            return jsonify({"error": "Parameter status diperlukan"}), 400
        
        valid_statuses = ['menunggu_persetujuan', 'proses', 'dibatalkan', 'selesai']
        if status not in valid_statuses:
            return jsonify({"error": f"Status tidak valid. Status yang valid: {valid_statuses}"}), 400
        
        penyewaans = Penyewaan.get_by_status(status)
        return jsonify({
            "status": "success",
            "message": f"Data penyewaan dengan status '{status}' berhasil diambil",
            "data": penyewaans,
            "count": len(penyewaans)
        }), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

def read_penyewaan_by_user_id():
    try:
        user_id = request.args.get('user_id', '')
        if not user_id:
            return jsonify({"error": "Parameter user_id diperlukan"}), 400
        
        penyewaans = Penyewaan.get_by_user_id(user_id)
        return jsonify({
            "status": "success",
            "message": f"Data penyewaan untuk user ID {user_id} berhasil diambil",
            "data": penyewaans,
            "count": len(penyewaans)
        }), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
   
@jwt_required()   
def read_penyewaan_user():
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "Parameter user_id diperlukan"}), 400
        
        penyewaans = Penyewaan.get_by_user_id(user_id)
        return jsonify({
            "status": "success",
            "message": f"Data penyewaan untuk user ID {user_id} berhasil diambil",
            "data": penyewaans,
            "count": len(penyewaans)
        }), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
    


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_github(file):
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        content = base64.b64encode(file.read()).decode('utf-8')

        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/ktp/{unique_filename}"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        data = {
            "message": f"Upload KTP selfie: {unique_filename}",
            "content": content,
            "branch": BRANCH
        }

        response = requests.put(url, headers=headers, json=data)
        
        if response.status_code == 201:
            return f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/ktp/{unique_filename}"
        else:
            raise Exception(f"GitHub API error: {response.json().get('message', 'Unknown error')}")
    except Exception as e:
        raise e

@jwt_required()
def create_penyewaan():
    try:
        # Ambil user_id dari JWT, bukan dari request.form
        user_id = get_jwt_identity()

        required_fields = ['produk_id', 'tanggal_mulai', 'tanggal_selesai', 'metode']
        for field in required_fields:
            if field not in request.form or not request.form[field]:
                return jsonify({"error": f"Field {field} is required"}), 400

        metode = request.form['metode']
        valid_methods = ['cod', 'ambil_di_toko']
        if metode not in valid_methods:
            return jsonify({"error": f"Metode tidak valid. Metode yang valid: {valid_methods}"}), 400

        try:
            tanggal_mulai = datetime.strptime(request.form['tanggal_mulai'], '%Y-%m-%d').date()
            tanggal_selesai = datetime.strptime(request.form['tanggal_selesai'], '%Y-%m-%d').date()
            if tanggal_selesai <= tanggal_mulai:
                return jsonify({"error": "Tanggal selesai harus setelah tanggal mulai"}), 400
        except ValueError:
            return jsonify({"error": "Format tanggal tidak valid. Gunakan format YYYY-MM-DD"}), 400

        selfie_ktp_url = None
        if 'selfie_ktp' in request.files and request.files['selfie_ktp'].filename != '':
            file = request.files['selfie_ktp']
            if not allowed_file(file.filename):
                return jsonify({"error": "Tipe file selfie KTP tidak valid"}), 400
            selfie_ktp_url = upload_to_github(file)

        jam_cod = request.form.get('jam_cod')
        if jam_cod:
            try:
                datetime.strptime(jam_cod, '%H:%M:%S')
            except ValueError:
                return jsonify({"error": "Format jam COD tidak valid. Gunakan format HH:MM:SS"}), 400

        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        if latitude:
            latitude = float(latitude)
        if longitude:
            longitude = float(longitude)

        new_penyewaan = Penyewaan.create(
            produk_id=int(request.form['produk_id']),
            user_id=int(user_id),
            tanggal_mulai=tanggal_mulai,
            tanggal_selesai=tanggal_selesai,
            metode=metode,
            jam_cod=jam_cod,
            latitude=latitude,
            longitude=longitude,
            selfie_ktp=selfie_ktp_url
        )

        return jsonify({
            "status": "success",
            "message": "Penyewaan berhasil dibuat",
            "data": new_penyewaan,
            "meta": {
                "code": 201,
                "request_id": request.headers.get('X-Request-ID'),
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
        }), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal membuat penyewaan: {str(e)}"}), 500
    
def update_penyewaan(penyewaan_id):
    try:
        if not request.form and not request.files:
            return jsonify({"error": "Tidak ada data yang dikirim"}), 400

        update_data = {}

        if request.form.get('produk_id'):
            update_data['produk_id'] = int(request.form['produk_id'])
        if request.form.get('user_id'):
            update_data['user_id'] = int(request.form['user_id'])
        
        if request.form.get('tanggal_mulai'):
            try:
                update_data['tanggal_mulai'] = datetime.strptime(request.form['tanggal_mulai'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Format tanggal_mulai tidak valid. Gunakan format YYYY-MM-DD"}), 400
                
        if request.form.get('tanggal_selesai'):
            try:
                update_data['tanggal_selesai'] = datetime.strptime(request.form['tanggal_selesai'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Format tanggal_selesai tidak valid. Gunakan format YYYY-MM-DD"}), 400

        if 'tanggal_mulai' in update_data and 'tanggal_selesai' in update_data:
            if update_data['tanggal_selesai'] <= update_data['tanggal_mulai']:
                return jsonify({"error": "Tanggal selesai harus setelah tanggal mulai"}), 400

        if request.form.get('metode'):
            metode = request.form['metode']
            valid_methods = ['cod', 'ambil_di_toko']
            if metode not in valid_methods:
                return jsonify({"error": f"Metode tidak valid. Metode yang valid: {valid_methods}"}), 400
            update_data['metode'] = metode

        if request.form.get('jam_cod'):
            jam_cod = request.form['jam_cod']
            try:
                datetime.strptime(jam_cod, '%H:%M:%S')
                update_data['jam_cod'] = jam_cod
            except ValueError:
                return jsonify({"error": "Format jam COD tidak valid. Gunakan format HH:MM:SS"}), 400

        if request.form.get('latitude'):
            update_data['latitude'] = float(request.form['latitude'])
        if request.form.get('longitude'):
            update_data['longitude'] = float(request.form['longitude'])

        if 'selfie_ktp' in request.files and request.files['selfie_ktp'].filename != '':
            file = request.files['selfie_ktp']
            if not allowed_file(file.filename):
                return jsonify({"error": "Tipe file selfie KTP tidak valid"}), 400
            
            selfie_ktp_url = upload_to_github(file)
            update_data['selfie_ktp'] = selfie_ktp_url

        updated_penyewaan = Penyewaan.update(penyewaan_id, update_data)

        if not updated_penyewaan:
            return jsonify({"error": "Penyewaan tidak ditemukan"}), 404

        return jsonify({
            "status": "success",
            "message": "Penyewaan berhasil diupdate",
            "data": updated_penyewaan,
            "meta": {
                "code": 200,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengupdate penyewaan: {str(e)}"}), 500

def update_status_penyewaan(penyewaan_id):
    """Update status penyewaan"""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"error": "Field status diperlukan"}), 400

        new_status = data['status']
        updated_penyewaan = Penyewaan.update_status(penyewaan_id, new_status)

        return jsonify({
            "status": "success",
            "message": f"Status penyewaan berhasil diubah menjadi '{new_status}'",
            "data": updated_penyewaan,
            "meta": {
                "code": 200,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengupdate status: {str(e)}"}), 500

def delete_penyewaan(penyewaan_id):
    """Menghapus penyewaan"""
    try:
        success = Penyewaan.delete(penyewaan_id)
        
        return jsonify({
            "status": "success",
            "message": "Penyewaan berhasil dihapus",
            "meta": {
                "code": 200,
                "deleted_at": datetime.utcnow().isoformat() + "Z"
            }
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": f"Gagal menghapus penyewaan: {str(e)}"}), 500