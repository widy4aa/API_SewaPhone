from app.models.produk_model import Produk
from flask import jsonify,request
from psycopg2 import errors
import os
import base64
from werkzeug.utils import secure_filename
from datetime import datetime
import requests
from koneksi import get_db

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = 'widy4aa'
REPO_NAME = 'dump_image'
BRANCH = 'main'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def read_all_produk():
    try:
        produks = Produk.get_all()
        return jsonify(produks), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
    
def read_popular_produk():
    try:
        produks = Produk.get_popular()
        return jsonify(produks), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
    
    
def read_rekomendasi_produk():
    try:
        produks = Produk.get_rekomendasi()
        return jsonify(produks), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
    
def read_produk(id):
    try:
        Produks = Produk.get_by_id(id)
        return jsonify(Produks), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_github(file):
    """Upload file to GitHub and return public URL"""
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        content = base64.b64encode(file.read()).decode('utf-8')

        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{unique_filename}"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        data = {
            "message": f"Upload produk image: {unique_filename}",
            "content": content,
            "branch": BRANCH
        }

        response = requests.put(url, headers=headers, json=data)
        
        if response.status_code == 201:
            return f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{unique_filename}"
        else:
            raise Exception(f"GitHub API error: {response.json().get('message', 'Unknown error')}")
    except Exception as e:
        raise e

def create_produk():
    try:
        required_fields = ['nama_produk', 'warna', 'harga_sewa', 'keterangan']
        for field in required_fields:
            if field not in request.form or not request.form[field]:
                return jsonify({"error": f"Field {field} is required"}), 400

        charger = request.form.get('charger', 'true').lower() == 'true'
        casing = request.form.get('casing', 'true').lower() == 'true'

        if 'gambar' not in request.files:
            return jsonify({"error": "No file part"}), 400
            
        file = request.files['gambar']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        image_url = upload_to_github(file)

        data = {
            'nama_produk': request.form['nama_produk'],
            'warna': request.form['warna'],
            'harga_sewa': int(request.form['harga_sewa']),
            'keterangan': request.form['keterangan'],
            'img_path': image_url,  # Sekarang berisi URL GitHub
            'status': request.form.get('status', 'active'),
            'charger': charger,
            'casing': casing
        }

        new_id = Produk.create_produk(**data)
        
        return jsonify({
            "status": "success",
            "message": "Produk berhasil dibuat",
            "data": {
                "id": new_id,
                "nama_produk": request.form['nama_produk'],
                "warna": request.form['warna'],
                "harga_sewa": int(request.form['harga_sewa']),
                "keterangan": request.form['keterangan'],
                "status": request.form.get('status', 'active'),
                "gambar": {
                    "url": image_url,
                    "filename": secure_filename(file.filename)
                },
                "kelengkapan": {
                    "charger": charger,
                    "casing": casing
                },
                "created_at": datetime.utcnow().isoformat() + "Z"
            },
            "meta": {
                "code": 201,
                "request_id": request.headers.get('X-Request-ID')
            }
        }), 201

    except Exception as e:
        return jsonify({"error": f"Gagal membuat produk: {str(e)}"}), 500
    
def update_produk(product_id, request):
    try:
        if not request.form and not request.files:
            return jsonify({"error": "Tidak ada data yang dikirim"}), 400

        update_data = {
            'nama_produk': request.form.get('nama_produk'),
            'warna': request.form.get('warna'),
            'harga_sewa': request.form.get('harga_sewa'),
            'keterangan': request.form.get('keterangan'),
            'status': request.form.get('status'),
            'kelengkapan': {
                'charger': request.form.get('charger'),
                'casing': request.form.get('casing')
            }
        }

        if 'gambar' in request.files and request.files['gambar'].filename != '':
            file = request.files['gambar']
            if not allowed_file(file.filename):
                return jsonify({"error": "Tipe file tidak valid"}), 400
            
            image_url = upload_to_github(file)
            update_data['img'] = image_url

        updated_product, updated_kelengkapan = Produk.update(product_id, update_data)

        if not updated_product:
            return jsonify({"error": "Produk tidak ditemukan"}), 404

        if not updated_kelengkapan:
            cursor = get_db().cursor()
            cursor.execute("SELECT * FROM kelengkapan WHERE produk_id = %s", (product_id,))
            updated_kelengkapan = dict(cursor.fetchone() or {'charger': True, 'casing': True})

        response_data = {
            "id": updated_product['id'],
            "nama_produk": updated_product['nama_produk'],
            "warna": updated_product['warna'],
            "harga_sewa": updated_product['harga_sewa'],
            "keterangan": updated_product['keterangan'],
            "status": updated_product['status'],
            "gambar": updated_product['img'],
            "kelengkapan": {
                "charger": updated_kelengkapan.get('charger', True),
                "casing": updated_kelengkapan.get('casing', True)
            }
        }

        return jsonify({
            "status": "success",
            "message": "Produk berhasil diupdate",
            "data": response_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500