# app.py
from flask import Flask
from config import Config
from database import db, init_db
#from swagger.swagger_ui import create_swagger

app = Flask(__name__)
app.config.from_object(Config)

# 1. PRVO: Inicijalizuj bazu
init_db(app)

with app.app_context():
    from models import Team, TeamMember, Task, Goal
    from blueprints.api_routes import api_bp
    from blueprints.web_routes import web_bp
    from blueprints.ai_routes import ai_bp

# 3. Registracija Blueprints-a
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(ai_bp)

# 4. Sada Swagger može da radi normalno
""" create_swagger(app, [
    (Team, "/api/teams"),
    (TeamMember, "/api/team-members"),
    (Task, "/api/tasks"),
    (Goal, "/api/goals"),
]) """

if __name__ == '__main__':
    app.run(debug=True)