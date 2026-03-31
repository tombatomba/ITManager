# test_query.py

from flask import Flask
from config import Config
from database import db
import os

def run_test():
    # 1. Kreiramo privremenu Flask aplikaciju za test
    app = Flask(__name__)
    app.config.from_object(Config)

    # 2. Inicijalizujemo bazu sa tom aplikacijom
    db.init_app(app)

    with app.app_context():
        try:
            # 3. Importujemo modele unutar context-a (važno!)
            from models import TeamMember, Team
            
            print("--- POKREĆEM TEST QUERY ---")
            
            # 4. Izvršavamo query
            # Koristimo execute/scalars jer je to najsigurniji način u novom SQLAlchemy-u
            users = db.session.execute(db.select(TeamMember)).scalars().all()
            
            if not users:
                print("⚠️  Baza je povezana, ali tabela 'TeamMember' je prazna.")
                # Provera da li uopšte postoje timovi, jer su oni FK
                teams_count = db.session.execute(db.select(db.func.count(Team.ID))).scalar()
                print(f"Informacija: U tabeli 'Team' imaš {teams_count} zapisa.")
            else:
                print(f"✅ Uspešno pronađeno {len(users)} korisnika:\n")
                for u in users:
                    print(f"ID: {u.ID} | Ime: {u.Name} | Email: {u.Email} | TeamID: {u.TeamID}")
            
        except Exception as e:
            print("❌ GREŠKA PRILIKOM TESTIRANJA:")
            print(str(e))

if __name__ == "__main__":
    run_test()