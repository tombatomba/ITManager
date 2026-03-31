import sys
import json
from datetime import datetime, date, timedelta
from database import db
from models import (
    Company, Team, TeamMember, TaskCategories, 
    Task, AIConfig, Budget
)
from werkzeug.security import generate_password_hash
from flask import Flask

app = Flask(__name__)
# OBAVEZNO: Ovde postavi svoj konekcioni string
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://bane:Administrator.11@.\\SQLEXPRESS/ElPatron?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def run_init(company_name, team_name, admin_email):
    with app.app_context():
        print(f"🔍 Inicijalizacija: {company_name} | {team_name} | {admin_email}")
        
        try:
            # 1. Kompanija
            company = Company.query.filter_by(CompanyName=company_name).first()
            if not company:
                company = Company(CompanyName=company_name, JsonData='{}')
                db.session.add(company)
                db.session.flush()

            # 2. Tim
            team = Team.query.filter_by(Name=team_name, CompanyID=company.ID).first()
            if not team:
                team = Team(Name=team_name, CompanyID=company.ID, JsonData='{}')
                db.session.add(team)
                db.session.flush()

            # 3. Admin Korisnik (John Doe sa tvojim emailom)
            admin_user = TeamMember.query.filter_by(Email=admin_email).first()
            if not admin_user:
                admin_user = TeamMember(
                    Name="John Doe",
                    Email=admin_email,
                    Role="Admin",
                    Password=generate_password_hash("Admin123!"),
                    TeamID=team.ID,
                    NeedPasswordChange=True,
                    Suspended=False
                )
                db.session.add(admin_user)
                db.session.flush()
                print(f"✅ Kreiran admin: {admin_email}")

            # 4. Demo Budžet (Samo dve stavke)
            budget_data = {
                "data": [
                    ["SW-DEV", "Website development", "TechCorp", 50000, 15000, 120000, 10000, 5000, "Yes"],
                    ["SW-LIC", "Office 365 licenses", "Microsoft", 12000, 11000, 0, 0, 0, "Yes"]
                ],
                "columns": [
                    {"type": "text", "title": "Category", "source": ["SW-DEV", "SW-LIC", "HW-EQUIP", "HW-LIC", "HOSTING", "SERVICES", "EDU", "OTHER"]},
                    {"type": "text", "title": "Description"},
                    {"type": "text", "title": "Vendor name"},
                    {"type": "numeric", "title": "Budget", "mask": "#.##0,00 €", "decimal": ","},
                    {"type": "numeric", "title": "Payed Q1", "mask": "#.##0,00 €", "decimal": ","},
                    {"type": "numeric", "title": "Payed Q2", "mask": "#.##0,00 €", "decimal": ","},
                    {"type": "numeric", "title": "Payed Q3", "mask": "#.##0,00 €", "decimal": ","},
                    {"type": "numeric", "title": "Payed Q4", "mask": "#.##0,00 €", "decimal": ","},
                    {"type": "dropdown", "title": "Status", "source": ["Yes", "No", "Pending"]}
                ]
            }

            existing_budget = Budget.query.filter_by(TeamID=team.ID).first()
            if not existing_budget:
                new_budget = Budget(
                    TeamID=team.ID,
                    JsonData=json.dumps(budget_data) # Pakujemo u string
                )
                db.session.add(new_budget)
                print("✅ Kreiran budžet sa dve demo stavke.")

            # 5. Osnovni AI Config
            if not AIConfig.query.filter_by(TeamID=team.ID).first():
                ai_cfg = AIConfig(
                    TeamID=team.ID,
                    JsonData='{"default_model": "models/gemini-flash-latest", "temperature": 0.7}'
                )
                db.session.add(ai_cfg)

            db.session.commit()
            print("\n🚀 Sistem uspešno spreman!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Greška: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uputstvo: python init_system.py \"Ime Kompanije\" \"Ime Tima\" \"admin@email.com\"")
    else:
        run_init(sys.argv[1], sys.argv[2], sys.argv[3])