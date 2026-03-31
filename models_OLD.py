# models.py

from database import db
from datetime import datetime

# ==========================
# MODELI
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

# Dodajte funkciju za serijalizaciju (pomaže kod API-ja)
def serialize_model(instance, date_fields=None):
    """Pomoćna funkcija za serijalizaciju SQLAlchemy objekata u dict."""
    data = instance.__dict__.copy()
    data.pop('_sa_instance_state', None) # Uklanja SQLAlchemy interni ključ

    if date_fields:
        for field in date_fields:
            if field in data and data[field] is not None:
                data[field] = str(data[field])

    return data