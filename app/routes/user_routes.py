from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity 
from decorators import role_required
from app.controllers.user_controller import (
    read_all_user,
    read_user,
    read_user_from_jwt,
    update_user_profile,
    
)


user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_users_route():
    return read_all_user()

@user_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_users_by_id(id):
    return read_user(id)

@user_bp.route("/me", methods=["GET"])
@jwt_required()
def get_user_profile():
    return read_user_from_jwt(get_jwt_identity())
    

@user_bp.route('/me', methods=['PUT'])
@jwt_required()
def put_user_profile():
    return update_user_profile(get_jwt_identity(),request.get_json())

