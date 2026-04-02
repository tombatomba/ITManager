# blueprints/api_routes.py (POTPUNO ISPRAVLJENA VERZIJA)

from flask import Blueprint, request, jsonify, g
from database import db
import requests  # Ovo je Python biblioteka za HTTP zahteve
from functools import wraps
from models import (
    AIConfig,
    Budget,
    CalendarEvents,
    Company,
    Goal,
    Notes,
    Task,
    TaskCategories,
    Team,
    TeamMember
)
from openai import OpenAI
from config import Config
from crud_factory import create_crud_blueprint



api_bp = Blueprint('api', __name__, url_prefix='/API')

# Pretpostavljamo da je ova funkcija definisana negde (npr. u util.py)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ostavljamo kao placeholder, ali je neophodan za rad
        return f(*args, **kwargs)
    return decorated_function

@api_bp.post("/chatgpt")
def chatgpt():
    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    """
    Prima JSON: { "message": "tekst korisnika" }
    Vraća: odgovor ChatGPT-a
    """
    #print("usao")

    if not request.is_json:
        return jsonify({"error": "Request is not JSON"}), 415


    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    try:
        completion = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": Config.OPENAI_INTRO},
                {"role": "user", "content": data["message"]}
            ]
        )

        answer = completion.choices[0].message.content
        #print(answer)

        return jsonify({"reply": answer})

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@api_bp.post('/dschat')
def chat_with_deepseek():
    
    try:
        data = request.json
        user_message = data.get('message', '')

        # Dobijanje podataka iz zahteva
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        
        # Konfiguracija za DeepSeek API
        chat_payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": user_message}
            ],
            "temperature": Config.DEEPSEEK_TEMPERATURE,
            "max_tokens": 1000
        }
        
        headers = {
            "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Slanje zahteva DeepSeek AI-u
        response = requests.post(
            Config.DEEPSEEK_URL,
            json=chat_payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            return jsonify({
                "response": ai_response,
                "model": result.get('model', 'deepseek-chat'),
                "usage": result.get('usage', {})
            })
        else:
            return jsonify({
                "error": "Failed to get response from DeepSeek",
                "status_code": response.status_code
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/save_note", methods=["POST"])
def save_note():
    my_notes = struct1.my_notes
    data = request.json
    date = data.get("date")
    title = data.get("title")
    content = data.get("content")
    #print('usao')
    # Proveri da li beleška postoji i update
    for note in my_notes:
        if note['date'] == date:
            note['title'] = title
            note['content'] = content
            break
    else:
        # Dodaj novu belešku
        my_notes.append({'date': date, 'title': title, 'content': content})

    return jsonify({"status":"ok"})

""" @api_bp.route('/updateKanban', methods=['POST'])
def updateKanban():
    new_data = request.json
    #save_data(new_data)
    return jsonify({"status": "ok"}) """



def commit_db():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

# ===============================================
# GENERIČKI API CRUD FACTORY
# ===============================================

def crud_api_factory(model, model_name, date_fields=None):
    """
    Kreira generičke GET, POST, PUT, DELETE API rute za dati model sa jedinstvenim endpointima.
    """
    
    # 1. FUNKCIJA ZA LISTU I KREIRANJE (GET ALL / POST NEW)
    def list_and_create_dynamic():
        if request.method == 'GET':
            all_items = model.query.all()
            return jsonify([serialize_model(i, date_fields) for i in all_items])
        
        elif request.method == 'POST':
            data = request.json
            try:
                # Filtriranje samo validnih polja za kreiranje
                instance = model(**data)
                db.session.add(instance)
                commit_db()
                return jsonify({'message': f'{model_name} created', f'{model_name}ID': getattr(instance, f'{model_name}ID')}), 201
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': f'Failed to create {model_name}: {str(e)}'}), 400

    # Dodeljivanje jedinstvenog imena funkcije
    list_and_create_dynamic.__name__ = f'list_and_create_{model_name.lower()}'
    
    # Registracija rute (Endpoint: api.list_and_create_user, api.list_and_create_category, itd.)
    api_bp.add_url_rule(
        rule=f'/{model_name.lower()}s', 
        endpoint=list_and_create_dynamic.__name__, # Koristi JEDINSTVENO ime kao endpoint
        view_func=login_required(list_and_create_dynamic), # Obavezna prijava
        methods=['GET', 'POST']
    )
    
    # 2. FUNKCIJA ZA DETALJE, AŽURIRANJE I BRISANJE (GET BY ID / PUT / DELETE)
    def detail_dynamic(id):
        instance = model.query.get_or_404(id)

        if request.method == 'GET':
            return jsonify(serialize_model(instance, date_fields))

        elif request.method == 'PUT':
            data = request.json
            try:
                # Ažuriranje samo prosleđenih polja
                for key, value in data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                
                commit_db()
                return jsonify({'message': f'{model_name} updated'})
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': f'Failed to update {model_name}: {str(e)}'}), 400

        elif request.method == 'DELETE':
            db.session.delete(instance)
            commit_db()
            return jsonify({'message': f'{model_name} deleted'})

    # Dodeljivanje jedinstvenog imena funkcije
    detail_dynamic.__name__ = f'detail_{model_name.lower()}'

    # Registracija rute (Endpoint: api.detail_user, api.detail_category, itd.)
    api_bp.add_url_rule(
        rule=f'/{model_name.lower()}s/<int:id>',
        endpoint=detail_dynamic.__name__, # Koristi JEDINSTVENO ime kao endpoint
        view_func=login_required(detail_dynamic), # Obavezna prijava
        methods=['GET', 'PUT', 'DELETE']
    )

# ===============================================
# INICIJALIZACIJA RUTA KORIŠĆENJEM FACTORY FUNKCIJE
# ===============================================
# crud_api_factory(User, 'User')
# crud_api_factory(Category, 'Category')
# crud_api_factory(Project, 'Project', date_fields=['StartDate', 'EndDate'])
# crud_api_factory(Task, 'Task', date_fields=['DueDate'])
# crud_api_factory(TaskAssignment, 'TaskAssignment', date_fields=['AssignedAt', 'CompletedAt'])
# crud_api_factory(TaskDependency, 'TaskDependency')
# crud_api_factory(DailyTodo, 'DailyTodo', date_fields=['TodoDate'])


# AI Config
api_bp.register_blueprint(create_crud_blueprint(AIConfig, '/ai-configs'))

# Budget
api_bp.register_blueprint(create_crud_blueprint(Budget, '/budgets'))

# Calendar Events
api_bp.register_blueprint(create_crud_blueprint(CalendarEvents, '/calendar-events'))

# Company
api_bp.register_blueprint(create_crud_blueprint(Company, '/companies'))

# Goal
api_bp.register_blueprint(create_crud_blueprint(Goal, '/goals'))

# Notes
api_bp.register_blueprint(create_crud_blueprint(Notes, '/notes'))

# Task
api_bp.register_blueprint(create_crud_blueprint(Task, '/tasks'))

# Task Categories
api_bp.register_blueprint(create_crud_blueprint(TaskCategories, '/task-categories'))

# Team
api_bp.register_blueprint(create_crud_blueprint(Team, '/teams'))

# Team Member
api_bp.register_blueprint(create_crud_blueprint(TeamMember, '/team-members'))