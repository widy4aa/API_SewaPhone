from flask import Flask
from app.routes.user_routes import user_bp
from app.routes.another_routes import another
from app.routes.auth_routes import auth
from app.routes.produk_routes import produk_bp
from app.routes.penyewaan_routes import penyewaan
from flask_jwt_extended import JWTManager


def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(another, url_prefix='/api/another/')
    app.register_blueprint(produk_bp, url_prefix='/api/produk/')
    app.register_blueprint(penyewaan, url_prefix='/api/penyewaan/')
    app.config.from_mapping(
    JWT_SECRET_KEY="a9f3c5d68c70e1435f2e8ac4939fc79ab35c5d4a9d8e7c6ff0482b6b85b7c86f",
    

)

    jwt = JWTManager(app)
    return app

