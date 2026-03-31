import time
from datetime import datetime
from database import db
from models import AICallLog  # Putanja do tvog modela
from config import price_list     # Putanja do tvoje liste cena

class AICostService:
    @staticmethod
    def get_model_config(model_name):
        """Pronalazi cene za model (case-insensitive)."""
        if not model_name:
            return None
        return next((item for item in price_list if item['model'].lower() == model_name.lower()), None)

    @classmethod
    def log_call(cls, team_member_id, model_name, input_tokens, output_tokens, execution_time_ms, status="success", error_msg=None, prompt_text=None, ai_response=None, request_id=None):
        """
        Glavna metoda za izračunavanje cene i insert u bazu.
        """
        # 1. Pronađi cene u configu
        config = cls.get_model_config(model_name)
        
        # Ako model nije u listi, postavi cene na 0 da ne bi pukao insert
        in_p = config['input_price_per_1k'] if config else 0.0
        out_p = config['output_price_per_1k'] if config else 0.0
        
        # 2. Izračunaj procenjenu cenu (Price / 1000 * tokens)
        estimated_price = ((input_tokens / 1000) * in_p) + ((output_tokens / 1000) * out_p)

        try:
            # 3. Kreiraj objekat po tvom modelu
            new_log = AICallLog()
            new_log.TeamMemberID = str(team_member_id)
            new_log.Model = model_name
            new_log.InputTokens = input_tokens
            new_log.OutputTokens = output_tokens
            new_log.InputPricePer1K = in_p
            new_log.OutputPricePer1K = out_p
            new_log.EstimatedPrice = estimated_price
            new_log.RequestId = request_id
            new_log.ExecutionTimeMs = int(execution_time_ms)
            new_log.ExecutionStatus = status
            new_log.ErrorMessage = error_msg
            new_log.CreatedAt = datetime.utcnow()
            new_log.PromptText = prompt_text
            new_log.ResponseText = ai_response


            # 4. Save u bazu
            db.session.add(new_log)
            db.session.commit()
            return new_log
            
        except Exception as e:
            db.session.rollback()
            print(f"Greška pri logovanju AI poziva: {str(e)}")
            return None