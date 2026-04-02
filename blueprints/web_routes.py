# blueprints/web_routes.py

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from sqlalchemy import desc
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, Response, render_template, request, redirect, url_for, flash, session, current_app, jsonify
import requests
from AIConfig import AIConfig
from blueprints.ai_routes import call_openai
from database import db                               
from models import TeamMember, TaskCategories,Goal ,CalendarEvents ,Budget , Notes,Task,Company, TaskComment, TeamKnowledge, DashboardCard, CompanyKnowledge, Team, KnowledgeEmbedding    # Modeli sada koriste bazu iz database.py
from datetime import date, timedelta, datetime, timezone
from collections import defaultdict
import uuid
import json


# Uključivanje pomoćnih funkcija
from blueprints.api_routes import commit_db # Koristimo commit_db definisanu u API rutama

from util import handle_error # Pretpostavlja se da je handle_error definisan u util.py

web_bp = Blueprint('web', __name__)



# ==========================
# LOGIN / LOGOUT
# ==========================
@web_bp.route('/', methods=['GET'])
def index():
    if 'current_user_name' in session:
        return redirect(url_for('web.categories_web')) # Prebacujemo na web.categories_web
    return redirect(url_for('web.login'))

@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('username') # HTML input name="username"
        password = request.form.get('password')

        # 1. Pronađi korisnika u bazi preko maila
        user = TeamMember.query.filter_by(Email=email).first()
        print('DEBUG user',user)

        # 2. Proveri da li korisnik postoji i da li je lozinka ispravna
        # check_password_hash upoređuje uneti password sa kriptovanim hashom iz baze
        if user and check_password_hash(user.Password, password):
            
            # 3. Postavljanje sesije sa realnim podacima iz baze
            session['current_user_id'] = user.ID
            session['current_user_name'] = user.Name
            session['team_id'] = user.TeamID
            team = Team.query.filter_by(ID=user.TeamID).first()
            session['company_id'] = team.CompanyID

            # 4. UČITAVANJE GLOBALNOG CONFIGA (onaj Singleton od maločas)
            # Sada imamo prave TeamID i CompanyID za spajanje JSON-a
            print('DEBUG dosao ovde')
            AIConfig.load(team.CompanyID, user.TeamID)
            if user.NeedPasswordChange:
                print('DEBUG need password change TRUE')
                return redirect(url_for('web.change_password'))

            flash(f"Welcome, {user.Name}!", "success")
            return redirect(url_for('web.kanban'))
        
        else:
            flash("Bad credentials", "danger")
            
    return render_template('login.html')

@web_bp.route('/logout')
def logout():
    session.pop('current_user_name', None)
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for('web.login')) # Koristimo web. prefiks

@web_bp.before_request
def ensure_config_loaded():
    # Ako je korisnik ulogovan, a AIConfig memorija je prazna (npr. nakon restarta)
    if 'current_user_id' in session and not AIConfig.all():
        print("🔄 Server restartovan, ponovo učitavam config iz sesije...")
        AIConfig.load(session.get('company_id'), session.get('team_id'))



@web_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'current_user_id' not in session:
        return redirect(url_for('web.login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password == confirm_password:
            user = TeamMember.query.get(session['current_user_id'])
            
            # Update password and set flag to False
            user.Password = generate_password_hash(new_password)
            user.NeedPasswordChange = False  # <--- IMPORTANT
            db.session.commit()

            flash("Password updated successfully!", "success")
            return redirect(url_for('web.kanban'))
        else:
            flash("Passwords do not match.", "danger")

    return render_template('change_password.html')


# ==========================
# USERS (KORISNICI)
# ==========================
@web_bp.route("/users_web", methods=['GET', 'POST'])
def users_web():
    print(f"Debug: Active app: {current_app.name}")
    print(f"Debug: DB engine: {db.engine}")
   
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email', '')
        role = request.form.get('role', '')
        team_id = session['team_id']

        default_pwd = AIConfig.get('DEFAULT_PASSWORD','ChangeMe123!')       
        hashed_pwd = generate_password_hash(default_pwd)

        if username and team_id:
            # Kreiramo novog člana tima
            new_user = TeamMember(
                Name=username, 
                Email=email, 
                Role=role, 
                TeamID=team_id,
                Password = hashed_pwd,
                NeedPasswordChange=True,
                Suspended = False                
            )
            try:
                db.session.add(new_user)
                db.session.commit() # Ili tvoj commit_db()
                flash(f"User {username} added successfully!", "success")
            except Exception as e:
                db.session.rollback() # OBAVEZNO: Čisti sesiju nakon greške
                print(f"Greška pri upisu: {e}")
                flash("Unable to add user. Check if Team ID is valid.", "danger")
        else:
            flash("Username and Team ID are required!", "warning")
            
        return redirect(url_for('web.users_web'))

    # GET deo: Prikaz svih korisnika
    try:
        # Uzimamo sve članove tima koji pripadaju mom timu, sortirane po imenu
        users = TeamMember.query.filter_by(TeamID=session['team_id']).order_by(TeamMember.Name).all()
        
    except Exception as e:
        db.session.rollback()
        print(f"Greška pri čitanju: {e}")
        users = []
        flash("Unable to load users from database.", "danger")

    return render_template("users.html", users=users)

@web_bp.route("/users_web/delete/<string:user_id>", methods=['POST'])
def delete_user(user_id):
    try:
        user = TeamMember.query.get_or_404(user_id)
        db.session.delete(user)
        commit_db()
        flash("User deleted successfully!", "success")
    except Exception as e:
        handle_error(e, db, friendly_message="Unable to delete user.")
    return redirect(url_for('web.users_web'))

@web_bp.route("/users_web/edit/<string:user_id>", methods=['GET', 'POST'])
def edit_user(user_id):
    user = TeamMember.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.Name = request.form.get('Name', '').strip()
        user.Email = request.form.get('Email', '').strip()
        user.Role = request.form.get('Role', '').strip()
        print('id:',user.ID,'name:',user.Name,'role:',user.Role,'teamID',user.TeamID,'date:',user.CreatedAt)  
        if not user.Name or not user.Email or not user.Role:
            flash("Please fill in all required fields.", "danger")
            #print('usao ovde')
            return render_template("edit_user.html", user=user)

        try:
            commit_db()
            flash("User updated successfully!", "success")
        except Exception as e:
            handle_error(e, db, "Unable to update user. Please try again.")

        return redirect(url_for('web.users_web'))

    return render_template("edit_user.html", user=user)

@web_bp.route('/admin/users')
def users_admin():
    # Pretpostavka da koristiš SQLAlchemy
    current_team_id=session['team_id']
    users = TeamMember.query.filter_by(TeamID=current_team_id).all()
    return render_template('admin_users.html', users=users)

@web_bp.route('/admin/users/update-status/<string:user_id>', methods=['POST'])
def update_user_status(user_id):
    user = TeamMember.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'is_suspended' in data:
        user.Suspended = data['is_suspended']
    if 'need_password_change' in data:
        user.NeedPasswordChange = data['need_password_change']
        
    db.session.commit()
    return {"status": "success"}



# ==========================
# CATEGORIES (KATEGORIJE)
# ==========================
@web_bp.route('/categories_web', methods=['GET', 'POST'])
def categories_web():
    team_id = session['team_id']
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
    
        if name:
            new_cat = TaskCategories(Name=name, Description=description, TeamID=team_id)
            try:
                db.session.add(new_cat)
                commit_db()
                flash("Category added successfully!", "success")
            except Exception as e:
                handle_error(e, db, friendly_message="Unable to add category. Please try again.")
        return redirect(url_for('web.categories_web'))

    categories = TaskCategories.query.filter_by(TeamID = team_id)
    return render_template('categories.html', categories=categories)

@web_bp.route('/categories_web/delete/<string:id>', methods=['POST'])
def delete_category(id):
    cat = TaskCategories.query.get_or_404(id)
    try:
        db.session.delete(cat)
        commit_db()
        flash('Category deleted!', 'danger')
    except Exception as e:
        handle_error(e, db, friendly_message="Unable to delete category. Check for associated projects/tasks.")
    return redirect(url_for('web.categories_web'))

@web_bp.route('/categories_web/edit/<string:id>', methods=['GET', 'POST'])
def edit_category(id):
    team_id = session['team_id']
    cat = TaskCategories.query.get_or_404(id)
    if request.method == 'POST':
        cat.Name = request.form['name']
        cat.Description = request.form.get('description', '')
        cat.TeamID = team_id
        try:
            commit_db()
            flash('Category updated!', 'success')
        except Exception as e:
            handle_error(e, db, friendly_message="Unable to update category.")
        return redirect(url_for('web.categories_web'))
    return render_template('edit_category.html', category=cat)

# ==========================
# TASKS & ASSIGNMENTS (Hardkodovane rute su očišćene i pojednostavljene)
# ==========================

@web_bp.route('/update_task_status', methods=['POST'])
def update_task_status():
    data = request.get_json()
    task_id = data.get('task_id')
    new_status = data.get('status')
       
    task = Task.query.get(task_id)
    if task:
        task.Status = new_status
        db.session.commit()
        return {"result": "success"}
    return {"result": "error"}, 404


@web_bp.route("/taskAssign_web")
def taskAssign_web():
    # OVO TREBA ZAMENITI DB UPITIMA, Ostavljeno kao hardkodovani placeholder
    #employees = struct1.employees # Pretpostavlja se da je premešteno u struct1.py
    team_id = session.get('team_id')
    employees = get_employees_tasks_report(team_id)

    # 1. Pozivamo tvoju osnovnu metodu koja vraća sve taskove za tim
    all_tasks = get_tasks_for_team(team_id)
    
    # 2. Filtriramo listu tako da ostanu samo oni gde je AssignedToID None
    # i mapiramo ih u traženi format
    unassigned_tasks = [
        {
            "TaskID": task["TaskID"], 
            "Title": task["TaskName"], 
            "DateTo": task["EndDate"],
            "Description":task["Description"]
        }
        for task in all_tasks if task["AssignedToID"] is None
    ]
    


    return render_template("employees_tasks_cards.html", employees=employees,unassigned_tasks=unassigned_tasks )


@web_bp.route('/assign_task', methods=['POST'])
def assign_task():
    data = request.get_json()
    task_id = data.get('taskId')
    employee_id = data.get('employeeId') # Može biti ID ili string "UNASSIGNED"

    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"success": False, "message": "Task nije pronađen"}), 404

        # Ako je spušten u unassigned-zone, employee_id će biti "UNASSIGNED"
        if employee_id == "UNASSIGNED":
            task.AssignedTo = None
        else:
            task.AssignedTo = employee_id

        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500



#-------------------------------------------------------------------------
# TASK COMMENTS
#-------------------------------------------------------------------------
def get_task_comments(task_id):
    # 1. Dobavi trenutnog korisnika iz sesije (za IsMine logiku)
    current_user_id = session['current_user_id']
    
    
    # 2. Dobavi osnovne informacije o tasku
    task = Task.query.get(task_id)
    if not task:
        return None

    # 3. Upit koji spaja komentare i članove tima
    # Povlačimo objekat komentara i ime autora u jednom prolazu
    query_results = db.session.query(
        TaskComment, 
        TeamMember.Name,        
    ).join(TeamMember, TaskComment.user_id == TeamMember.ID) \
     .filter(TaskComment.task_id == task_id) \
     .order_by(TaskComment.created_at.asc()).all()

    # 4. Pakovanje u tvoj dummy format
    task_comments = {
        "TaskID": task.ID,
        "TaskName": task.Name,
        "DueDate": task.EndDate.strftime('%Y-%m-%d') if task.EndDate else "N/A",
        "Comments": []
    }

    for comment, author_name in query_results:
        # Poredimo GUID-ove kao stringove (lower case zbog sigurnosti)
        is_mine = False
        if current_user_id:
            is_mine = str(comment.user_id).lower() == str(current_user_id).lower()
            print('curentuser:',current_user_id)
            print('commentUserID:',comment.user_id)
        task_comments["Comments"].append({
            "CommentID": comment.id,
            "UserName": author_name,
            "Message": comment.message,
            "CreatedAt": comment.created_at.strftime('%Y-%m-%d %H:%M'),
            "IsMine": is_mine
        })

    return task_comments

@web_bp.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):    
    user_id = session['current_user_id']
    comment = TaskComment.query.get_or_404(comment_id)

    # Provera: Samo autor može obrisati svoju poruku
    if str(comment.user_id).lower() == str(user_id).lower():
        try:
            now_str = datetime.now().strftime('%d.%m.%Y %H:%M') 
            comment.message = f"#Deleted at: {now_str}#"           
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("Greška pri brisanju poruke.", "danger")
    else:
        flash("Nemate dozvolu da obrišete ovu poruku.", "danger")

    return redirect(url_for('web.task_chat', task_id=comment.task_id))

@web_bp.route("/task_chat/<int:task_id>")
def task_chat(task_id):    
    task_comments = get_task_comments(task_id)
    if not task_comments:
        flash("Task not found.", "danger")
        return redirect(url_for('web.tasks_overview')) 

    return render_template("task_chat.html", data=task_comments)

@web_bp.route('/task/<int:task_id>/add_comment', methods=['POST'])
def add_comment(task_id):
    # 1. Uzmi poruku iz forme
    message_text = request.form.get('message')
    
    # 2. Uzmi ID ulogovanog korisnika iz sesije
    user_id = session['current_user_id'] 
    
    # Provera da li je korisnik ulogovan i da li poruka nije prazna
    if not user_id:
        flash("Yo have to be logged in.", "danger")
        return redirect(url_for('web.login')) # Ili gde već ide login
        
    if message_text and message_text.strip():
        try:
            # 3. Kreiraj novi objekat komentara
            # Napomena: CreatedAt će baza sama upisati (default GETDATE())
            new_comment = TaskComment(
                task_id=task_id,
                user_id=user_id,
                message=message_text.strip()
            )
            
            # 4. Sačuvaj u bazu
            db.session.add(new_comment)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"Greška pri upisu komentara: {e}")
            flash("Došlo je do greške pri slanju poruke.", "danger")

    # 5. Vrati korisnika na istu stranicu (chat prozor)
    return redirect(url_for('web.task_chat', task_id=task_id))



def get_tasks_for_team(team_id):
   
    # JOIN-ujemo Task sa TeamMember (za ime) i TaskCategory (za naziv kategorije)
    results = db.session.query(
        Task.ID,
        Task.Name.label('TaskName'),
        TaskCategories.Name.label('CategoryName'),
        Task.ActivationDate,        
        Task.EndDate,
        Task.Status,
        Task.Description,
        Task.DateLog, # Možemo koristiti ovo kao CreatedDate
        TeamMember.Name,
        TeamMember.ID.label('TeamMemberID'),
    ).outerjoin(TeamMember, Task.AssignedTo == TeamMember.ID) \
     .join(TaskCategories, Task.TaskCategoryID == TaskCategories.ID) \
     .filter(Task.TeamID == team_id).all()

    tasks = []
    for row in results:
        tasks.append({
            "TaskID": row.ID,
            "TaskName": row.TaskName,
            "TaskCategory": row.CategoryName,
            "CreatedDate": row.DateLog.strftime('%Y-%m-%d') if row.DateLog else None,
            "EndDate": row.EndDate.isoformat() if row.EndDate else None,
            "ActivationDate": row.ActivationDate.isoformat() if row.ActivationDate else None,
            "AssignedTo": row.Name ,
            "Status":row.Status,
            "Description":row.Description,
            "AssignedToID":row.TeamMemberID
        })

    return tasks



def get_employees_tasks_report(team_id):
    # 1. Prvo dohvaćamo SVE članove tima iz baze podataka
    # Pretpostavljam da se model zove TeamMember i da ima TeamID i Name polja
    all_members = TeamMember.query.filter_by(TeamID=team_id).all()
    
    # 2. Inicijaliziramo rečnik sa SVIM radnicima (prazne liste taskova)
    employees_map = {}
    for member in all_members:
        employees_map[member.ID] = {
            "EmployeeID": member.ID,
            "Name": member.Name,
            "Tasks": []
        }

    # 3. Pozivamo tvoju postojeću metodu da dobijemo "ravnu" listu taskova
    all_tasks = get_tasks_for_team(team_id)
    
    # 4. Raspoređujemo taskove radnicima koji su već u mapi
    for task in all_tasks:
        emp_id = task["AssignedToID"]
        status = task.get("Status", "To Do")
        # Ako task ima dodijeljenog radnika i taj radnik postoji u našem timu
        if emp_id is not None and emp_id in employees_map:
            employees_map[emp_id]["Tasks"].append({
                "TaskID": task["TaskID"],
                "Title": task["TaskName"],
                "DateTo": task["EndDate"],  
                "Status":status, 
                "Description":task["Description"],                            
                "TaskCategory": task.get("TaskCategory", "") # Dodano radi popup-a ako postoji
            })

    # 5. Pretvori rečnik u listu (sadrži sve radnike, sa ili bez taskova)
    return list(employees_map.values())



@web_bp.route("/tasks_overview")
def tasks_overview():
    #tasks = struct1.tasks
    current_team_id=session['team_id']
    tasks = get_tasks_for_team(current_team_id)    
    # GET parametri
    
    name_filter = request.args.get("name", "").lower()
    category_filter = request.args.get("category", "")
    assigned_filter = request.args.get("assigned", "")
    created_month = request.args.get("created_month", "")
    end_month = request.args.get("end_month", "")
    activation_month = request.args.get("activation_month", "")
    today = date.today().strftime("%Y-%m-%d")
    filtered_tasks = []
    for t in tasks:
        # filter po name contains
        if name_filter and name_filter not in t["TaskName"].lower():
            continue
        # filter po kategoriji
        if category_filter and category_filter != t["TaskCategory"]:
            continue
        # filter po assigned
        if assigned_filter:
            if assigned_filter == "-1":
                # Ako je izabrano "Unassigned", tražimo one koji su "Unassigned" ili None
                if t["AssignedTo"] not in ("Unassigned", None, ""):
                    continue
            else:
                # Ako je izabrano konkretno ime, poredimo ga
                if assigned_filter != t["AssignedTo"]:
                    continue
        

        # filter po created month
        if created_month:
            month = int(created_month)
            if month != int(t["CreatedDate"].split("-")[1]):
                continue
        # filter po end month
        if end_month:
            month = int(end_month)
            if month != int(t["EndDate"].split("-")[1]):
                continue
        # filter po activation month
        if activation_month:   
            month = int(activation_month)
            # Provera da li ActivationDate postoji i da li je validan format
            activation_date = t.get("ActivationDate")
            if not activation_date or activation_date in ("N/A", ""):
                continue  # preskoči ovaj task ako nema validan datum
            try:
                task_month = int(activation_date.split("-")[1])
            except (ValueError, IndexError):
                continue  # preskoči ako datum nije validan
            if month != task_month:
                continue
        filtered_tasks.append(t)

    # Dobavljamo jedinstvene vrednosti za dropdowns    
    #categories = sorted(set(t["TaskCategory"] for t in tasks))
    #assigned_to = sorted(set(t["AssignedTo"] for t in tasks))
    # OVO MENJAMO TAKO DA MOZE DA povuce iz sifarnika
    categories = TaskCategories.query.filter_by(TeamID=current_team_id).all()
    users =TeamMember.query.filter_by(TeamID=current_team_id).all()
    next_week = datetime.now() + timedelta(days=7) # Računamo datum za 7 dana

    return render_template(
        "tasks_overview.html",
        tasks=filtered_tasks,
        categories=categories,
        users=users,
        today=today,
        nextWeek = next_week.strftime("%Y-%m-%d"),
        filters=request.args
    )


@web_bp.route('/task/close-review/<int:task_id>')
def task_close_review(task_id):
    task = Task.query.get_or_404(task_id)
    print('assigneName:',task.assignee.Name)
    comments = TaskComment.query.filter_by(task_id=task_id).all()
    
    # Računanje kašnjenja (Days past EndDate)
    days_past = 0
    if task.EndDate:
        delta = datetime.now().date() - task.EndDate
        days_past = delta.days

    return render_template('task_close_review.html', 
                           task=task, 
                           comments=comments, 
                           current_date=datetime.now().strftime('%Y-%m-%d'),
                           days_past=days_past)

@web_bp.route('/task/confirm-archive/<int:task_id>', methods=['POST'])
def confirm_archive(task_id):
    current_user_id = session['current_user_id'];
    user = TeamMember.query.get(current_user_id)
    current_role = user.Role if user else "Guest"
    if current_role != 'Admin':
        return "Unauthorized", 403

    task = Task.query.get_or_404(task_id)
    
    # Hvatanje podataka iz forme
    closed_date = request.form.get('closed_date')
    rating = request.form.get('rating')
    closing_note = request.form.get('closing_note')

    try:
        task.Status = "Archived"
        task.ArchiveDate = closed_date # Ažuriramo na stvarni datum zatvaranja
        # Ovde bi bilo dobro da imaš kolone Rating i Feedback u tabeli Task
        task.Rating = int(rating)
        task.ClosingNote = closing_note
        
        db.session.commit()
        flash(f"Zadatak '{task.Name}' archived with rating {rating}.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Archiving process error", "danger")

    return redirect(url_for('web.kanban'))

@web_bp.route('/archive_task', methods=['POST'])
def archive_task():
    
    current_role='Admin' # ovo treba da povuce iz current usera
    # 1. Provera Admin uloge    
    if current_role != 'Admin':
        return jsonify({"success": False, "message": "Samo Admini mogu arhivirati zadatke"}), 403

    data = request.get_json()
    task_id = data.get('taskId')
    description = data.get('description')

    task = Task.query.get(task_id)
    if not task:
        return jsonify({"success": False, "message": "Zadatak nije pronađen"}), 404

    try:
        # 2. Ažuriranje statusa i opisa
        task.Status = "Archived"
        # Pretpostavljam da imaš polje za opis ili dodaješ u log
        task.Description = f"ARCHIVED BY {session.get('user_name')}: {description}"
        
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@web_bp.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    from models import Task, TaskCategories, TeamMember, db
    from datetime import datetime

    current_team_id = session.get('team_id')
    
    # 1. Pronađi task u bazi (koristimo ID koji je bigint)
    task_record = Task.query.get(task_id)
    
    if not task_record:
        flash("Task not found!", "danger")
        return redirect(url_for("web.tasks_overview"))

    # 2. Povuci liste za dropdown (ID i Name)
    categories = TaskCategories.query.filter_by(TeamID=current_team_id).all()
    users = TeamMember.query.filter_by(TeamID=current_team_id).all()

    if request.method == "POST":
        try:
            # 3. Ažuriranje osnovnih polja (pazi na nazive kolona u bazi)
            task_record.Name = request.form.get("TaskName")
            task_record.Description = request.form.get("TaskDescription")
            task_record.TaskCategoryID = request.form.get("TaskCategory") # Ovde stiže ID iz ispravljenog HTML-a
            task_record.AssignedTo = request.form.get("AssignedTo")      # Ovde stiže ID

            # Provera da li je odabrano "Unassigned" (-1) PA MENJAM OBJEKAT TAKO DA SACUVA NULL
            if request.form.get("AssignedTo")  == "-1":
                task_record.AssignedTo = None
            
            # 4. Konverzija datuma (HTML string -> Python date)
            def parse_date(date_str):
                if not date_str: return None
                return datetime.strptime(date_str, '%Y-%m-%d').date()

            task_record.EndDate = parse_date(request.form.get("EndDate"))
            task_record.ActivationDate = parse_date(request.form.get("ActivationDate"))

            # 5. Snimanje
            db.session.commit()
            flash("Task updated successfully!", "success")
            return redirect(url_for("web.tasks_overview"))

        except Exception as e:
            db.session.rollback()
            print(f"Update error: {e}")
            flash(f"Error updating task: {str(e)}", "danger")

    # Ako je GET, šaljemo podatke u templejt
    
    return render_template("edit_task.html", 
                           task=task_record, 
                           categories=categories, 
                           users=users)


@web_bp.route("/task/new", methods=["POST"]) # Promenio u samo POST jer je forma na overview strani
def new_task():

    current_team_id = session.get('team_id')
    assigned_val = request.form.get("AssignedTo")

 
    try:
        # 1. Kreiranje objekta - proveri nazive polja sa tvojim SQL-om
        new_task_obj = Task(
            Name = request.form.get("TaskName"),
            Description = request.form.get("Description"), # Dodaj ovo polje u HTML ako ga želiš
            TaskCategoryID = request.form.get("TaskCategory"), # Ovo sada prima ID iz HTML-a
            AssignedTo = request.form.get("AssignedTo"),       # Ovo sada prima ID
            ProjectName = request.form.get("ProjectName"),
            Status = "To Do", 
            TeamID = current_team_id,
            DateLog = datetime.now()
        )
        # Provera da li je odabrano "Unassigned" (-1) PA MENJAM OBJEKAT TAKO DA SACUVA NULL
        if assigned_val == "-1" or not assigned_val:
            new_task_obj.AssignedTo = None
        

        # 2. Parsiranje datuma
        if request.form.get("EndDate"):
            new_task_obj.EndDate = datetime.strptime(request.form.get("EndDate"), '%Y-%m-%d').date()
        
        if request.form.get("ActivationDate"):
            new_task_obj.ActivationDate = datetime.strptime(request.form.get("ActivationDate"), '%Y-%m-%d').date()
        else:
            new_task_obj.ActivationDate = datetime.now().date()

        # 3. Upis
        db.session.add(new_task_obj)
        db.session.commit()
        flash("New task created successfully!", "success")

    except Exception as e:
        db.session.rollback()
        print(f"Greška: {e}")
        flash(f"Error: {str(e)}", "danger")

    # Uvek se vrati na overview stranu
    return redirect(url_for("web.tasks_overview"))
    




@web_bp.route('/get_holidays_data')
def get_holidays_data():
    from models import CalendarEvents, TeamMember
    import json

    current_team_id = session.get('team_id')
    
    # 1. Uzimamo podatke iz baze (JOIN da dobijemo ime i broj slobodnih dana)
    # Pretpostavljam da FreeDays čuvaš u JsonData u TeamMember ili fiksno
    results = db.session.query(CalendarEvents, TeamMember)\
        .join(TeamMember, CalendarEvents.TeamMemberID == TeamMember.ID)\
        .filter(TeamMember.TeamID == current_team_id)\
        .all()

    holidays_dict = {}

    for cal_event, member in results:
        emp_id = member.ID
        
        # Ako zaposleni još nije u rečniku, inicijalizuj ga
        if emp_id not in holidays_dict:
            # Parsiramo dodatne podatke o zaposlenom ako postoje (npr. FreeDays)
            # Ako je FreeDays fiksni broj ili kolona u bazi, prilagodi ovde:
            free_days = 25 
            
            holidays_dict[emp_id] = {
                "EmployeeID": emp_id,
                "Name": member.Name,
                "FreeDays": free_days,
                "Abesence": []
            }
        
        # 2. Parsiramo JSON listu odsustava za taj red i dodajemo u "Abesence"
        try:
            # Sređujemo navodnike ako su u bazi jednostruki
            raw_json = cal_event.JsonData.replace("'", '"')
            absences = json.loads(raw_json)
            
            if isinstance(absences, list):
                holidays_dict[emp_id]["Abesence"].extend(absences)
            else:
                holidays_dict[emp_id]["Abesence"].append(absences)
                
        except Exception as e:
            print(f"Greška kod usera {member.Name}: {e}")

    # 3. Pretvaramo rečnik nazad u čistu listu kakvu tvoj kod očekuje
    holidays = list(holidays_dict.values())
    
    return holidays # Ili return render_template(..., holidays=holidays)

@web_bp.route('/get_budget_data')
def get_budget_data():
    from models import Budget
    import json
    
    current_team_id = session.get('team_id')
    
    # 1. Uzimamo zapis iz baze
    result = db.session.query(Budget).filter(Budget.TeamID == current_team_id).first()
    #print('result:',result.JsonData)
    if result and result.JsonData:
        try:
            # SQL Server često vraća string, pa ga pretvaramo u Python rečnik
            # Koristimo .replace ako su u bazi slučajno ostali jednostruki navodnici
            clean_json = result.JsonData.replace("'", '"')
            print('clean_json:',clean_json)
            budget_dict = json.loads(clean_json)
        except Exception as e:
            print(f"Greška pri parsiranju JSON-a: {e}")
            budget_dict = {"data": [], "columns": []}
    else:
        # Vraćamo praznu strukturu ako nema podataka u bazi
        budget_dict = {"data": [[]], "columns": []}

    # Ako ti ova metoda treba kao API (za AJAX poziv):
    # return jsonify(budget_dict)
    
    # Ako ti treba unutar druge Python funkcije:
    
    return budget_dict

@web_bp.route("/calendar")
def calendar_view():    
    holidays = get_holidays_data()
    current_team_id = session['team_id']

    team_members = TeamMember.query.filter_by(TeamID=current_team_id).all()
    # Pretvaramo u FullCalendar events format
    events = []
    colors = {
        "holiday": "#ff6961",
        "freeDay": "#77dd77",
        "homeOffice": "#779ecb"
    }


 
    for emp in holidays:
        for a in emp["Abesence"]:
            events.append({
                "id":a['id'],
                "title": f"{emp['Name']} ({a['type']})",
                "start": a["start"],
                "end": a["end"],
                "color": colors.get(a["type"], "gray"),
                "extendedProps": {
                    "employeeId": emp["EmployeeID"],
                    "type": a["type"]
                }
            })
    #print('events',events)
    return render_template("calendar.html", events=events, team_members=team_members)


@web_bp.route('/add-absence', methods=['POST'])
def add_absence():
    

    if request.method == 'POST':
        # 1. Preuzimanje podataka iz forme
        employee_id = request.form.get('employeeSelect')
        start_date_str = request.form.get('startDate')
        end_date_str = request.form.get('lastDate')
        absence_type = request.form.get('typeSelect')

        if not employee_id:
            flash("Morate odabrati zaposlenog!", "danger")
            return redirect(url_for('web.calendar_view'))

        # 2. Pronalaženje postojećeg zapisa u bazi za tog zaposlenog
        calendar_record = CalendarEvents.query.filter_by(TeamMemberID=employee_id).first()

        # Priprema novog objekta odsustva
        new_absence = {
            "id": str(uuid.uuid4()), # Generišemo string ID za JSON
            "start": start_date_str,
            "end": end_date_str,
            "type": absence_type
        }

        try:
            if calendar_record:
                # --- SLUČAJ A: Korisnik već ima listu odsustava ---
                # Dekodiramo trenutni JSON (pazimo na navodnike)
                current_data = json.loads(calendar_record.JsonData.replace("'", '"'))
                
                # Dodajemo novi element u listu
                current_data.append(new_absence)
                
                # Vraćamo u JSON string i snimamo
                calendar_record.JsonData = json.dumps(current_data)
            else:
                # --- SLUČAJ B: Prvi put dodajemo odsustvo za ovog korisnika ---
                new_record = CalendarEvents(
                    TeamMemberID=employee_id,
                    JsonData=json.dumps([new_absence]) # Lista sa jednim elementom
                )
                db.session.add(new_record)

            db.session.commit()
            flash("Odsustvo uspešno sačuvano u bazi!", "success")
            
        except Exception as e:
            db.session.rollback()
            flash(f"Greška pri upisu u bazu: {str(e)}", "danger")

        return redirect(url_for('web.calendar_view'))
    
    # Ako se iz nekog razloga pristupi ruti preko GET zahteva (trebalo bi biti blokirano)
    return redirect(url_for('index'))

@web_bp.route('/update-absence', methods=['POST'])
def update_absence():
    
    current_team_id=session['team_id']
    
    # 1. Preuzimanje podataka iz JSON tela zahteva
    data = request.get_json()
    absence_id = data.get('id')
    new_start = data.get('start')
    new_end = data.get('end')

    if not absence_id:
        return {"status": "error", "message": "Missing ID"}, 400

    # 2. Potraga za zapisom u bazi
    #all_records = CalendarEvents.query.all()
    all_records = db.session.query(CalendarEvents)\
        .join(TeamMember, CalendarEvents.TeamMemberID == TeamMember.ID)\
        .filter(TeamMember.TeamID == current_team_id)\
        .all()
    found = False

    try:
        for record in all_records:
            if not record.JsonData:
                continue
            
            absences = json.loads(record.JsonData.replace("'", '"'))
            modified = False
            
            # 3. Prolazimo kroz listu i tražimo onaj sa pravim ID-em
            for a in absences:
                if a.get('id') == absence_id:
                    a['start'] = new_start
                    # FullCalendar nekad šalje end kao null ako je u pitanju jedan dan
                    # ili šalje ekskluzivni datum (dan posle), pa to treba imati na umu
                    a['end'] = new_end if new_end else new_start
                    modified = True
                    break
            
            # Ako smo izmenili nešto u ovom redu, snimamo u bazu
            if modified:
                record.JsonData = json.dumps(absences)
                db.session.commit()
                found = True
                break

        if found:
            return {"status": "success"}, 200
        else:
            return {"status": "error", "message": "Event not found in DB"}, 404

    except Exception as e:
        db.session.rollback()
        print(f"Greška pri ažuriranju: {e}")
        return {"status": "error", "message": str(e)}, 500


@web_bp.route('/budget', methods=['GET'])
def budget():    
    from collections import defaultdict
    
    # Preuzimamo podatke (rečnik sa 'data' i 'columns')
    budget_config = get_budget_data()

    grouped = defaultdict(lambda: {
        "code": "",
        "vendors": set(),
        "budget": 0.0,
        "spent": 0.0
    })

    # Provera da li uopšte imamo podatke da izbegnemo grešku u petlji
    if not budget_config or "data" not in budget_config:
        budget_config = {"data": [], "columns": []}

    # Grupisanje po kategoriji
    for row in budget_config["data"]:
        # JSpreadsheet nekad doda prazne redove na kraju, ovo ih preskače
        if not row or len(row) < 4:
            continue

        code = row[0]
        vendor = row[2] if row[2] else "N/A"

        # BEZBEDNA KONVERZIJA: Korisnik može ostaviti prazno polje ili uneti pogrešan format
        try:
            budget_value = float(row[3]) if row[3] else 0.0
            # Sabiramo Q1 do Q4 (indeksi 4, 5, 6, 7)
            spent_total = sum([float(x) if x else 0.0 for x in row[4:8]])
        except (ValueError, TypeError):
            # Ako konverzija ne uspe, preskoči taj red ili postavi nule
            budget_value = 0.0
            spent_total = 0.0

        g = grouped[code]
        g["code"] = code
        if vendor: g["vendors"].add(vendor)
        g["budget"] += budget_value
        g["spent"] += spent_total

    items = []
    total_budget = 0.0
    total_spent = 0.0

    for _, g in grouped.items():
        if not g["code"]: continue # Preskoči ako je kod kategorije prazan

        used_percent = round((g["spent"] / g["budget"] * 100), 2) if g["budget"] > 0 else 0
        items.append({
            "code": g["code"],
            "name": g["code"],
            "vendor": ", ".join(filter(None, g["vendors"])), # Čisti None vrednosti
            "budget": g["budget"],
            "spent": g["spent"],
            "remaining": g["budget"] - g["spent"],
            "used_percent": used_percent
        })

        total_budget += g["budget"]
        total_spent += g["spent"]

    # TOTAL objekat
    total_used_percent = round((total_spent / total_budget * 100), 2) if total_budget > 0 else 0
    total_item = {
        "budget": total_budget,
        "spent": total_spent,
        "remaining": total_budget - total_spent,
        "used_percent": total_used_percent
    }

    return render_template(
        'budget.html',
        config_json=budget_config, # Flask Jinja2 će u HTML-u uraditi ostalo
        items=items,
        total_item=total_item
    )

@web_bp.route('/save-budget', methods=['POST'])
def save_budget():
    import util
    
    incoming_data = request.get_json() 
    current_team_id = session.get('team_id')

    if not incoming_data or 'data' not in incoming_data:
        return {"status": "error", "message": "Nema podataka za snimanje"}, 400

    # --- ČIŠĆENJE PODATAKA ---
    raw_rows = incoming_data['data']
    cleaned_rows = []

    for row in raw_rows:
        # Preskačemo potpuno prazne redove
        if not any(row):
            continue
            
        new_row = list(row)
        
        # Indeksi kolona koje treba da očistimo (Budget, Q1, Q2, Q3, Q4)
        # To su indeksi 3, 4, 5, 6, 7 prema tvom JSON-u
        for i in [3, 4, 5, 6, 7]:
            if i < len(new_row):
                new_row[i] = util.clean_to_float(new_row[i])
        
        cleaned_rows.append(new_row)

    # Pakujemo očišćene redove nazad u originalnu strukturu
    incoming_data['data'] = cleaned_rows

    # --- UPIS U BAZU ---
    try:
        budget_record = Budget.query.filter_by(TeamID=current_team_id).first()
        
        # Koristimo json.dumps(incoming_data) jer sada incoming_data sadrži očišćene brojeve
        if budget_record:
            budget_record.JsonData = json.dumps(incoming_data)
        else:
            new_record = Budget(
                TeamID=current_team_id, 
                JsonData=json.dumps(incoming_data)
            )
            db.session.add(new_record)
            
        db.session.commit()
        return {"status": "success"}
        
    except Exception as e:
        db.session.rollback()
        print(f"Greška pri snimanju budžeta: {e}")
        return {"status": "error", "message": str(e)}, 500

@web_bp.route("/notes") 
def notes():
    from models import Notes
    from datetime import date
    
    # Pretpostavka: TeamMemberID dobijamo iz sesije korisnika koji je ulogovan
    member_id = session['current_user_id'] 
    
    # Vučemo sve beleške za tog člana tima, sortirane po datumu
    my_notes = Notes.query.filter_by(TeamMemberID=member_id).order_by(Notes.NoteDate.asc()).all()
    #print('my-notes:',my_notes)
    today = date.today().isoformat()
    return render_template("notes.html", notes=my_notes, todayDate=today)



# API za cuvanje beleške

@web_bp.route("/save_note", methods=["POST"])
def save_note():
    from models import Notes
    from datetime import datetime
    import uuid

    # 1. Prikupljanje podataka iz forme
    note_id = request.form.get("note_id")  # Skriveno polje iz HTML-a
    date_str = request.form.get("date")
    title_val = request.form.get("title")
    content_val = request.form.get("content")
    
    # 2. Identifikacija korisnika (osiguraj da je ključ u sesiji tačan)
    member_id = session['current_user_id'] 
    if not member_id:
        return "Greška: Korisnik nije identifikovan (nema TeamMemberID u sesiji)", 403

    # 3. Parsiranje datuma
    try:
        note_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        note_date = datetime.now().date()

    try:
        # 4. LOGIKA: Update ili Insert
        existing_note = None
        if note_id and note_id.strip():
            # Ako imamo ID, tražimo baš tu belešku
            existing_note = Notes.query.filter_by(ID=note_id, TeamMemberID=member_id).first()

        if existing_note:
            # UPDATE: Menjamo postojeću belešku
            existing_note.NoteDate = note_date
            existing_note.NoteTitle = title_val
            existing_note.NoteContent = content_val
            existing_note.DateLog = datetime.now()
        else:
            # INSERT: Pravimo potpuno novu belešku
            new_note = Notes(
                ID=str(uuid.uuid4()), # Generišemo novi ID
                NoteDate=note_date,
                NoteTitle=title_val,
                NoteContent=content_val,
                TeamMemberID=member_id,
                DateLog=datetime.now()
            )
            db.session.add(new_note)

        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Greška pri snimanju beleške: {str(e)}")
        return f"Greška na serveru: {str(e)}", 500

    return redirect(url_for("web.notes"))

@web_bp.route('/employee/<string:employee_id>/goals')
def employee_goals(employee_id):
    
    # 2. Pronađi zaposlenog u bazi (da bismo dobili njegovo ime)
    employee = TeamMember.query.get_or_404(employee_id)
    employee_name = employee.Name
    processed_goals=[]
    print('DEBUG: employee_goal, --empoid-',employee_id)
    # 3. Učitaj sve ciljeve iz baze za tog zaposlenog
    # Filtriramo po koloni TeamMemberID koja se nalazi u Goal modelu
    db_goals = Goal.query.filter_by(TeamMemberID=employee_id).all()
    for g in db_goals:
        goal_data = {
            'ID': g.ID,
            'EmployeeID':employee_id,
            'GoalDescription': g.Description,
            'GoalType': g.GoalType,
            'Year': g.Year,
            'EmployeeName': employee_name # Dodajemo ime radi kompatibilnosti sa starim kodom
        }
        processed_goals.append(goal_data)

   
    #employee_goals = [g for g in goals if g['EmployeeID'] == employee_id]
    # Pronađi ime zaposlenog (ako postoji bar jedan cilj)
    #employee_name = employee_goals[0]['EmployeeName'] if employee_goals else "Unknown Employee"
    
    return render_template('goals_list.html', 
                          goals=processed_goals, 
                          employee_id=employee_id,
                          employee_name=employee_name)

# Dodavanje novog cilja za zaposlenog
@web_bp.route('/employee/<string:employee_id>/goals/add', methods=['GET', 'POST'])
def add_goal(employee_id):
    from models import TeamMember, Goal
    from datetime import datetime

    # 1. Pronađi zaposlenog da bi izvukao ime za naslov forme
    employee = TeamMember.query.get_or_404(employee_id)
    employee_name = employee.Name

    if request.method == 'POST':
        try:
            # 2. Kreiranje nove instance Goal modela
            new_goal = Goal(
                TeamMemberID=employee_id,
                GoalType=request.form.get('goal_type'),
                Description=request.form.get('goal_description'),
                Year=datetime.utcnow().year, # Automatski setujemo trenutnu godinu
                JsonData=json.dumps({})      # Inicijalizujemo prazan JSON ako zatreba kasnije
            )
            
            # 3. Upis u bazu
            db.session.add(new_goal)
            db.session.commit()
            
            flash('Goal successfully added!', 'success')
            return redirect(url_for('web.employee_goals', employee_id=employee_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding goal: {str(e)}', 'danger')

    # Za GET zahtev prikazujemo praznu formu
    return render_template('goals_form.html', 
                          goal=None, 
                          action='add', 
                          employee_id=employee_id,
                          employee_name=employee_name)

# Izmena postojećeg cilja
@web_bp.route('/employee/<string:employee_id>/goals/edit/<string:goal_id>', methods=['GET', 'POST'])
def edit_goal(employee_id, goal_id):
    # Pronađi goal u bazi (koristi objekte, ne nizove)
    goal = Goal.query.filter_by(ID=goal_id, TeamMemberID=employee_id).first()
    
    if not goal:
        flash('Goal not found.', 'danger')
        return redirect(url_for('web.employee_goals', employee_id=employee_id))

    if request.method == 'POST':
        # Uzimamo podatke iz forme koristeći ispravne name atribute
        # Koristimo .get() da bismo izbegli BadRequestKeyError
        g_type = request.form.get('goal_type')
        g_year = request.form.get('goal_year')
        g_desc = request.form.get('goal_description')

        # Provera da li su polja popunjena
        if not g_type or not g_year or not g_desc:
            flash('All fields are required!', 'warning')
            return render_template('goals_form.html', goal=goal, action='edit', 
                                 employee_id=employee_id, employee_name=goal.EmployeeName)

        # Ažuriranje SQLAlchemy objekta (koristimo .atribut, ne ['ključ'])
        goal.GoalType = g_type
        goal.Year = g_year # Proveri da li se kolona u bazi zove Year ili GoalYear
        goal.Description = g_desc

        
        try:
            db.session.commit()
            flash('Goal successfully updated!', 'success')
            return redirect(url_for('web.employee_goals', employee_id=employee_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Database error: {str(e)}', 'danger')

    # Za inicijalni GET request
    return render_template('goals_form.html', 
                          goal=goal, 
                          action='edit', 
                          employee_id=employee_id,
                          employee_name=getattr(goal, 'EmployeeName', 'Employee'))# Brisanje cilja
@web_bp.route('/employee/<string:employee_id>/goals/delete/<string:goal_id>')
def delete_goal(employee_id, goal_id):
    print('usao ovde:',employee_id)
    # 1. Pronađi cilj u bazi koristeći primarni ključ (goal_id)
    # Proveravamo i TeamMemberID da bismo bili sigurni da brišemo cilj pravog zaposlenog
    goal = Goal.query.filter_by(ID=goal_id, TeamMemberID=employee_id).first()
    print('goal za brisanje',goal.ID)
    if goal:
        try:
            # 2. Obriši objekat iz sesije
            db.session.delete(goal)
            
            # 3. Potvrdi izmenu u bazi
            db.session.commit()
            flash('Goal successfully deleted!', 'success')
        except Exception as e:
            # U slučaju greške, poništi promene
            db.session.rollback()
            flash(f'Error deleting goal: {str(e)}', 'danger')
    else:
        flash('Goal not found.', 'danger')
        
    return redirect(url_for('web.employee_goals', employee_id=employee_id))


#----------------------------------------------------------------------
# kanban data
#----------------------------------------------------------------------

def get_kanban_data(team_id, team_member_id="-1"):
       
    # 1. Osnovni upit: Svi zadaci koji pripadaju timu
    query = Task.query.filter(Task.TeamID == team_id)
    
    # 2. Logika filtriranja na osnovu team_member_id
    # Ako je "-1", ne dodajemo dodatni filter (prikazuje sve)
    if team_member_id == "-1" or team_member_id is None:
        pass 
    elif team_member_id == "" or team_member_id == "None":
        # Ako želimo da vidimo samo nedodeljene (Unassigned)
        query = query.filter(Task.AssignedTo == None)
    else:
        # Ako je prosleđen konkretan ID člana tima
        query = query.filter(Task.AssignedTo == team_member_id)

    tasks = query.all()
    
    # Povuci sve članove tima iz baze
    users_data = TeamMember.query.filter_by(TeamID=team_id).all()

    # Napravi hash tabelu: { "ID": "Name" }
    users_dict = {str(u.ID): u.Name for u in users_data}

    # Primer korišćenja:
    # ime = users_dict.get(t.AssignedTo, "Unassigned")
    # Standardne kolone na Kanbanu
    status_list = ["To Do", "In Progress", "Done"]
    projects = {}

    for t in tasks:
        p_name = t.ProjectName if t.ProjectName else "General"
        
        if p_name not in projects:
            projects[p_name] = {status: [] for status in status_list}
        days_left = (t.EndDate - datetime.now().date()).days if t.EndDate else None
        if t.Status in projects[p_name]:
            projects[p_name][t.Status].append({
               "id": f"card{t.ID}",
                "title": t.Name,
                "description": t.Description if t.Description else "",
                "activation_date": t.ActivationDate.strftime('%d.%m.%Y') if t.ActivationDate else "N/A",
                "end_date": t.EndDate.strftime('%d.%m.%Y') if t.EndDate else "N/A",
                "assigned_name": users_dict.get(t.AssignedTo, "Unassigned"),
                "days_left": days_left,
                "real_id": t.ID  # Treba nam čist ID za link ka komunikaciji
            })

    # 3. Pakovanje u finalni JSON format
    kanban_json = {"boards": []}
    
    for p_idx, (p_name, lists) in enumerate(projects.items(), start=1):
        board = {
            "id": f"board{p_idx}",
            "name": p_name,
            "lists": []
        }
        
        for l_idx, (status, cards) in enumerate(lists.items(), start=1):
            board["lists"].append({
                "id": f"list{p_idx}_{l_idx}",
                "name": status,
                "cards": cards
            })
            
        kanban_json["boards"].append(board)
        
    return kanban_json

# Ruta za prikaz Kanban board-a
@web_bp.route('/kanban')
def kanban(): 
    from models import TeamMember
    team_id = session.get('team_id')
    
    # 1. Uzmi member_id iz filtera (URL parametar)
    # Podrazumevano je "-1" što smo u metodi definisali kao "Prikaži sve"
    selected_member_id = request.args.get('member_id', "-1")
    
    # 2. Pozovi tvoju novu metodu sa filterom
    data = get_kanban_data(team_id, selected_member_id)
    
    # 3. Uzmi listu korisnika za padajuću listu
    users = TeamMember.query.filter_by(TeamID=team_id).all()
    print('---users----',users)
    
    # Uzimamo prvi board iz profiltriranih podataka (obično "General" ili ime projekta)
    # Ako tvoja metoda vraća više board-ova, ovde biramo prvi za prikaz
    board = data["boards"][0] if data["boards"] else {"name": "No Tasks", "lists": []}
    
    return render_template('kanban.html', 
                           board=board, 
                           data=data, 
                           users=users, 
                           selected_member_id=selected_member_id)




""" @web_bp.route("/browser2",methods=["GET","POST"])
def browser2():
    if request.method == "POST":
        url = request.form.get("url")
    else:
        # prvi load (prazan panel)
        return render_template("browser_panel.html")

    if not url:
        return render_template("browser_panel.html", error="URL is required")

    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        return render_template("browser_panel.html", error="Invalid URL")

    # security allow-list
    #if parsed.hostname not in ALLOWED_DOMAINS:
    #    return render_template("browser_panel.html", error="Domain not allowed")

    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    # rewrite links
    for tag in soup.find_all(["a", "link", "script", "img"]):
        attr = "href" if tag.name in ["a", "link"] else "src"
        if tag.has_attr(attr):
            tag[attr] = urljoin(url, tag[attr])

    body_html = soup.body.decode_contents() if soup.body else str(soup)

    return render_template(
        "browser_panel.html",
        page_html=body_html,
        page_url=url
    ) """

@web_bp.route("/browser",methods=["GET","POST"])
def browser():
    url = request.args.get("url")
    if not url:
        return "Missing url parameter", 400

    try:
        r = requests.get(
            url,
            timeout=12,
            headers={
                "User-Agent": "Mozilla/5.0 AI-Browser"
            }
        )
        r.raise_for_status()

        html = r.text

        inject = """
<script>
window.addEventListener("message", (e) => {
    if (e.data.type === "GET_CONTEXT") {
        const text = document.body.innerHTML;
        window.parent.postMessage(
            { type: "AI_CONTEXT", text },
            "*"
        );
    }
});
</script>
"""

        if "</body>" in html:
            html = html.replace("</body>", inject + "</body>")
        else:
            html += inject

        return Response(html, content_type="text/html")

    except Exception as e:
        return f"Browser error: {str(e)}", 500

@web_bp.route("/browser_panel")
def browser_panel():
    return render_template("browser_panel.html")

@web_bp.route("/playground")
def ai_playground():
    return render_template("ai_playground.html")

@web_bp.route("/multi_playground")
def multi_playground():
    return render_template("multi_playground.html")




@web_bp.route("/absence_matrix")
def absence_matrix():
    # 1. Određivanje godine za filter
    selected_year = request.args.get('year', default=datetime.now().year, type=int)
    
    try:
        # Koristimo tvoju novu funkciju koja vuče podatke iz baze
        # (Osiguraj da get_holidays_data() filtrira po TeamID iz sesije)
        holidays = get_holidays_data() 
        
        # Ako struct1.holidays_set sadrži fiksne praznike, proveri da li su za tu godinu
        # Idealno bi bilo da imaš funkciju get_public_holidays(selected_year)
        #import struct1
        holidays_set = struct1.holidays_set 
    except Exception as e:
        print(f"Greška pri učitavanju podataka: {e}")
        return {"error": str(e)}

    matrix = {} 
    matrix2 = {} 
    demo = {}
    emp_remain = {}

    for emp in holidays:
        emp_name = emp["Name"] 
        emp_freeday = emp.get("FreeDays", 25)
        
        # Inicijalizacija matrica za odabranu godinu
        matrix[emp_name, emp_freeday] = {w: 0 for w in range(1, 54)} 
        matrix2[emp_name] = {w: 0 for w in range(1, 54)} 
        medjusuma = 0

        if "Abesence" not in emp:
            continue
            
        for abs_item in emp["Abesence"]:
            try:
                start = date.fromisoformat(abs_item.get("start"))
                end = date.fromisoformat(abs_item.get("end"))
            except (ValueError, TypeError):
                continue

            # --- FILTER PO GODINI ---
            # Preskačemo ceo termin ako se uopšte ne preklapa sa izabranom godinom
            if start.year > selected_year or end.year < selected_year:
                continue

            # Ograničavamo opseg (ako odmor počinje u decembru prošle ili se završava u januaru sledeće)
            cur = max(start, date(selected_year, 1, 1))
            actual_end = min(end, date(selected_year, 12, 31))
                
            while cur <= actual_end:
                # Vikendi i Praznici
                if cur.weekday() >= 5 or cur in holidays_set:
                    pass 
                else:
                    week = cur.isocalendar().week
                    
                    # Korekcija za isocalendar: 1. januar može biti 52. nedelja prošle godine
                    # Ovde osiguravamo da upisujemo u matricu samo ako je week u range-u
                    if 1 <= week <= 53: 
                        if abs_item.get("type") == "homeOffice":
                            matrix2[emp_name][week] += 1
                        else:
                            matrix[emp_name, emp_freeday][week] += 1
                            medjusuma += 1
                
                cur += timedelta(days=1)

        demo[emp_name] = medjusuma
        emp_remain[emp_name] = emp_freeday - demo[emp_name]
                    
    return render_template("absence_matrix.html", 
                           matrix=matrix, 
                           matrix2=matrix2, 
                           emp_remain=emp_remain,
                           selected_year=selected_year)


@web_bp.route('/delete-absence/<string:absence_id>', methods=['POST'])
def delete_absence(absence_id):
    from models import CalendarEvents
    import json

    # 1. Pronalazimo sve zapise jer ne znamo unapred kojem zaposlenom pripada taj ID odsustva
    # (Ovo je neophodno jer je ID unutar JSON-a, a ne primarni ključ tabele)
    all_events = CalendarEvents.query.all()    
    found = False
    try:
        for record in all_events:
            if not record.JsonData:
                continue
                
            # Učitavamo listu odsustava (pazimo na navodnike)
            absences = json.loads(record.JsonData.replace("'", '"'))
            
            # 2. Filtriramo listu tako da IZBACIMO element sa traženim ID-em
            initial_count = len(absences)
            new_absences = [a for a in absences if a.get('id') != absence_id]
            
            # Ako je lista sada kraća, znači da smo pronašli i uklonili event
            if len(new_absences) < initial_count:
                record.JsonData = json.dumps(new_absences)
                db.session.commit()
                found = True
                break 

        if found:
            return {"status": "success"}, 200
        else:
            return {"status": "error", "message": "Event not found"}, 404

    except Exception as e:
        db.session.rollback()
        print(f"Delete Error: {e}")
        return {"status": "error", "message": str(e)}, 500




@web_bp.route('/team-knowledge')
def team_knowledge_list():
    # Proveravamo da li korisnik ima pravo da pristupi podacima ovog tima
    # (Opciono, zavisno od tvoje logike sesije)
    team_id = session['team_id']
    current_user_id = session['current_user_id'];
    user = TeamMember.query.get(current_user_id)     
    if  user.Role != 'Admin':
        flash("You do not have permission to view this  knowledge base.", "danger")
        return redirect(url_for('web.index'))

    # Dohvatanje svih dokumenata iz TeamKnowledge za dati TeamID
    # Koristimo .all() da dobijemo listu svih zapisa
    documents = TeamKnowledge.query.filter_by(TeamID=team_id).all()

    return render_template('knowledge_list.html', 
                           documents=documents, 
                           team_id=team_id,
                           scope='team')
@web_bp.route('/team-knowledge/view/<string:doc_id>')

@web_bp.route('/company-knowledge')
def company_knowledge_list():
    from models import Team, TeamMember, CompanyKnowledge
    
    # Preuzimamo podatke iz sesije
    team_id = session.get('team_id')
    current_user_id = session.get('current_user_id')
    generate_team_structural_md(team_id)
    if not current_user_id:
        return redirect(url_for('web.login'))

    user = TeamMember.query.get(current_user_id)
    
    # Provera Admin role (ako je to uslov za Company nivo)
    if user.Role != 'Admin':
        flash("You do not have permission to view Company knowledge base.", "danger")
        return redirect(url_for('web.index'))

    # Dohvatamo tim da bismo saznali CompanyID
    my_team = Team.query.filter_by(ID=team_id).first()
    
    if not my_team:
        flash("Team not found.", "warning")
        return redirect(url_for('web.index'))

    # Dohvatamo dokumente za celu kompaniju
    documents = CompanyKnowledge.query.filter_by(CompanyID=my_team.CompanyID).all()

    # Prosleđujemo 'scope' šablonu da bi znao koje dugmiće da iscrta
    return render_template('knowledge_list.html', 
                           documents=documents, 
                           team_id=team_id,
                           scope='company')

@web_bp.route('/knowledge/view-doc/<string:doc_id>')
def view_doc(doc_id):
    import markdown
    
    # 1. Prvo tražimo u Team tabeli
    doc = TeamKnowledge.query.filter_by(ID=doc_id).first()
    scope = 'team'
    
    # 2. Ako nije tamo, tražimo u Company tabeli
    if doc is None:
        doc = CompanyKnowledge.query.filter_by(ID=doc_id).first()
        scope = 'company'
    
    # 3. Ako dokument ne postoji ni u jednoj tabeli, vrati 404
    if not doc:
        from flask import abort
        abort(404)
        
    # 4. Konvertuj Markdown u HTML
    html_content = markdown.markdown(
        doc.FileContent or "", 
        extensions=['fenced_code', 'tables', 'nl2br']
    )
    
    return render_template('knowledge_view.html', 
                           doc=doc, 
                           html_content=html_content,
                           scope=scope)




@web_bp.route('/knowledge/edit/<string:scope>/<string:doc_id>')
@web_bp.route('/knowledge/create/<string:scope>')
def create_knowledge(scope, doc_id=None):
    
    doc = None
    if doc_id:
        if scope == 'team':
            doc = TeamKnowledge.query.get_or_404(doc_id)
        else:
            doc = CompanyKnowledge.query.get_or_404(doc_id)
    
    return render_template('knowledge_editor.html', scope=scope, doc=doc)

@web_bp.route('/knowledge/save', methods=['POST'])
def save_knowledge():
    scope = request.form.get('scope')
    doc_id = request.form.get('doc_id')
    print('datetime:',datetime.now(timezone.utc).replace(tzinfo=None))
    # Podacdatetime.now(timezone.utc)1i zajednički za oba modela
    data = {
        'FileName': request.form.get('FileName'),
        'FileContent': request.form.get('FileContent'),
        'Description': request.form.get('Description')
    }
    
    try:
        if scope == 'team':
            model_class = TeamKnowledge
            # Dodajemo TeamID samo ako je u pitanju novi dokument
            if not doc_id:
                data['TeamID'] = session.get('team_id')
            success_url = url_for('web.team_knowledge_list', team_id=session.get('team_id'))
        
        elif scope == 'company':
            model_class = CompanyKnowledge
            # Dodajemo CompanyID samo ako je u pitanju novi dokument
            if not doc_id:
                # Moramo dohvatiti CompanyID iz tima ili sesije
                from models import Team
                my_team = Team.query.get(session.get('team_id'))
                data['CompanyID'] = my_team.CompanyID
            success_url = url_for('web.company_knowledge_list')
        
        else:
            flash("Nevalidan opseg (scope).", "danger")
            return redirect(url_for('web.index'))

        if doc_id:  # --- EDIT MOD ---
            doc = model_class.query.get_or_404(doc_id)
            # Ažuriramo samo polja koja su dozvoljena za promenu
            doc.FileName = data['FileName']
            doc.FileContent = data['FileContent']
            doc.Description = data['Description']
            doc.DateLog = datetime.now(timezone.utc).replace(tzinfo=None)
            flash("Dokument uspešno ažuriran!", "success")
        else:  # --- CREATE MOD ---
            doc = model_class(**data)
            db.session.add(doc)
            flash("Novi dokument uspešno kreiran!", "success")

        db.session.commit()
        return redirect(success_url)

    except Exception as e:
        db.session.rollback()
        print(f"Greška pri čuvanju: {str(e)}")
        flash(f"Greška: {str(e)}", "danger")
        return redirect(request.referrer)
@web_bp.route('/knowledge/delete/<string:scope>/<string:doc_id>', methods=['POST'])
def delete_knowledge(scope, doc_id):
    try:
        # 1. PRVO brišemo embeddinge iz AI baze
        # Ovo je ključno jer KnowledgeID referencira dokument koji brišemo
        KnowledgeEmbedding.query.filter_by(KnowledgeID=doc_id).delete()
        urlLink ='web.team_knowledge_list'
        # 2. Pronalazimo i brišemo sam dokument
        if scope == 'team':
            doc = TeamKnowledge.query.get(doc_id)
        else:
            doc = CompanyKnowledge.query.get(doc_id)
            urlLink ='web.company_knowledge_list'
            
        if doc:
            db.session.delete(doc)
            db.session.commit()
            flash("Document and its AI embeddings successfully deleted.", "success")
        else:
            flash("Document not found.", "warning")

    except Exception as e:
        db.session.rollback()
        flash(f"Error during deletion: {str(e)}", "danger")
        
    return redirect(url_for(urlLink, scope=scope))


@web_bp.route('/knowledge/process/<string:scope>')
def process_knowledge(scope):
    from openai import OpenAI
    
    import numpy as np 
    client = OpenAI(api_key=AIConfig.get('OPENAI_API_KEY'))
    team_id = session.get('team_id')
    company_id = Team.query.filter_by(ID=team_id).first().CompanyID

    

    try:
        # 1. Filtriramo samo dokumente koji su novi ili su menjani nakon poslednjeg procesiranja
        if scope == 'team':
            # Uzimamo dokumente gde je UpdateDate > LastProcessedAt ili LastProcessedAt is NULL
            documents = TeamKnowledge.query.filter(
                TeamKnowledge.TeamID == team_id,
                (TeamKnowledge.LastProcessedAt == None) | (TeamKnowledge.DateLog > TeamKnowledge.LastProcessedAt)
            ).all()
        else:
            documents = CompanyKnowledge.query.filter(
                CompanyKnowledge.CompanyID == company_id,
                (CompanyKnowledge.LastProcessedAt == None) | (CompanyKnowledge.DateLog > CompanyKnowledge.LastProcessedAt)
            ).all()

        if not documents:
            flash("All documents are up to date. No processing needed.", "info")
            return redirect(request.referrer)

        for doc in documents:
            # 2. BRIŠEMO STARE EMBEDDINGE SAMO ZA OVAJ SPECIFIČNI DOKUMENT
            # Ne brišemo ceo Scope više, jer čuvamo ostale validne embeddinge
            KnowledgeEmbedding.query.filter_by(KnowledgeID=doc.ID).delete()
            
            text = doc.FileContent or ""
            chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
            
            for chunk in chunks:
                response = client.embeddings.create(
                    model="text-embedding-3-large",
                    input=chunk
                )
                vector = np.array(response.data[0].embedding).astype('float32')
                
                new_emb = KnowledgeEmbedding(
                    KnowledgeID=doc.ID,
                    Scope=scope,
                    TeamID=team_id if scope == 'team' else None,
                    CompanyID=company_id if scope == 'company' else None,
                    ChunkText=chunk,
                    Embedding=vector.tobytes()
                )
                db.session.add(new_emb)
            
            # 3. OZNAČAVAMO DOKUMENT KAO PROCESIRAN
            doc.LastProcessedAt = datetime.now(timezone.utc)
        
        db.session.commit()
        flash(f"Updated AI memory for {len(documents)} new/modified documents.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
        
    return redirect(request.referrer)

##############################################
## Generisanje strukture
##############################################




def generate_team_structural_md(team_id):
    # 1. Prikupljanje podataka
    from models import RiskHistory, RiskRegister
    team = Team.query.get(team_id)
    members = TeamMember.query.filter_by(TeamID=team_id).all()
    
    # Vreme za zaglavlje i DateLog
    now_local_tz = datetime.now()
    now_local_naive = now_local_tz.replace(tzinfo=None) # Za SQL DATETIME
    
    md = f"# ORGANIZACIONI KONTEKST TIMA: {team.Name if team else 'Nepoznat'}\n"
    md += f"*Automatski generisan izveštaj: {now_local_tz.strftime('%d.%m.%Y %H:%M')}*\n\n"
    md += "> **NAPOMENA:** Ovaj fajl je sistemski generisan. Ručne izmene će biti prebrisane pri sledećoj sinhronizaciji.\n\n"
    
    # 2. Iteracija po članovima - GRUPISANJE PODATAKA OKO OSOBE
    for m in members:
        md += f"## Team members: {m.Name}\n"
        #md += f"- **Uloga:** {m.Role}\n" /rola mi nije sada znacajna
        md += f"- **Email:** {m.Email}\n"
        if m.JsonData:
            md += f"- **Dodatni podaci:** {m.JsonData}\n"
        
        # --- CILJEVI ---
        my_goals = Goal.query.filter_by(TeamMemberID=m.ID).all()
        if my_goals:
            md += "####  Goals:\n"
            for g in my_goals:
                md += f"  - [{g.Year}] *{g.GoalType}*: {g.Description}\n"
        
        # --- ZADACI (Koristeći relaciju ili filter) ---
        my_tasks = Task.query.filter_by(AssignedTo=m.ID).all()
        if my_tasks:
            md += "#### Tasks:\n"
            
            for t in my_tasks:  
                communication_str = "None." 
                task_comments = TaskComment.query.filter_by(task_id=t.ID).order_by(TaskComment.created_at.asc()).all()
                # 2. Formatiranje komunikacije u jedan string
                if task_comments:
                    # Spajamo komentare u formatu: "Ime: Poruka (Datum)"
                    comm_list = [f"{c.author.Name}: {c.message} ({c.created_at.strftime('%d.%m %H:%M')})" for c in task_comments]
                    communication_str = " | ".join(comm_list)
               
                            
                md += f"  - {t.Status} **{t.Name}** | Desc: {t.Description} | Rok: {t.EndDate if t.EndDate else 'N/A'} | ClosingNote: {t.ClosingNote} | Communication:{communication_str} \n"
        
        # --- ODSUSTVA / KALENDAR ---
        #-- Brisem nepotreban GUID
        my_events = CalendarEvents.query.filter_by(TeamMemberID=m.ID).all()
        if my_events:
                    md += "#### Kalendar i Događaji:\n"
                    for e in my_events:
                        try:
                            # 1. Učitavamo JSON
                            data = json.loads(e.JsonData)
                            
                            # 2. Pošto je tvoj primer LISTA rečnika, prolazimo kroz nju
                            if isinstance(data, list):
                                events_list = data
                            else:
                                events_list = [data] # Pretvaramo u listu ako je jedan rečnik

                            for event_item in events_list:
                                # 3. Uklanjamo ID (guid) - proveravamo sve varijacije ključa
                                event_item.pop('id', None)
                                event_item.pop('ID', None)
                                
                                # 4. Formatiramo preostale ključeve (start, end, type...)
                                # npr. "type: homeOffice, start: 2026-02-18, end: 2026-02-19"
                                clean_info = ", ".join([f"{k}: {v}" for k, v in event_item.items()])
                                md += f"  - {clean_info}\n"
                                
                        except Exception as ex:
                            # U slučaju bilo kakve greške sa JSON-om, ispisujemo sirov podatak bez pucanja koda
                            md += f"  - {e.JsonData}\n"
        
        # --- BELEŠKE (Notes) ---
        my_notes = Notes.query.filter_by(TeamMemberID=m.ID).all()
        if my_notes:
            md += "#### Meeting Notes:\n"
            for n in my_notes:
                md += f"  - *{n.NoteDate}:* **{n.NoteTitle}** - {n.NoteContent}\n"

        md += "\n---\n\n"

    # --- TIMSKI BUDŽET (Nije vezan za pojedinca) ---
    team_budgets = Budget.query.filter_by(TeamID=team_id).all()
    if team_budgets:
        md += "## TEAM BUDGET (Overview)\n"
        
        for b in team_budgets:
            try:
                budget_json = json.loads(b.JsonData)
                rows = budget_json.get("data", [])
                cols = budget_json.get("columns", [])
                
                # 1. Izvlačenje naslova kolona (npr. Category, Description, Budget...)
                headers = [col.get("title", f"Col {i}") for i, col in enumerate(cols)]
                
                if rows:
                    # 2. Kreiranje Markdown zaglavlja
                    md += "| " + " | ".join(headers) + " |\n"
                    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                    
                    # 3. Dodavanje redova sa podacima
                    for row in rows:
                        # Čistimo podatke od potencijalnih None vrednosti i pretvaramo u string
                        clean_row = [str(item) if item is not None else "" for item in row]
                        md += "| " + " | ".join(clean_row) + " |\n"
                else:
                    md += "_No data._\n"
                    
            except Exception as e:
                md += f"  - [Error while reading budget data]: {b.JsonData}\n"
        
        md += "\n---\n"

    # --- RISK MANAGEMENT ---
    risk_registar = RiskRegister.query.filter_by(TeamID=team_id).all()
    if risk_registar:
        md += "# Risk Register Audit Report\n\n"
        md += f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        for r in risk_registar:
            try:
                # Glavni naslov rizika sa ID-jem radi lakše pretrage
                md += f"## Risk: {r.Title} (ID: #{r.RiskID})\n\n"
                
                # Osnovni podaci u obliku tabele za bolju preglednost u bazi znanja
                md += "| Property | Value |\n"
                md += "| :--- | :--- |\n"
                md += f"| **Status** | {r.RiskStatus} |\n"
                md += f"| **Current Score** | {r.RiskScore} |\n"
                md += f"| **Probability** | {r.Probability} |\n"
                md += f"| **Impact** | {r.Impact} |\n"
                md += f"| **Category** | {r.Category} |\n"
                md += f"| **Identified** |  {r.IdentifiedDate.strftime('%Y-%m-%d') if r.IdentifiedDate else 'N/A'} |\n"
                md += f"| **Due Date** | {r.DueDate.strftime('%Y-%m-%d') if r.DueDate else 'N/A'} |\n"
                ownerName = TeamMember.query.filter_by(ID=r.OwnerID).first().Name
                md += f"| **Owner** | {ownerName} |\n\n"
                
                # Sekcija za opis i strategiju
                md += "### Description\n"
                md += f"{r.RiskDescription if r.RiskDescription else '*No description.*'}\n\n"
                
                md += "### Mitigation Strategy\n"
                if r.MitigationStrategy:
                    # Koristimo blockquote za strategiju da bi se vizuelno istakla
                    md += f"> {r.MitigationStrategy}\n\n"
                else:
                    md += "*Not defined.*\n\n"

                md += "### Contigency plan\n"
                if r.ContingencyPlan:
                    # Koristimo blockquote za strategiju da bi se vizuelno istakla
                    md += f"> {r.ContingencyPlan}\n\n"
                else:
                    md += "*No contingency plan defined.*\n\n"

                
                
                last_history_entry = RiskHistory.query.filter_by(RiskID=r.RiskID)\
                                             .order_by(desc(RiskHistory.Timestamp))\
                                             .first()

                if last_history_entry:
                    md += "### ℹ️ Latest Update Notes\n"
                    # Čistimo komentar od None vrednosti
                    note = last_history_entry.ChangeNotes if last_history_entry.ChangeNotes else "No notes provided."
                    date_str = last_history_entry.Timestamp.strftime('%Y-%m-%d')
                    
                    md += f"*{note}* (updated on {date_str})\n\n"
                else:
                    md += "### ℹ️ Latest Update Notes\n"
                    md += "*No history records found for this risk.*\n\n"
                    
                
                md += "---\n\n" # Razdelnik između dva rizika
                
            except Exception as e:
                md += f"### ⚠️ [Error while reading risk data for Risk ID: {getattr(r, 'id', 'Unknown')}]\n"
                md += f"Details: {str(e)}\n\n---\n\n"




    # 3. UPIS U BAZU (COMMIT LOGIKA)
    filename = "SYSTEM_STRUCTURED_DATA.md"
    existing_doc = TeamKnowledge.query.filter_by(TeamID=team_id, FileName=filename).first()

    if existing_doc:
        # Ažuriramo postojeći
        existing_doc.FileContent = md
        existing_doc.Description = "Auto-generated my current data structure."
        existing_doc.DateLog = now_local_naive
        # Bitno: Resetujemo LastProcessedAt da bi FAISS procesor znao da treba ponovo da ga "indeksira"
        existing_doc.LastProcessedAt = None 
        print(f"Ažuriran sistemski fajl za tim {team_id}")
    else:
        # Pravimo novi zapis
        new_doc = TeamKnowledge(
            TeamID=team_id,
            FileName=filename,
            FileContent=md,
            Description="Auto-generated my current data structure.",
            DateLog=now_local_naive,
            LastProcessedAt=None # Inicijalno NULL da bi odmah bio spreman za Sync
        )
        db.session.add(new_doc)
        print(f"Kreiran novi sistemski fajl za tim {team_id}")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Greška pri čuvanju sistemskog MD fajla: {e}")
        raise e

    return md


@web_bp.route('/config-admin')
def config_admin():
    from models import ConfigData
    # 1. Provera prijave
    user_id = session.get('current_user_id')
    if not user_id:
        flash("Morate biti ulogovani da biste pristupili konfiguraciji.", "warning")
        return redirect(url_for('web.login'))

    company_id = session.get('company_id')
    team_id = session.get('team_id')

    # 2. Učitavanje inicijalnog konfiga (podrazumevano za Team, jer je on selektovan u HTML-u)
    # Prvo tražimo Team override
    initial_config = "{}"
    record = ConfigData.query.filter_by(TeamID=team_id).first()
    
    # Ako nema tima, možemo učitati Company kao fallback ili ostaviti prazno
    if not record:
        record = ConfigData.query.filter_by(CompanyID=company_id, TeamID=None).first()
    
    if record and record.ConfigData:
        try:
            # Formatiramo ga odmah u Pythonu da bi bio "lep" u editoru
            parsed = json.loads(record.ConfigData)
            initial_config = json.dumps(parsed, indent=4)
        except:
            initial_config = record.ConfigData

    # 3. Prikaz stranice sa prosleđenim podacima
    print('DEBUG: initial_config: ',initial_config)
    return render_template('config_admin.html', 
                           title="Config Manager", 
                           initial_config=initial_config)


@web_bp.route('/save-config-json', methods=['POST'])
def save_config_json():
    from models import ConfigData  # Proveri putanju do modela
    data = request.json
    level = data.get('level')          # 'team' ili 'company'
    config_string = data.get('configData') # JSON string iz Ace Editora
    
    # 1. Validacija JSON-a na strani servera (sigurnost pre svega)
    try:
        json.loads(config_string) 
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid JSON format"}), 400

    # 2. Identifikacija entiteta iz sesije
    company_id = session.get('company_id')
    team_id = session.get('team_id')

    if not company_id:
        return jsonify({"error": "No company context found in session"}), 403

    try:
        # 3. Pronalaženje postojećeg zapisa (Logic: Team vs Company)
        if level == 'team':
            if not team_id:
                return jsonify({"error": "No team context found"}), 400
            record = ConfigData.query.filter_by(TeamID=team_id).first()
        else:
            # Company level: TeamID mora biti NULL
            record = ConfigData.query.filter_by(CompanyID=company_id, TeamID=None).first()

        # 4. Ako ne postoji, kreiramo novi objekat
        if not record:
            record = ConfigData()
            # ID se generiše automatski u modelu (uuid4)
            if level == 'team':
                record.TeamID = team_id
                record.CompanyID = company_id # Povezujemo tim sa kompanijom
            else:
                record.CompanyID = company_id
                record.TeamID = None

        # 5. Ažuriranje podataka
        record.ConfigData = config_string
        record.DateLog = datetime.utcnow()

        db.session.add(record)
        db.session.commit()

        return jsonify({"success": True, "message": "Configuration saved"}), 200
        #return jsonify({"config": record.ConfigData if record else "{}"})

    except Exception as e:
        db.session.rollback()
        print(f"Error saving config: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    
@web_bp.route('/get-config-json')
def get_config_json():
    from models import ConfigData
    # 1. Uzimamo parametre i podatke iz sesije
    level = request.args.get('level', 'team')
    company_id = session.get('company_id')
    team_id = session.get('team_id')

    if not company_id:
        return jsonify({"error": "Nije pronađen ID kompanije u sesiji"}), 403

    try:
        # 2. Logika pretrage: Team ili Company
        if level == 'team':
            record = ConfigData.query.filter_by(TeamID=team_id).first()
        else:
            record = ConfigData.query.filter_by(CompanyID=company_id, TeamID=None).first()

        # 3. Priprema podataka za Ace Editor
        # Ace traži STRING. Ako u bazi imamo JSON string, šaljemo ga direktno.
        # Ako nema zapisa, šaljemo prazan JSON string.
        config_to_send = "{}"
        
        if record and record.ConfigData:
            # Proveravamo da li je u bazi validan JSON pre slanja (opciono, ali sigurno)
            try:
                # Samo potvrđujemo da je validan, ali ga šaljemo kao string!
                json.loads(record.ConfigData)
                config_to_send = record.ConfigData
            except:
                # Ako je u bazi slučajno "pokvaren" tekst, bar ga pošalji kao string
                config_to_send = str(record.ConfigData)

        return jsonify({"config": config_to_send})

    except Exception as e:
        print(f"Baza Greška: {str(e)}")
        return jsonify({"error": "Greška pri čitanju iz baze"}), 500
    
@web_bp.route('/get-latest-comments')
def get_latest_comments():
    from models import TaskComment, db
    
    # Uzimamo poslednjih 10 komentara (možeš dodati filter za CompanyID ako je potrebno)
    comments = TaskComment.query.order_by(TaskComment.created_at.desc()).limit(10).all()
    
    result = []
    for c in comments:
        result.append({
            "task_id": c.task_id,
            "author": c.author.Name,  # ili kako god se zove polje u tvojoj tabeli
            "comment": c.message[:50] + "...", # Skraćena verzija
            "time": c.created_at.strftime("%H:%M")
        })
    
    return jsonify({"comments": result, "count": len(result)})

@web_bp.route('/my-dashboard')
def show_dashboard():
    from util import get_allowed_views, rewrite_query_for_security
    user_id = session.get('current_user_id')
    team_id = session.get('team_id')
    company_id = session.get('company_id')
    from sqlalchemy import text
    
    # 1. Dohvati kartice
    cards = DashboardCard.query.filter_by(AuthorID=user_id).order_by(DashboardCard.Position).all()
    
    display_data = []

    for card in cards:
        result_value = ""
        card_format = "scalar" # Default format
        
        try:
            if card.CardType == 'SQL':
                allowed_views = get_allowed_views()
                secure_sql = rewrite_query_for_security(card.QueryOrPrompt, allowed_views, team_id)            
                print('DEBUG: secure_sql2:',secure_sql)
                result = db.session.execute(text(secure_sql), {"author_id": user_id, "team_id": team_id, "company_id": company_id})
                
                columns = result.keys()
                rows = result.fetchall()
                
                # Logika za tabelu vs skalar
                if len(columns) > 1 or len(rows) > 1:
                    result_value = [dict(zip(columns, row)) for row in rows]
                    card_format = "table"
                else:
                    result_value = rows[0][0] if rows else 0
                    card_format = "scalar"
                
            elif card.CardType == 'AI':
                result_value = f"Prompt: {card.QueryOrPrompt}\n HAS TO BE MANUALLY EXECUTED"
                card_format = "ai"

        except Exception as e:
            result_value = f"Greška: {str(e)}"
            card_format = "error"

        display_data.append({
            "id": card.ID,
            "title": card.Title,
            "value": result_value,
            "raw_query": card.QueryOrPrompt,
            "size": card.Size,
            "type": card.CardType,
            "model": card.Model,
            "format": card_format # Šaljemo format frontendu
        })

    return render_template('my-dashboard.html', cards=display_data)

@web_bp.route('/my-dashboard/save', methods=['POST'])
def save_card():
    import util 
    card_id = request.form.get('id')
    title = request.form.get('title')
    card_type = request.form.get('type')
    query = request.form.get('query')
    size = request.form.get('size')
    model = request.form.get('model')

    # --- VALIDACIJA SAMO ZA SQL KARTICE ---
    if card_type == 'SQL':
        is_valid, error_msg = util.validate_sql(query)
        if not is_valid:
            # Vraćamo korisnika nazad ili šaljemo error flash poruku
            # Pretpostavljam da koristiš flash za obaveštenja
            #flash(error_msg, "danger")
            return redirect(url_for('web.show_dashboard'))
            #return jsonify({"error": error_msg}), 400

    if card_id: # UPDATE
        card = DashboardCard.query.get(card_id)
        if card and card.AuthorID == session['current_user_id']:
            card.Title = title
            card.CardType = card_type
            card.QueryOrPrompt = query
            card.Size = size
            card.Model = model
    else: # INSERT
        new_card = DashboardCard(
            AuthorID=session['current_user_id'],
            TeamID=session['team_id'],
            Title=title,
            CardType=card_type,
            QueryOrPrompt=query,
            Size=size,
            Model=model
        )
        db.session.add(new_card)

    db.session.commit()
    return redirect(url_for('web.show_dashboard'))


@web_bp.route('/my-dashboard/run-card/<int:card_id>')
def run_single_card(card_id):
    from sqlalchemy import text
    from util import get_allowed_views, rewrite_query_for_security
    user_id = session.get('current_user_id')
    team_id = session.get('team_id')
    
    card = DashboardCard.query.get_or_404(card_id)
    user_id = session.get('current_user_id')
    team_id = session.get('team_id')
    company_id = session['company_id']
    
    result_value = ""
    try:
        if card.CardType == 'SQL':           
            #['v_task', 'v_absence', 'v_taskcomments', 'v_budget']
            allowed_views = get_allowed_views()
            secure_sql = rewrite_query_for_security(card.QueryOrPrompt, allowed_views, team_id)            
            print('DEBUG: secure_sql in run single card',secure_sql)
            result = db.session.execute(text(secure_sql), {"author_id": user_id, "team_id": team_id, "company_id": company_id})
            
            # Uzimamo nazive kolona
            columns = result.keys()
            # Uzimamo sve redove
            rows = result.fetchall()
            
            # Ako ima više od jedne kolone ili više od jednog reda, vraćamo tabelu
            if len(columns) > 1 or len(rows) > 1:
                data_list = [dict(zip(columns, row)) for row in rows]
                return jsonify({"value": data_list, "type": "table"})
            else:
                # Ako je ipak samo jedan podatak, vrati ga kao skalar radi kompatibilnosti
                val = rows[0][0] if rows else 0
                return jsonify({"value": val, "type": "scalar"})
        elif card.CardType == 'AI':
            #advisor = AIAdvisor(myModel=card.Model)
            from ai.context_service import ContextService
            current_context_service = ContextService(team_id=team_id, company_id=company_id)
            context_data = current_context_service.get_context(card.QueryOrPrompt)
            final_prompt = f"Context from database:\n{context_data}\n\nUser Question: {card.QueryOrPrompt}"
            messages = [                
                {"role": "user", "content": final_prompt}
            ]
            #call_openai(messages)
            result_value = call_openai(messages)  # 'advisor.ask(card.QueryOrPrompt)'
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"value": result_value})

@web_bp.route('/my-dashboard/delete/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    # Pronalazimo karticu ili vraćamo 404
    card = DashboardCard.query.get_or_404(card_id)
    
    # Sigurnosna provera: samo autor može da obriše svoju karticu
    if card.AuthorID != session.get('current_user_id'):
        return jsonify({"error": "Nemate dozvolu za brisanje ove kartice"}), 403
    
    try:
        db.session.delete(card)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@web_bp.route('/my-dashboard/reorder', methods=['POST'])
def reorder_cards():
    data = request.json
    new_order = data.get('order', []) # Lista [{id: 1, position: 0}, ...]

    try:
        for item in new_order:
            # Ažuriramo poziciju za svaku karticu direktno u bazi
            db.session.query(DashboardCard).filter_by(ID=item['id']).update({
                "Position": item['position']
            })
        
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@web_bp.route('/my-dashboard/validate-query', methods=['POST'])
def api_validate_query():
    data = request.get_json()
    query = data.get('query', '')
    
    # Pozivamo tvoju postojeću funkciju
    import util
    is_valid, error_msg = util.validate_sql(query)
    
    return jsonify({
        "isValid": is_valid,
        "error": error_msg
    })


@web_bp.route('/file-validator')
def file_validator_page():
    # Proveri da li se tvoj fajl tačno zove file_validator.html u templates folderu
    return render_template('file_validator.html')


@web_bp.route('/validate-xls', methods=['POST'])
def validate_xls():
    import pandas as pd
    import io
    from  util import audit_dataframe
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Nema fajla"}), 400
    
    file = request.files['file']
    
    try:
        # Čitamo Excel direktno iz memorije (bez čuvanja na disk)
        df = pd.read_excel(file)
        

        

        # Pretvaramo u Markdown
        # index=False da ne bismo imali kolonu sa brojevima redova
        # md_text = df.to_markdown(index=False)
        md_text = audit_dataframe(df)
        
        return jsonify({
            "success": True, 
            "markdown": md_text
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

@web_bp.route('/my-ai-costs')
def my_ai_costs():
    from sqlalchemy import func
    from models import AICallLog
    from datetime import datetime, timedelta
    
    user_id = session.get("current_user_id")
    if not user_id:
        return "Unauthorized", 401

    # Sanitizacija datuma
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        else:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
    except (ValueError, TypeError):
        # Ako korisnik unese loš format, vrati na default
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

    # Detaljna istorija
    logs = AICallLog.query.filter(
        AICallLog.TeamMemberID == str(user_id),
        AICallLog.CreatedAt.between(start_date, end_date)
    ).order_by(AICallLog.CreatedAt.desc()).all()

    # Agregacija po modelima
    stats_by_model = db.session.query(
        AICallLog.Model, 
        func.sum(AICallLog.EstimatedPrice).label('total_cost'),
        func.sum(AICallLog.TotalTokens).label('total_tokens')
    ).filter(
        AICallLog.TeamMemberID == str(user_id),
        AICallLog.CreatedAt.between(start_date, end_date)
    ).group_by(AICallLog.Model).all()

    # Agregacija po danima
    stats_by_day = db.session.query(
        func.cast(AICallLog.CreatedAt, db.Date).label('day'),
        func.sum(AICallLog.EstimatedPrice).label('daily_cost')
    ).filter(
        AICallLog.TeamMemberID == str(user_id),
        AICallLog.CreatedAt.between(start_date, end_date)
    ).group_by(func.cast(AICallLog.CreatedAt, db.Date)).order_by('day').all()

    # KONVERZIJA U JSON (Ovo šaljemo u JS)
    # Koristimo .get() ili indexe jer su ovo rezultati query-ja
    stats_by_model_json = [
        {"model": s[0] if s[0] else "Unknown", "total_cost": float(s[1] or 0), "total_tokens": int(s[2] or 0)} 
        for s in stats_by_model
    ]

    stats_by_day_json = [
        {"day": s[0].strftime('%d.%m.') if s[0] else "", "daily_cost": float(s[1] or 0)} 
        for s in stats_by_day
    ]

    return render_template('ai_costs.html', 
                            logs=logs, 
                            stats_by_model=stats_by_model_json,
                            stats_by_day=stats_by_day_json,
                            start_date=start_date.strftime('%Y-%m-%d'),
                            end_date=end_date.strftime('%Y-%m-%d'))

@web_bp.route('/admin')
def admin_panel():
    # Ovde možeš dodati proveru: if not session.get('is_admin'): return abort(403)
    return render_template('admin_panel.html')


def list_blueprint_routes(blueprint_name):
    routes = []
    # Pristupamo url_map preko current_app (unutar request contexta)
    for rule in current_app.url_map.iter_rules():
        # Blueprint rute u Flasku uvek imaju endpoint u formatu "blueprint_name.function_name"
        if rule.endpoint.startswith(f"{blueprint_name}."):
            routes.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods),
                "url": rule.rule,
                "function": current_app.view_functions[rule.endpoint].__name__
            })
    return routes

# Primer korišćenja u ruti:
@web_bp.route('/debug-routes')
def debug_routes():
    blueprint_routes = list_blueprint_routes('web')
    return {"admin_routes": blueprint_routes}

@web_bp.route('/prompts-archive')
def prompts_archive():
    from models import Prompt
    userID = session['current_user_id']
    # Uzimamo sve iz tabele Prompt, sortirano po datumu
    # Pretpostavljam da je db.session tvoj SQLAlchemy session
    prompts = Prompt.query.filter_by(TeamMemberID=userID).order_by(Prompt.CreatedDate.desc()).all()
    return render_template('my_prompts.html', prompts=prompts)

@web_bp.route('/risks')
def risk_list():
    """
    Prikazuje listu svih rizika filtriranih prema TeamID-u ulogovanog korisnika.
    Rizici sa najvećim RiskScore-om (Probability * Impact) se pojavljuju prvi.
    """
    from models import RiskRegister
    try:
        # 1. Uzimamo TeamID od trenutno ulogovanog korisnika (iz tvog User modela)
        user_team_id = session.get('team_id')
        
        # 2. Query: Filtriramo po timu i sortiramo opadajuće po RiskScore
        # Koristimo .desc() jer želimo da "vrući" rizici budu na vrhu
        risks = RiskRegister.query.filter_by(TeamID=user_team_id)\
                                   .order_by(desc(RiskRegister.RiskScore))\
                                   .all()
        print('-----------------------------------------')
        print(risks)
        print('-----------------------------------------')
        # 3. Renderujemo stranicu sa listom rizika
        return render_template('risk_list.html', risks=risks)
        
    except Exception as e:
        # Logovanje greške ako nešto krene po zlu sa bazom
        print(f"Error fetching risks: {e}")
        flash("Could not load risk register. Please check database connection.", "danger")
        return redirect(url_for('web.kanban'))
    
@web_bp.route('/risk/new', methods=['GET', 'POST'])
def new_risk():
    from models import RiskRegister
    if request.method == 'POST':
        # 1. Kreiramo instancu bez ikakvih parametara u init-u
        new_r = RiskRegister()
        
        # 2. Ručno dodeljujemo vrednosti iz forme (name atribute iz HTML-a)
        new_r.Title = request.form.get('Title')
        new_r.RiskDescription = request.form.get('RiskDescription')
        new_r.Category = request.form.get('Category')
        new_r.RiskStatus = request.form.get('RiskStatus', 'Identified')
        new_r.MitigationStrategy = request.form.get('MitigationStrategy')
        new_r.ContingencyPlan = request.form.get('ContingencyPlan')
        
        # 3. Konverzija brojeva (važno za RiskScore kalkulaciju u bazi)
        try:
            new_r.Probability = int(request.form.get('Probability', 1))
            new_r.Impact = int(request.form.get('Impact', 1))
        except (ValueError, TypeError):
            new_r.Probability = 1
            new_r.Impact = 1
            
        # 4. Automatski podaci (da ne mora korisnik da kuca)
        # OwnerID mora biti string 36 karaktera jer si tako stavio u modelu
        new_r.OwnerID = session.get('current_user_id') 
        new_r.TeamID = session.get('team_id') 
        
        # 5. Provera pre snimanja (da izbegnemo IntegrityError)
        if not new_r.Title:
            flash("Title is mandatory!", "danger")
            return render_template('risk_update.html', risk=None, is_new=True)
        try:
            db.session.add(new_r)
            db.session.commit()
            flash("Risk saved", "success")
            return redirect(url_for('web.risk_list'))
        except Exception as e:
            db.session.rollback()
            print(f"DATABASE ERROR: {e}")
            flash("Error, check error log.", "danger")
            
    return render_template('risk_update.html', risk=None, is_new=True)

@web_bp.route('/risk/update/<risk_id>', methods=['GET', 'POST']) # <risk_id> je ključno
def update_risk(risk_id): # Ovde mora pisati risk_id
    from models import RiskRegister, RiskHistory
    risk = RiskRegister.query.get_or_404(risk_id) 
    team = Team.query.filter_by(ID=session.get('team_id')).first()
    user = TeamMember.query.filter_by(ID=session.get('current_user_id')).first()        
    
    if request.method == 'POST':
        # Ručno ažuriranje pošto smo izbacili .update() metodu
        risk.Title = request.form.get('Title')
        risk.RiskDescription = request.form.get('RiskDescription')
        risk.Category = request.form.get('Category')
        risk.Probability = int(request.form.get('Probability', 1))
        risk.Impact = int(request.form.get('Impact', 1))
        risk.RiskStatus = request.form.get('RiskStatus')
        risk.MitigationStrategy = request.form.get('MitigationStrategy')
        risk.ContingencyPlan = request.form.get('ContingencyPlan')
        risk.DueDate = datetime.strptime(request.form.get('DueDate'), '%Y-%m-%d') if request.form.get('DueDate') else None

        history_entry = RiskHistory(
        RiskID = risk.RiskID,
        Probability = risk.Probability,
        Impact = risk.Impact,          
        RiskStatus = risk.RiskStatus,
        MitigationStrategy = risk.MitigationStrategy,
        ChangedBy = str(user.ID),
        ChangeNotes = request.form.get('Comment')
        )
        print('DEBUG:',history_entry)

        db.session.add(history_entry)
        db.session.commit()
        flash("Risk updated successfully!", "success")
        return redirect(url_for('web.risk_list'))

    return render_template('risk_update.html', risk=risk, teamName=team.Name ,is_new=False)

@web_bp.route('/risk/timeline/<risk_id>')
def risk_timeline(risk_id):
    from models import RiskRegister, RiskHistory
    risk = RiskRegister.query.get_or_404(risk_id)
    # Bitno je da je sortirano opadajuće po vremenu!
    history = RiskHistory.query.filter_by(RiskID=risk_id).order_by(RiskHistory.Timestamp.desc()).all()
    
    return render_template('risk_timeline.html', risk=risk, history=history)

@web_bp.route('/save-ai-task', methods=['POST'])
def save_ai_task():
    data = request.get_json()
    team_id = session.get('team_id')
    
    try:
        # Kreiranje nove instance Task modela
        new_task = Task(
            Name=data.get('Name'),
            Description=data.get('Description'),
            TaskCategoryID=data.get('TaskCategoryID'),
            ProjectName="Autotask",
            Status="Open",
            # Konverzija stringa u date objekat
            ActivationDate=datetime.strptime(data.get('ActivationDate'), '%Y-%m-%d').date() if data.get('ActivationDate') else None,
            EndDate=datetime.strptime(data.get('EndDate'), '%Y-%m-%d').date() if data.get('EndDate') else None,
            TeamID=team_id,
            DateLog=datetime.now(),
            TaskCommentsJSON=json.dumps([{"user": "System", "text": "Task automatically suggested by AI context."}])
        )
        
        db.session.add(new_task)
        db.session.commit()
        flash("Task successfully created!",'success')
        return jsonify({"success": True, "message": "Task successfully created!"}), 200
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving task: {str(e)}",'error')
        print(f"Error saving task: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@web_bp.route('/generate-task-modal')
def generate_task_modal():    
    import re
    from models import RiskRegister
    referrer = request.referrer  
    team_id = session.get('team_id')
    categories = TaskCategories.query.filter_by(TeamID=team_id).all()
    team_members = TeamMember.query.filter_by(TeamID=team_id)
    categories_text = ", ".join([f"{cat.ID}: {cat.Name}" for cat in categories])
    team_members_text = ", ".join([f"{member.ID}: {member.Name}" for member in team_members])

    #Ako je trenutno aktivna stranica o rizicima generisi output tj takava suggestion da moze da se sacuva
    if '/risk' in referrer:
        last_segment = referrer.split('/')[-1]
        guid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if bool(re.match(guid_pattern, last_segment, re.IGNORECASE)):
            risk_id = last_segment
            risk_data  = RiskRegister.query.filter_by(RiskID=risk_id).first()
            prompt = f"""
            Based on this risk: {risk_data.Title}
            Description: {risk_data.RiskDescription}
            Current strategy: {risk_data.MitigationStrategy}
        
            Suggest concrete 3 TASKS which is applicable for one of following topic.
            Return valid JSON format with a root key "tasks" containing a list of 3 objects.
            Each object must have following fields:
            Return valid JSON format with following fields:
            - Name: (Short title)
            - Description: (Detail description what should be done up to 300 characters)
            - TaskCategoryID: (Pick appropriate ID of categories: {categories_text})            
            - ProjectName: 'Autotask'
            - Status: 'Open'
            - ActivationDate: '{datetime.now().strftime('%Y-%m-%d')}'
            - EndDate: (suggest realistic deadline, npr. +14 days)
            """
        # u svakom drugom slucaju odradi standardan upit
        else:
            prompt = f"""
            Based on Active context                                
            Suggest concrete 3 TASKS which is applicable for one of following topic.
            Return valid JSON format with a root key "tasks" containing a list of 3 objects.
            Each object must have following fields:
            - Name: (Short title)
            - Description: (Detail description what should be done up to 300 characters)
            - TaskCategoryID: (Pick appropriate ID of categories: {categories_text})            
            - ProjectName: 'Autotask'
            - Status: 'Open'
            - ActivationDate: '{datetime.now().strftime('%Y-%m-%d')}'
            - EndDate: (suggest realistic deadline, npr. +14 days)
            """
   
    from ai.context_service import ContextService
    current_context_service = ContextService(team_id=team_id, company_id=session.get('company_id'))
    context_data = current_context_service.get_context(prompt)
    final_prompt = f"Context from database:\n{context_data}\n\nUser Question: {prompt}"
    messages = [                
            {"role": "user", "content": final_prompt}
        ]             
    result_value = call_openai(messages)  # 'advisor.ask(card.QueryOrPrompt)'
    print('DEBUG final prompt value:',final_prompt)
    print('DEBUG result value:',result_value)

    clean_json = re.sub(r'```json\s*|```', '', result_value).strip()        
    
    #suggestion = json.loads(clean_json)  //ovo je kad imam jedan task

    #ovo koristim kad zelim 3 taska
    data = json.loads(clean_json)
    print('DEBUG: my DATA:',data)
    suggestions = data.get('tasks', [])[:3]
    #suggestion = suggestions[0]
 
    
    return render_template('partials/task_modal_content.html', suggestions=suggestions,categories=categories, referrer=referrer)