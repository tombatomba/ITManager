from openai import OpenAI
from ai.chat_logger import log_chat


class MyOpenAI:
    def __init__(self, **kwargs):
        # instancira pravi OpenAI client
        self._client = OpenAI(**kwargs)

    def chat_completions_create(self, **kwargs):
        response = self._client.chat.completions.create(**kwargs)

        messages = kwargs.get("messages", [])
        prompt = "\n".join(m.get("content", "") for m in messages)

        # ✔️ bezbedno čitanje usage
        usage = getattr(response, "usage", None)
        total_tokens = usage.total_tokens if usage else 0
        model = getattr(response,"model",None)
        

        answer = response.choices[0].message.content

        log_chat(prompt, answer, total_tokens, model)
        print('radi ovo')

        return response
    
    def __getattr__(self, name):
        if name == "chat_completions_create":
            return self.chat_completions_create
        return getattr(self._client, name)