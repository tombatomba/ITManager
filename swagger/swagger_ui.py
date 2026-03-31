from flask import Blueprint, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from swagger.auto_spec import crud_paths


def create_swagger(app, model_routes):
    """
    model_routes = [
        (Team, "/api/teams"),
        (Task, "/api/tasks"),
        ...
    ]
    """

    SWAGGER_URL = "/docs"
    API_URL = "/swagger.json"

    swaggerui_bp = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={"app_name": "ElPatron API"}
    )

    app.register_blueprint(swaggerui_bp)

    @app.route("/swagger.json")
    def swagger_json():
        paths = {}

        for model, prefix in model_routes:
            paths.update(crud_paths(model, prefix))

        return jsonify({
            "openapi": "3.0.0",
            "info": {
                "title": "ElPatron REST API",
                "version": "1.0.0"
            },
            "servers": [{"url": "/"}],
            "components": {
                "securitySchemes": {
                    "cookieAuth": {
                        "type": "apiKey",
                        "in": "cookie",
                        "name": "session"
                    }
                }
            },
            "security": [{"cookieAuth": []}],
            "paths": paths
        })
