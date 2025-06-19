from flask_jwt_extended import verify_jwt_in_request, get_jwt
from functools import wraps
from flask import jsonify

def role_required(required_role):
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            print("🔍 JWT claims:", claims)

            if claims.get("role") != required_role:
                return jsonify(msg="Akses ditolak untuk role ini"), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper
