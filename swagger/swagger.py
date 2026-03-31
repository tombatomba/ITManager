from flask import Blueprint, jsonify
from flask_swagger_ui import get_swaggerui_blueprint


SWAGGER_URL = '/docs'
API_URL = '/swagger.json'

swaggerui_bp = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "ElPatron API"
    }
)
