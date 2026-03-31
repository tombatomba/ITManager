from ai.myopenai import MyOpenAI
from openai import OpenAI
from config import Config
from AIConfig import AIConfig



#client = MyOpenAI(api_key=Config.OPENAI_API_KEY)

class AIAdvisor:
    def __init__(self, client = None, myModel = None, temperature = None) :
        if client is None:
            self.client = MyOpenAI(api_key=Config.OPENAI_API_KEY)
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
        
   
    def answer(self, context: str, prompt: str):
        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant for an IT Director."
            },
            {
                "role": "system",
                "content": f"Context:\n{context}"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        print('ai ADVISOR chat completion cp1')
        response = self.client.chat_completions_create(
            model=self.myModel, #"gpt-4.1-mini",
            messages=messages,
            temperature=self.temperature
        )
        if hasattr(response, "usage"):
            print(f"Total tokens used for embeddings: {response.usage.total_tokens}")
        else:
            print("Token usage info not available in this SDK version.")
        return response.choices[0].message.content
    
    
    def get_temperature_for_model(model_name):
        """Vraća temperaturu za dati model ili default vrednost"""
        return Config.MODEL_TEMPS[model_name]  # default 0.7 ako model nije pronađen