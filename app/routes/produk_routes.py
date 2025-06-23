from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity 
from decorators import role_required
from app.controllers.produk_controller import read_all_produk,read_popular_produk,read_rekomendasi_produk,read_produk,create_produk,update_produk


produk_bp = Blueprint('produk_bp', __name__)

@produk_bp.route('/', methods=['GET'])
def get_produk_route():
    return read_all_produk()

@produk_bp.route('/popular', methods=['GET'])
@jwt_required()
def get_produk_popular_route():
    return read_popular_produk()

@produk_bp.route('/rekomendasi', methods=['GET'])
@jwt_required()
def get_produk_rekomendasi_route():
    return read_rekomendasi_produk()

@produk_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_produk_by_id(id):
    return read_produk(id)

@produk_bp.route('/create', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_produk_route():
    return create_produk()

@produk_bp.route('/update/<int:id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def handle_update_produk(id):
    try:
        if request.content_type == 'application/json':
            data = request.get_json()
            request.form = data  
            if 'kelengkapan' in data:
                request.form.update(data['kelengkapan'])

        return update_produk(id, request)
    
    except Exception as e:
        return jsonify({"error": "Invalid request format"}), 400