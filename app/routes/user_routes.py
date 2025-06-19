from flask import Blueprint, jsonify, request
from app.controllers.user_controller import read_all_user,read_user,create_user,read_user_from_jwt
from flask_jwt_extended import jwt_required, get_jwt_identity 
from decorators import role_required


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
    
