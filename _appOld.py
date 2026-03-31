from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask import render_template, redirect, url_for, flash, session
from datetime import datetime, date

import struct1
from util import *
from struct1 import *
from functools import wraps

app = Flask(__name__)
app.secret_key = "neki_veoma_tajni_kljuc_12345"
# ==========================
# SQL Server konekcija
# ==========================
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://ITmanagerLogin:EstimatedTimeMinutes.1@demo?driver=ODBC+Driver+18+for+SQL+Server"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================
# MODELS
# ==========================
class User(db.Model):
    __tablename__ = 'Users'
    UserID = db.Column(db.Integer, primary_key=True)
    UserName = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(255), unique=True, nullable=False)
    Role = db.Column(db.String(50), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

class Category(db.Model):
    __tablename__ = 'Categories'
    CategoryID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.String(500))

class Project(db.Model):
    __tablename__ = 'Projects'
    ProjectID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(200), nullable=False)
    CategoryID = db.Column(db.Integer, db.ForeignKey('Categories.CategoryID'), nullable=False)
    Description = db.Column(db.String(1000))
    StartDate = db.Column(db.Date)
    EndDate = db.Column(db.Date)
    Status = db.Column(db.String(50), default='Active')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    __tablename__ = 'Tasks'
    TaskID = db.Column(db.Integer, primary_key=True)
    ProjectID = db.Column(db.Integer, db.ForeignKey('Projects.ProjectID'), nullable=False)
    Title = db.Column(db.String(200), nullable=False)
    Description = db.Column(db.String(1000))
    Priority = db.Column(db.Integer, default=3)
    Status = db.Column(db.String(50), default='Pending')
    DueDate = db.Column(db.Date)
    EstimatedTimeMinutes = db.Column(db.Integer)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, default=datetime.utcnow)

class TaskAssignment(db.Model):
    __tablename__ = 'TaskAssignments'
    TaskAssignmentID = db.Column(db.Integer, primary_key=True)
    TaskID = db.Column(db.Integer, db.ForeignKey('Tasks.TaskID'), nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), nullable=False)
    AssignedAt = db.Column(db.DateTime, default=datetime.utcnow)
    CompletedAt = db.Column(db.DateTime, nullable=True)

class TaskDependency(db.Model):
    __tablename__ = 'TaskDependencies'
    TaskDependencyID = db.Column(db.Integer, primary_key=True)
    TaskID = db.Column(db.Integer, db.ForeignKey('Tasks.TaskID'), nullable=False)
    DependsOnTaskID = db.Column(db.Integer, db.ForeignKey('Tasks.TaskID'), nullable=False)

class DailyTodo(db.Model):
    __tablename__ = 'DailyTodo'
    DailyTodoID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), nullable=False)
    TaskID = db.Column(db.Integer, db.ForeignKey('Tasks.TaskID'), nullable=False)
    TodoDate = db.Column(db.Date, nullable=False)
    Status = db.Column(db.String(50), default='Pending')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================
# HELPER FUNCTIONS
# ==========================
def commit_db():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

# ==========================
# Login LOGOUTLogic
# ==========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Ovde možeš povezati sa bazom korisnika, za primer koristimo statički login
        if username == "admin" and password == "admin":
            session['current_user_name'] = username
            flash(f"Welcome, {username}!", "success")
            return redirect(url_for('categories_web'))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('current_user_name', None)
    flash("You have been logged out", "info")
    return redirect(url_for('login'))

# ==========================
# CRUD ENDPOINTS TEMPLATE
# ==========================
# GET all / POST
@app.route('/API/users', methods=['GET', 'POST'])
@login_required
def users():
    if request.method == 'GET':
        all_users = User.query.all()
        return jsonify([{'UserID': u.UserID, 'UserName': u.UserName, 'Email': u.Email, 'Role': u.Role} for u in all_users])
    elif request.method == 'POST':
        data = request.json
        u = User(UserName=data['UserName'], Email=data['Email'], Role=data['Role'])
        db.session.add(u)
        commit_db()
        return jsonify({'message': 'User created', 'UserID': u.UserID})


@app.route("/users_web", methods=['GET', 'POST'])
def users_web():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email', '')
        role = request.form.get('role', '')

        if username:
            new_user = User(UserName=username, Email=email, Role=role)
            try:
                db.session.add(new_user)
                db.session.commit()
                flash("User added successfully!", "success")
            except Exception as e:
                handle_error(e, db, friendly_message="Unable to add user. Please try again.")
        return redirect(url_for('users_web'))

    # GET: list of users
    try:
        users = User.query.order_by(User.UserName).all()
    except Exception as e:
        handle_error(e, db, friendly_message="Unable to load users.")
        return redirect(url_for('login'))

    return render_template("users.html", users=users)

@app.route("/users_web/delete/<int:user_id>", methods=['POST'])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash("User deleted successfully!", "success")
        else:
            flash("User not found.", "danger")
    except Exception as e:
        handle_error(e, db, friendly_message="Unable to delete user.")

    return redirect(url_for('users_web'))

@app.route("/users_web/edit/<int:user_id>", methods=['GET', 'POST'])
def edit_user(user_id):
    try:
        # pokušaj da učitaš korisnika
        user = User.query.get(user_id)
        if user is None:
            flash("User not found.", "danger")
            return redirect(url_for('users_web'))
    except Exception as e:
        handle_error(e, db, "Unable to load user for editing.")
        return redirect(url_for('users_web'))

    if request.method == 'POST':
        # čitanje podataka iz forme
        username = request.form.get('UserName', '').strip()
        email = request.form.get('Email', '').strip()
        role = request.form.get('Role', '').strip()

        if not username or not email or not role:
            flash("Please fill in all required fields.", "danger")
            return render_template("edit_user.html", user=user)

        # ažuriranje polja
        user.UserName = username
        user.Email = email
        user.Role = role

        try:
            db.session.commit()
            flash("User updated successfully!", "success")
        except Exception as e:
            db.session.rollback()  # rollback ako commit ne uspe
            handle_error(e, db, "Unable to update user. Please try again.")

        return redirect(url_for('users_web'))

    # GET request → prikaz forme
    return render_template("edit_user.html", user=user)
    try:
        user = User.query.get(user_id)
    except Exception as e:
        handle_error(e, db, "Unable to load user for editing.")
        return redirect(url_for('users_web'))

    if user is None:
        flash("User not found.", "danger")
        return redirect(url_for('users_web'))

    if request.method == 'POST':
        user.UserName = request.form['Username']        
        user.Email = request.form.get('Email', '')
        user.Role = request.form.get('Role', '')

        try:
            db.session.commit()
            flash("User updated successfully!", "success")
        except Exception as e:
            handle_error(e, db, "Unable to update user.")
        return redirect(url_for('users_web'))

    return render_template("edit_user.html", user=user)

@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        username = request.form['username']
        email = request.form.get('email','')
        role = request.form.get('role','')
        new_user = User(UserName=username, Email=email, Role=role)
        db.session.add(new_user)
        db.session.commit()
        flash("User added successfully!", "success")
    except Exception as e:
        handle_error(e, db, friendly_message="Unable to add user.")
    return redirect(url_for('users_web'))


# GET by ID / PUT / DELETE
@app.route('/API/users/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def user_detail(id):
    u = User.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({'UserID': u.UserID, 'UserName': u.UserName, 'Email': u.Email, 'Role': u.Role})
    elif request.method == 'PUT':
        data = request.json
        u.UserName = data.get('UserName', u.UserName)
        u.Email = data.get('Email', u.Email)
        u.Role = data.get('Role', u.Role)
        commit_db()
        return jsonify({'message': 'User updated'})
    elif request.method == 'DELETE':
        db.session.delete(u)
        commit_db()
        return jsonify({'message': 'User deleted'})

# ==========================
# Slično možemo napraviti za sve ostale tabele
# ==========================
# Categories
@app.route('/API/categories', methods=['GET', 'POST'])
@login_required
def categories():
    if request.method == 'GET':
        all_categories = Category.query.all()
        return jsonify([{'CategoryID': c.CategoryID, 'Name': c.Name, 'Description': c.Description} for c in all_categories])
    elif request.method == 'POST':
        data = request.json
        c = Category(Name=data['Name'], Description=data.get('Description'))
        db.session.add(c)
        commit_db()
        return jsonify({'message': 'Category created', 'CategoryID': c.CategoryID})

@app.route('/categories_web', methods=['GET', 'POST'])
def categories_web():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')

        if name:
            new_cat = Category(Name=name, Description=description)
            try:
                db.session.add(new_cat)
                db.session.commit()
                flash("Category added successfully!", "success")
            except Exception as e:
                #db.session.rollback()  # very important!
                handle_error(e, db,friendly_message="Unable to add category. Please try again.")
                #flash(f"Error: {str(e.orig)}", "danger")  # show the DB error message
        return redirect(url_for('categories_web'))

    categories = Category.query.all()
    return render_template('categories.html', categories=categories)


@app.route('/API/categories/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def category_detail(id):
    c = Category.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({'CategoryID': c.CategoryID, 'Name': c.Name, 'Description': c.Description})
    elif request.method == 'PUT':
        data = request.json
        c.Name = data.get('Name', c.Name)
        c.Description = data.get('Description', c.Description)
        commit_db()
        return jsonify({'message': 'Category updated'})
    elif request.method == 'DELETE':
        db.session.delete(c)
        commit_db()
        return jsonify({'message': 'Category deleted'})

@app.route('/categories_web/delete/<int:id>', methods=['POST'])
def delete_category(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    try:
        db.session.commit()
        flash('Category deleted!', 'danger')
    except Exception as e:
        handle_error(e, db,friendly_message="Unable to add category. Please try again.")
    return redirect(url_for('categories_web'))

@app.route('/categories_web/edit/<int:id>', methods=['GET', 'POST'])
def edit_category(id):
    cat = Category.query.get_or_404(id)
    if request.method == 'POST':
        cat.Name = request.form['name']
        cat.Description = request.form.get('description', '')
        db.session.commit()
        flash('Category updated!', 'success')
        return redirect(url_for('categories_web'))
    return render_template('edit_category.html', category=cat)

# ==========================
# PROJECTS
# ==========================
@app.route('/API/projects', methods=['GET', 'POST'])
def projects():
    if request.method == 'GET':
        all_projects = Project.query.all()
        return jsonify([{
            'ProjectID': p.ProjectID,
            'Name': p.Name,
            'CategoryID': p.CategoryID,
            'Description': p.Description,
            'StartDate': str(p.StartDate),
            'EndDate': str(p.EndDate),
            'Status': p.Status
        } for p in all_projects])
    elif request.method == 'POST':
        data = request.json
        p = Project(
            Name=data['Name'],
            CategoryID=data['CategoryID'],
            Description=data.get('Description'),
            StartDate=data.get('StartDate'),
            EndDate=data.get('EndDate'),
            Status=data.get('Status', 'Active')
        )
        db.session.add(p)
        commit_db()
        return jsonify({'message': 'Project created', 'ProjectID': p.ProjectID})

@app.route('/API/projects/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def project_detail(id):
    p = Project.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'ProjectID': p.ProjectID,
            'Name': p.Name,
            'CategoryID': p.CategoryID,
            'Description': p.Description,
            'StartDate': str(p.StartDate),
            'EndDate': str(p.EndDate),
            'Status': p.Status
        })
    elif request.method == 'PUT':
        data = request.json
        p.Name = data.get('Name', p.Name)
        p.CategoryID = data.get('CategoryID', p.CategoryID)
        p.Description = data.get('Description', p.Description)
        p.StartDate = data.get('StartDate', p.StartDate)
        p.EndDate = data.get('EndDate', p.EndDate)
        p.Status = data.get('Status', p.Status)
        commit_db()
        return jsonify({'message': 'Project updated'})
    elif request.method == 'DELETE':
        db.session.delete(p)
        commit_db()
        return jsonify({'message': 'Project deleted'})

# ==========================
# TASKS
# ==========================
@app.route('/API/tasks', methods=['GET', 'POST'])
def tasks():
    if request.method == 'GET':
        all_tasks = Task.query.all()
        return jsonify([{
            'TaskID': t.TaskID,
            'ProjectID': t.ProjectID,
            'Title': t.Title,
            'Description': t.Description,
            'Priority': t.Priority,
            'Status': t.Status,
            'DueDate': str(t.DueDate),
            'EstimatedTimeMinutes': t.EstimatedTimeMinutes
        } for t in all_tasks])
    elif request.method == 'POST':
        data = request.json
        t = Task(
            ProjectID=data['ProjectID'],
            Title=data['Title'],
            Description=data.get('Description'),
            Priority=data.get('Priority', 3),
            Status=data.get('Status', 'Pending'),
            DueDate=data.get('DueDate'),
            EstimatedTimeMinutes=data.get('EstimatedTimeMinutes')
        )
        db.session.add(t)
        commit_db()
        return jsonify({'message': 'Task created', 'TaskID': t.TaskID})

@app.route('/API/tasks/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def task_detail(id):
    t = Task.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'TaskID': t.TaskID,
            'ProjectID': t.ProjectID,
            'Title': t.Title,
            'Description': t.Description,
            'Priority': t.Priority,
            'Status': t.Status,
            'DueDate': str(t.DueDate),
            'EstimatedTimeMinutes': t.EstimatedTimeMinutes
        })
    elif request.method == 'PUT':
        data = request.json
        t.ProjectID = data.get('ProjectID', t.ProjectID)
        t.Title = data.get('Title', t.Title)
        t.Description = data.get('Description', t.Description)
        t.Priority = data.get('Priority', t.Priority)
        t.Status = data.get('Status', t.Status)
        t.DueDate = data.get('DueDate', t.DueDate)
        t.EstimatedTimeMinutes = data.get('EstimatedTimeMinutes', t.EstimatedTimeMinutes)
        commit_db()
        return jsonify({'message': 'Task updated'})
    elif request.method == 'DELETE':
        db.session.delete(t)
        commit_db()
        return jsonify({'message': 'Task deleted'})

# ==========================
# TASK ASSIGNMENTS
# ==========================
@app.route('/API/taskassignments', methods=['GET', 'POST'])
def task_assignments():
    if request.method == 'GET':
        all_assignments = TaskAssignment.query.all()
        return jsonify([{
            'TaskAssignmentID': a.TaskAssignmentID,
            'TaskID': a.TaskID,
            'UserID': a.UserID,
            'AssignedAt': str(a.AssignedAt),
            'CompletedAt': str(a.CompletedAt) if a.CompletedAt else None
        } for a in all_assignments])
    elif request.method == 'POST':
        data = request.json
        a = TaskAssignment(
            TaskID=data['TaskID'],
            UserID=data['UserID'],
            CompletedAt=data.get('CompletedAt')
        )
        db.session.add(a)
        commit_db()
        return jsonify({'message': 'TaskAssignment created', 'TaskAssignmentID': a.TaskAssignmentID})

@app.route('/API/taskassignments/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def task_assignment_detail(id):
    a = TaskAssignment.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'TaskAssignmentID': a.TaskAssignmentID,
            'TaskID': a.TaskID,
            'UserID': a.UserID,
            'AssignedAt': str(a.AssignedAt),
            'CompletedAt': str(a.CompletedAt) if a.CompletedAt else None
        })
    elif request.method == 'PUT':
        data = request.json
        a.TaskID = data.get('TaskID', a.TaskID)
        a.UserID = data.get('UserID', a.UserID)
        a.CompletedAt = data.get('CompletedAt', a.CompletedAt)
        commit_db()
        return jsonify({'message': 'TaskAssignment updated'})
    elif request.method == 'DELETE':
        db.session.delete(a)
        commit_db()
        return jsonify({'message': 'TaskAssignment deleted'})

# ==========================
# TASK DEPENDENCIES
# ==========================
@app.route('/API/taskdependencies', methods=['GET', 'POST'])
def task_dependencies():
    if request.method == 'GET':
        all_deps = TaskDependency.query.all()
        return jsonify([{
            'TaskDependencyID': d.TaskDependencyID,
            'TaskID': d.TaskID,
            'DependsOnTaskID': d.DependsOnTaskID
        } for d in all_deps])
    elif request.method == 'POST':
        data = request.json
        d = TaskDependency(
            TaskID=data['TaskID'],
            DependsOnTaskID=data['DependsOnTaskID']
        )
        db.session.add(d)
        commit_db()
        return jsonify({'message': 'TaskDependency created', 'TaskDependencyID': d.TaskDependencyID})

@app.route('/API/taskdependencies/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def task_dependency_detail(id):
    d = TaskDependency.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'TaskDependencyID': d.TaskDependencyID,
            'TaskID': d.TaskID,
            'DependsOnTaskID': d.DependsOnTaskID
        })
    elif request.method == 'PUT':
        data = request.json
        d.TaskID = data.get('TaskID', d.TaskID)
        d.DependsOnTaskID = data.get('DependsOnTaskID', d.DependsOnTaskID)
        commit_db()
        return jsonify({'message': 'TaskDependency updated'})
    elif request.method == 'DELETE':
        db.session.delete(d)
        commit_db()
        return jsonify({'message': 'TaskDependency deleted'})



@app.route("/taskAssign_web")
def taskAssign_web():
    # Hardkodovani podaci (tvoj primer)
    employees = [
        {
            "EmployeeID": 1,
            "Name": "Marko Markovic",
            "Tasks": [
                {"TaskID": 101, "Title": "Fix API bug", "DateTo": "2025-02-03"},
                {"TaskID": 102, "Title": "Prepare report", "DateTo": "2025-02-10"},
            ]
        },
        {
            "EmployeeID": 2,
            "Name": "Jovana Petrovic",
            "Tasks": [
                {"TaskID": 103, "Title": "Database cleanup", "DateTo": "2025-01-28"}
            ]
        }
    ]

    # Neraspoređeni taskovi
    unassigned_tasks = [
        {"TaskID": 201, "Title": "Inventory check", "DateTo": "2025-03-02"},
        {"TaskID": 202, "Title": "Email campaign", "DateTo": "2025-02-12"}
    ]

    # Renderovanje našeg Jinja template-a
    return render_template("employees_tasks_cards.html", employees=employees,unassigned_tasks=unassigned_tasks )



@app.route("/task_chat/<int:task_id>")
def task_chat(task_id):
    # Hardkodovani primer taska
    task = {
        "TaskID": task_id,
        "TaskName": "Prepare Monthly Report",
        "DueDate": "2025-01-15",
        "Comments": [
            {
                "CommentID": 1,
                "UserName": "Marko",
                "Message": "Hej, počeo sam da radim na izveštaju.",
                "CreatedAt": "2025-01-10 10:32",
                "IsMine": False
            },
            {
                "CommentID": 2,
                "UserName": "Bane",
                "Message": "Super! Ja ću dodati finansijski deo.",
                "CreatedAt": "2025-01-10 10:35",
                "IsMine": True
            },
            {
                "CommentID": 3,
                "UserName": "Marko",
                "Message": "Odlično, javi ako ti treba nešto.",
                "CreatedAt": "2025-01-10 10:40",
                "IsMine": False
            },
             {
                "CommentID": 4,
                "UserName": "Bane",
                "Message": "Super! Ja ću dodati finansijski deo 2.",
                "CreatedAt": "2025-01-10 10:35",
                "IsMine": True
            },
            {
                "CommentID": 5,
                "UserName": "Bane",
                "Message": "Odlično, javi ako ti treba nešto 3.",
                "CreatedAt": "2025-01-10 10:40",
                "IsMine": True
            },
                       {
                "CommentID": 6,
                "UserName": "Bane",
                "Message": "Odlično, javi ako ti treba nešto 4.",
                "CreatedAt": "2025-01-10 10:40",
                "IsMine": True
            },
             {
                "CommentID": 7,
                "UserName": "Bane",
                "Message": "Super! Ja ću dodati finansijski deo 2.",
                "CreatedAt": "2025-01-10 10:35",
                "IsMine": True
            },
            {
                "CommentID": 8,
                "UserName": "Bane",
                "Message": "Odlično, javi ako ti treba nešto 3.",
                "CreatedAt": "2025-01-10 10:40",
                "IsMine": True
            },
                       {
                "CommentID": 9,
                "UserName": "Bane",
                "Message": "Odlično, javi ako ti treba nešto 4.",
                "CreatedAt": "2025-01-10 10:40",
                "IsMine": True
            }
        ]
    }

    return render_template("task_chat.html", task=task)

@app.route("/tasks_overview")
def tasks_overview():
    tasks = struct1.tasks    
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
        if assigned_filter and assigned_filter != t["AssignedTo"]:
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
    categories = Category.query.all()
    users =User.query.all()

    return render_template(
        "tasks_overview.html",
        tasks=filtered_tasks,
        categories=categories,
        users=users,
        today=today,
        filters=request.args
    )

@app.route("/tasks_overview/delete/<int:task_id>", methods=['POST'])
def delete_task(task_id):
    try:
        struct1.delete_task(task_id)     
        flash("Task deleted successfully!", "success")
        
    except Exception as e:
        handle_error(e, db, friendly_message="Unable to delete task.")

    return redirect(url_for('tasks_overview'))


@app.route("/task/new", methods=["GET", "POST"])
def new_task():
    categories = Category.query.all()   # iz DB
    users = User.query.all()            # iz DB

    if request.method == "POST":
        # Automatski ID
        next_id = max(t["TaskID"] for t in struct1.tasks) + 1 if struct1.tasks else 1

        task = {
            "TaskID": next_id,
            "TaskName": request.form.get("TaskName"),
            "TaskCategory": request.form.get("TaskCategory"),
            "CreatedDate": request.form.get("CreatedDate"),
            "EndDate": request.form.get("EndDate"),
            "ActivationDate": request.form.get("ActivationDate"),
            "AssignedTo": request.form.get("AssignedTo"),
        }

        struct1.add_task(task)

        flash("New task created!", "success")
        return redirect(url_for("tasks_overview"))
    
    
    



@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    # Hardkodovani primer, kasnije zameni sa DB query
    tasks = struct1.tasks
    task = next((t for t in tasks if t["TaskID"] == task_id), None)
    if not task:
        flash("Task not found!", "danger")
        return redirect(url_for("tasks_overview"))
    categories = Category.query.all()
    users =User.query.all()
    if request.method == "POST":
        try:
            task["TaskName"] = request.form.get("TaskName", task["TaskName"])
            task["TaskCategory"] = request.form.get("TaskCategory", task["TaskCategory"])
            task["CreatedDate"] = request.form.get("CreatedDate", task["CreatedDate"])
            task["EndDate"] = request.form.get("EndDate", task["EndDate"])
            task["ActivationDate"] = request.form.get("ActivationDate", task["ActivationDate"])
            task["AssignedTo"] = request.form.get("AssignedTo", task["AssignedTo"])

            # Ako koristiš DB:
            # db.session.commit()

            flash("Task updated successfully!", "success")
            return redirect(url_for("tasks_overview"))
        except Exception as e:
            handle_error(e, db, friendly_message="Unable to update task.")
            return redirect(url_for("tasks_overview"))

    return render_template("edit_task.html", task=task, categories=categories, users=users)


@app.route("/task/<int:task_id>/add_message", methods=["POST"])
def add_message(task_id):
    # Poruka iz forme
    message_text = request.form.get("message", "").strip()

    # U realnoj aplikaciji ovde bi isao INSERT u bazu
    # ali posto koristimo hardcodovani primer, samo logujemo:
    print(f"[DEBUG] New message for task {task_id}: {message_text}")

    # Vrati korisnika nazad na chat stranicu
    return redirect(url_for("task_chat", task_id=task_id))

# ==========================
# DAILY TODO
# ==========================
@app.route('/API/dailytodo', methods=['GET', 'POST'])
@login_required
def daily_todo():
    if request.method == 'GET':
        all_todos = DailyTodo.query.all()
        return jsonify([{
            'DailyTodoID': t.DailyTodoID,
            'UserID': t.UserID,
            'TaskID': t.TaskID,
            'TodoDate': str(t.TodoDate),
            'Status': t.Status
        } for t in all_todos])
    elif request.method == 'POST':
        data = request.json
        t = DailyTodo(
            UserID=data['UserID'],
            TaskID=data['TaskID'],
            TodoDate=data['TodoDate'],
            Status=data.get('Status', 'Pending')
        )
        db.session.add(t)
        commit_db()
        return jsonify({'message': 'DailyTodo created', 'DailyTodoID': t.DailyTodoID})

@app.route('/API/dailytodo/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def daily_todo_detail(id):
    t = DailyTodo.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'DailyTodoID': t.DailyTodoID,
            'UserID': t.UserID,
            'TaskID': t.TaskID,
            'TodoDate': str(t.TodoDate),
            'Status': t.Status
        })
    elif request.method == 'PUT':
        data = request.json
        t.UserID = data.get('UserID', t.UserID)
        t.TaskID = data.get('TaskID', t.TaskID)
        t.TodoDate = data.get('TodoDate', t.TodoDate)
        t.Status = data.get('Status', t.Status)
        commit_db()
        return jsonify({'message': 'DailyTodo updated'})
    elif request.method == 'DELETE':
        db.session.delete(t)
        commit_db()
        return jsonify({'message': 'DailyTodo deleted'})
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # kreira tabele ako ne postoje
    app.run(debug=True)