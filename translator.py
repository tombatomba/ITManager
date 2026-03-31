from openai import OpenAI
from config import Config  # ili direktno os.getenv("OPENAI_API_KEY")
import os

class Translator:
    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4o-mini",  # brži i jeftiniji, ili "gpt-4o" za najbolji kvalitet
        source_language: str = "auto"
    ):
        """
        Inicijalizacija prevodioca.
        
        :param api_key: OpenAI API ključ (ako nije u Config ili env)
        :param model: Model za prevod (gpt-4o-mini preporučen za brzinu/cenu)
        :param source_language: "auto" za automatsko prepoznavanje ili npr. "sr" za srpski
        """
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.source_language = source_language

    def translate(
        self,
        text: str,
        target_language: str = "en",
        context: str = None
    ) -> str:
        """
        Prevedi tekst na ciljni jezik.
        
        :param text: Tekst za prevod (upit ili bilo šta drugo)
        :param target_language: Kod ciljnog jezika (default: "en" za engleski)
        :param context: Opcionalni kontekst za bolji prevod (npr. "IT kompanija, osiguranje")
        :return: Prevedeni tekst
        """
        if not text.strip():
            return text

        # Mapiranje popularnih jezika na pun naziv (za bolji prompt)
        lang_names = {
            "en": "English",
            "sr": "Serbian",
            "hr": "Croatian",
            "de": "German",
            "fr": "French",
            "es": "Spanish",
            "it": "Italian",
            "ru": "Russian",
            # dodaj ostale po potrebi
        }

        target_name = lang_names.get(target_language, target_language.capitalize())

        system_prompt = (
            f"You are an expert translator. Translate the user query into {target_name}. "
            "Preserve the original meaning, tone, and intent exactly. "
            "Do not add explanations, greetings, or any extra text. "
            "Return ONLY the translated text."
        )

        if context:
            system_prompt += f"\nContext: This is from an internal company knowledge base about {context}."

        user_message = text

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.0,  # za maksimalnu konzistentnost
                max_tokens=1000
            )
            translated = response.choices[0].message.content.strip()
            return translated

        except Exception as e:
            print(f"Greška pri prevodu: {e}")
            return text  # fallback: vrati original ako API ne radi

    # Bonus: specijalna metoda za RAG upite
    def translate_query(self, query: str, target_language: str = "es") -> str:
        """
        Posebno optimizovana za prevod upita u RAG sistemu.
        """
        return self.translate(
            text=query,
            target_language=target_language,
            context="insurance company internal IT and HR procedures"
        )


# Primer korišćenja (ako pokreneš fajl direktno)
if __name__ == "__main__":
    translator = Translator()

    upiti = [
        "Koje su obaveze IT službe za reviziju?",
        "Kada mogu da radim od kuće?",
        "Šta je KLIK aplikacija?",
        "Koliko traje task?"
    ]

    for upit in upiti:
        prevod = translator.translate_query(upit, "es")
        print(f"SR: {upit}")
        print(f"Es: {prevod}")
        print("-" * 60)