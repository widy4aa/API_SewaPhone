from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity 
from decorators import role_required
from app.controllers.penyewaan_controller import (
    read_all_penyewaan,
    read_penyewaan,
    read_penyewaan_user,
    search_penyewaan_by_user,
    read_penyewaan_by_status,
    read_penyewaan_by_user_id,
    create_penyewaan,
    update_penyewaan,
    update_status_penyewaan,
    delete_penyewaan
)

penyewaan = Blueprint('penyewaan', __name__)

@penyewaan.route('', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_all_penyewaan():
    return read_all_penyewaan()

@penyewaan.route('/<int:penyewaan_id>', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_penyewaan_by_id(penyewaan_id):
    return read_penyewaan(penyewaan_id)

@penyewaan.route('/search', methods=['GET'])
@jwt_required()
@role_required('admin')
def search_by_nama_user():
    return search_penyewaan_by_user()

@penyewaan.route('/status', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_by_status():
    return read_penyewaan_by_status()

@penyewaan.route('/user', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_by_user_id():
    return read_penyewaan_by_user_id()

@penyewaan.route('/me',methods=['GET'])
@jwt_required()
@role_required('user')
def get_penyewaan_me():
    return read_penyewaan_user()

@penyewaan.route('', methods=['POST'])
@jwt_required()
@role_required('user')
def create_new_penyewaan():
    return create_penyewaan()

@penyewaan.route('/<int:penyewaan_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_existing_penyewaan(penyewaan_id):
    return update_penyewaan(penyewaan_id)

@penyewaan.route('/<int:penyewaan_id>/status', methods=['PATCH'])
@jwt_required()
def update_status(penyewaan_id):
    return update_status_penyewaan(penyewaan_id)
