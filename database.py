# database.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Potpuna inicijalizacija baze sa hvatanjem grešaka."""
    try:
        # Povezivanje SQLAlchemy objekta sa Flask aplikacijom
        db.init_app(app)
        
        with app.app_context():
            # Uvozimo modele unutar konteksta da izbegnemo circular import
            import models
            
            # Pokušaj kreiranja tabela
            db.create_all()
            
            print("✅ Baza podataka i modeli su uspešno inicijalizovani.")
            
    except Exception as e:
        print("❌ GREŠKA prilikom inicijalizacije baze:")
        print(f"Detalji: {str(e)}")
        # Ovde možeš dodati i 'raise e' ako želiš da aplikacija potpuno stane 
        # u slučaju neuspešne baze