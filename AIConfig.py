import json

class AIConfig:
    _data = {}

    @classmethod
    def load(cls, company_id, team_id):
        """Učitava i spaja konfiguraciju: Company (baza) + Team (override)"""
        # 1. Import unutar funkcije je obavezan da bi se izbegao Circular Import
        from models import ConfigData 

        try:
            # 2. Uzmi Company Defaults
            # Koristimo .first() i proveravamo postojanje
            company_rec = ConfigData.query.filter_by(CompanyID=company_id, TeamID=None).first()
            company_dict = {}
            if company_rec and company_rec.ConfigData:
                company_dict = json.loads(company_rec.ConfigData)

            # 3. Uzmi Team Override
            team_rec = ConfigData.query.filter_by(TeamID=team_id).first()
            team_dict = {}
            if team_rec and team_rec.ConfigData:
                team_dict = json.loads(team_rec.ConfigData)

            # 4. Spajanje (Team gazi Company)
            cls._data = {**company_dict, **team_dict}
            
            print(f"✅ AIConfig loaded. Keys: {list(cls._data.keys())}")
            return True
        except Exception as e:
            print(f"❌ Error loading AIConfig: {e}")
            return False

    @classmethod
    def get(cls, key, default=None):
        return cls._data.get(key, default)

    @classmethod
    def all(cls):
        return cls._data