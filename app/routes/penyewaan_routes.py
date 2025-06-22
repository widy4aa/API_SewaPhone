from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity 
from decorators import role_required
from app.controllers.penyewaan_controller import (
    read_all_penyewaan,
    read_penyewaan,
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
def get_all_penyewaan():
    return read_all_penyewaan()