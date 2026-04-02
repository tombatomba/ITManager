import uuid
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

class PresidioService:
    def __init__(self, global_synonyms=None):
        # Podižemo prag osetljivosti na 0.5 da ne bi hvatao obične reči
        self.analyzer = AnalyzerEngine(default_score_threshold=0.5)
        self.anonymizer = AnonymizerEngine()

    # 1. Definisanje REGEX-a za JMBG (13 cifara u nizu)
        jmbg_pattern = Pattern(
            name="jmbg_pattern",
            regex=r"\b\d{13}\b", # Traži tačno 13 cifara oivičenih granicama reči
            score=0.95           # Visoka pouzdanost jer je struktura fiksna
        )

        # 2. Kreiranje Recognizer-a za JMBG
        jmbg_recognizer = PatternRecognizer(
            supported_entity="JMBG", 
            patterns=[jmbg_pattern],
            context=["jmbg", "maticni broj", "id number"] # Reči koje povećavaju šansu za pogodak
        )

        # 3. Registracija u postojeći analyzer
        self.analyzer.registry.add_recognizer(jmbg_recognizer)

        
        self.global_synonyms = global_synonyms or {}
        
        if self.global_synonyms:
            synonym_recognizer = PatternRecognizer(
                supported_entity="GLOBAL_SYNONYM", 
                deny_list=list(self.global_synonyms.keys())
            )
            self.analyzer.registry.add_recognizer(synonym_recognizer)

        self.current_session_map = {}

    def custom_replacement_logic(self, annotated_text):
        """Logika koja odlučuje koji tag ide za koji tekst"""
        val = annotated_text.strip()
        
        # 1. Globalni sinonimi
        if val in self.global_synonyms:
            placeholder = self.global_synonyms[val]
            self.current_session_map[placeholder] = val
            return placeholder
        
        # 2. Provera duplikata u istoj sesiji (da Nenad uvek bude isti ENTITY)
        for p_holder, original_val in self.current_session_map.items():
            if original_val == val:
                return p_holder
        
        # 3. Novi UUID za nove ljude/lokacije
        u_id = str(uuid.uuid4())[:6]
        placeholder = f"[ENTITY_{u_id}]"
        self.current_session_map[placeholder] = val
        return placeholder

    def anonymize_text(self, text, reset_map=False):
        if not text or not isinstance(text, str):
            return ""

        if reset_map:
            self.current_session_map = {}
        
        # Ograničavamo na bitne entitete + naše sinonime
        entities = ["PERSON", "EMAIL_ADDRESS", "LOCATION","JMBG"]
        
        results = self.analyzer.analyze(text=text, entities=entities, language='en')

        # KLJUČNI DEO: Definisanje operatora koji poziva tvoju logiku
        operators = {
            entity: OperatorConfig("custom", {"lambda": self.custom_replacement_logic})
            for entity in entities
        }

        # IZVRŠAVANJE ANONIMIZACIJE
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        
        return anonymized_result.text

    def deanonymize_text(self, ai_response):
        if not ai_response or not isinstance(ai_response, str):
            return ai_response

        output = ai_response
        # Sortiranje po dužini ključa (descending) da duži tagovi ne budu "pojedeni"
        sorted_placeholders = sorted(self.current_session_map.items(), key=lambda x: len(x[0]), reverse=True)
        
        for placeholder, original in sorted_placeholders:
            output = output.replace(placeholder, original)
        print('DEBUG: native',ai_response)        
        print('DEBUG: Deanonimized output',output)        
        return output

def run_test():
    globalni_recnik = {
        "ELPatron": "[PROJECT_X]",
        "Sava Osiguranje": "[CLIENT_1]",
        "Microsoft": "[VENDOR_MS]"
    }
    service = PresidioService(global_synonyms=globalni_recnik)
    originalni_tekst = "Can you check branislav tomic, he is person with jmbg: 2802980710110 and he did something with Elpatron project"
    # 1. ANONIMIZACIJA (Dobijamo tekst sa nasumičnim tagovima)
    anonimni_tekst = service.anonymize_text(originalni_tekst)
    print(f"Poslato na AI: {anonimni_tekst}")    
    # --- KLJUČNI DEO ---
    # Simuliramo da AI vraća TAČNO onaj tekst koji je dobio (echo test)
    # U realnosti, OpenAI će u svom odgovoru koristiti baš te tagove koje vidi u anonimni_tekst
    ai_response = f"Potvrđujem da je {anonimni_tekst} primljen."
    
    # 2. DE-ANONIMIZACIJA
    finalni_tekst = service.deanonymize_text(ai_response)
    print(f"Konačan rezultat: {finalni_tekst}")

    # Provera mape (samo za debug)
    print(f"\nTrenutna mapa u memoriji: {service.current_session_map}")

if __name__ == "__main__":
    run_test()