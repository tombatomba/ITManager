from ai.myopenai import MyOpenAI
from openai import OpenAI
from config import Config
from AIConfig import AIConfig
from ai.presidio_service import PresidioService



#client = MyOpenAI(api_key=Config.OPENAI_API_KEY)

class AIAdvisor:
    def __init__(self, client = None, myModel = None, temperature = None, anonim=None) :
        if client is None:
            self.client = MyOpenAI(api_key=Config.OPENAI_API_KEY)   #ako klijent nije kreiran onda se desava povlacenje iz global configa
        else:
            self.client = client
        if myModel is None:
            self.myModel = 'gpt-4.1-mini'
        else:
            self.myModel = myModel
        
        if temperature is None:
            self.temperature = Config.MODEL_TEMPS.get(myModel,1)
        else:
            self.temperature = temperature
        
       # 4. Anonimizacija (Uvek definišemo atribut da izbegnemo AttributeError)
        self.presidio = None
        if anonim:
            try:
                self.presidio = PresidioService()
                print('DEBUG: Presidio service je podignut kako treba')
            except Exception as e:
                print(f'ERROR: Neuspešna inicijalizacija Presidio servisa: {e}')
               
        
    def answer(self, context: str, prompt: str):

        if hasattr(self, 'presidio') and self.presidio is not None:
            # VAŽNO: anonymize_text treba da DODAJE u mapu, a ne da je briše na početku 
            # ako planiraš više poziva za jedan zahtev.
            print('DEBUG: Presidio service je podignut')
            clean_context = self.presidio.anonymize_text(context)
            clean_prompt = self.presidio.anonymize_text(prompt)
        else:
            clean_context = context
            clean_prompt = prompt
        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant for an Manager. IMPORTANT: Maintain all [ENTITY_XXX] or [GLOBAL_XXX] tags in your response exactly as they appear. Do not translate or modify them."
            },
            {
                "role": "system",
                "content": f"Context:\n{clean_context}"
            },
            {
                "role": "user",
                "content": {clean_prompt}
            }
        ]
        
        response = self.client.chat_completions_create(
            model=self.myModel, #"gpt-4.1-mini",
            messages=messages,
            temperature=self.temperature
        )
        if hasattr(response, "usage"):
            print(f"Total tokens used for embeddings: {response.usage.total_tokens}")
        else:
            print("Token usage info not available in this SDK version.")
        
        returnValue = response.choices[0].message.content
        if self.presidio is not None:
            returnValue = self.presidio.deanonymize_text(returnValue)

        return returnValue
    
    
    def get_temperature_for_model(model_name):
        """Vraća temperaturu za dati model ili default vrednost"""
        return Config.MODEL_TEMPS[model_name]  # default 0.7 ako model nije pronađen
    
    def get_safe_response(self, messages, **kwargs):
        """
        Omotnica oko OpenAI klijenta koja automatski rukuje 
        anonimizacijom i de-anonimizacijom podataka.
        """
        print('DEBUG:Usao u get_safe_response')
    # 1. Provera i Anonimizacija (ako je Presidio podignut)
        if self.presidio:
            try:
                # Prolazimo kroz sve poruke (System, User, Assistant, History)
                for msg in messages:
                    if "content" in msg and isinstance(msg["content"], str):
                        # Važno: Ne resetujemo sesiju unutar petlje da bi tagovi bili konzistentni
                        msg["content"] = self.presidio.anonymize_text(msg["content"])
                
                print("DEBUG: Poruke su uspešno anonimizovane pre slanja.")
            except Exception as e:
                print(f"WARNING: Greška pri anonimizaciji: {e}. Šaljem originalni tekst.")

        # 2. Ažuriramo kwargs sa (potencijalno) novim porukama
        kwargs["messages"] = messages
        # Dodajemo model i temperaturu ako već nisu u kwargs
        kwargs.setdefault("model", self.myModel)
        kwargs.setdefault("temperature", self.temperature)

        # 3. Poziv OpenAI klijenta
        try:
            # Ovde pozivamo tvoj MyOpenAI wrapper
            response = self.client.chat_completions_create(**kwargs)
            
            # Izvlačenje teksta iz odgovora (prilagodi putanju svom wrapperu ako treba)
            ai_content = response.choices[0].message.content

            # 4. De-anonimizacija (Vraćanje pravih podataka)
            if self.presidio and ai_content:
                safe_content = self.presidio.deanonymize_text(ai_content)
                # Menjamo sadržaj u objektu odgovora da bi ostatak tvog koda radio normalno
                response.choices[0].message.content = safe_content
                print("DEBUG: Odgovor je uspešno de-anonimizovan.")
                
            return response

        except Exception as e:
            print(f"ERROR: Greška prilikom poziva OpenAI API-ja: {e}")
            raise e