import base64, io
import google.generativeai as genai
from flask import Blueprint, request, jsonify, render_template, session, render_template_string
import pandas as pd
import requests
from AICostService import AICostService
from ai.myopenai import MyOpenAI
from AIConfig import AIConfig
import ai.myopenai
from ai.faiss_store import FaissStore
import traceback
from ai.context_service import ContextService
from ai.advisor import AIAdvisor
import json, time
import config
import struct1
import util

ai_bp = Blueprint("ai", __name__)

    

@ai_bp.route("/ai/tokenscount", methods=["POST"])
def tokenCounts():
    try:
        data = request.json
        print("Received data:", data)
        
        # Provjeri da li su podaci prisutni
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Provjeri da li postoji 'tekst' ključ
        if 'tekst' not in data:
            return jsonify({"error": "Missing 'tekst' key"}), 400
        
        tekst = data["tekst"]
        
        # Provjeri tip podatka
        if not isinstance(tekst, str):
            return jsonify({"error": "'tekst' must be a string"}), 400
        
        # Izračunaj tokene
        token_count = util.count_tokens(tekst)
        
        # Vrati kao JSON broj (ne dictionary)
        return jsonify(token_count)
        
    except Exception as e:
        print("Error in tokenCounts:", str(e))
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    

@ai_bp.route("/ai/ask", methods=["POST"])
def ask_ai():
    start_time = time.time() # 1. Početak merenja vremena
    # Instanciram advisor
    cli = MyOpenAI(api_key=AIConfig.get('OPENAI_API_KEY'))
    all_temps = AIConfig.get('MODEL_TEMPS')
    model_name = AIConfig.get('OPENAI_MODEL')
    target_temp = all_temps.get(model_name, 0.7)
    print('DEBUG: all temps',all_temps)
    print()
    advisor = AIAdvisor(client=cli,myModel=model_name,temperature=target_temp)

    print('DEBUG: model_temp:',target_temp)
    # Preuzimanje podataka iz request-a
    data = request.json
    prompt = data.get("prompt")
    page = data.get("page") 
    func = data.get("func")
    liveContextIncluded = data.get("liveContextStatus", False)
    print('DEBUG: data object in  AI/ASK method:',data);
    #print('liveContextIncluded:',liveContextIncluded)
    
    # Preuzimanje identiteta iz sesije
    # Podrazumevamo da su team_id i company_id upisani u sesiju pri logovanju
    user_id = session.get("current_user_id", "guest")
    user_team_id = session.get("team_id")
    user_company_id = session.get("company_id")

    # 1️⃣ DINAMIČKA INICIJALIZACIJA CONTEXT SERVISA
    # Ovim osiguravamo da AI vidi samo "svoje" Team i Company dokumente iz SQL baze
    from ai.context_service import ContextService
    current_context_service = ContextService(team_id=user_team_id, company_id=user_company_id)
    
    # Pretraga baze znanja (RAG) PROVERA DA LI UZIMAM U OBZIR i LIVE context
    context=''
    if liveContextIncluded:
        context = current_context_service.get_context(prompt)
        print('DEBUG:ukljucen zivi context')
    else:
        context = current_context_service.get_context2(prompt)
        print('DEBUG:nije ukljucen zivi context')
    
    context2 = util.cleanHtml2md(page) if page else "No page context available."

    # Podešavanje modela i temperature za zadati model iz configa
    selected_model = data.get("model", "gpt-4o-mini")
    advisor.myModel = selected_model
    print('DEBUG: selected_model',selected_model)
    print('DEBUG: selected temperature',all_temps.get(selected_model, 1))

    advisor.temperature = all_temps.get(selected_model, 1)

    # 2️⃣ UPRAVLJANJE ISTORIJOM ČETA (Session-based)
    if "chat_history" not in session:
        session["chat_history"] = {}
    
    chat_history = session["chat_history"]

    if str(user_id) not in chat_history:
        chat_history[str(user_id)] = []

    # 3️⃣ KREIRANJE SYSTEM PORUKA
    messages = [
        {
            "role": "system", 
            "content": "You are an IT Director assistant. Use the provided Knowledge Base and Page Context to give accurate answers."
        },
        {"role": "system", "content": f"KNOWLEDGE BASE (Global):\n{context}"},
        {"role": "system", "content": f"PAGE CONTEXT (Active context):\n{context2}"}
    ]

    # Dodajemo poslednjih 6 poruka (3 konverzacije) za održavanje kontinuiteta
    messages += chat_history[str(user_id)][-6:]
    messages.append({"role": "user", "content": prompt})

    # 4️⃣ PRIPREMA PARAMETARA ZA OPENAI (KWARGS)
    kwargs = {
        "model": advisor.myModel,
        "messages": messages,
        "temperature": advisor.temperature 
    }

    # Rukovanje Function Calling-om ako postoji
    if func and func.get("text"):
        try:
            functions = json.loads(func["text"])
            kwargs["functions"] = functions
            if func.get("name") and func["name"] != "auto":
                kwargs["function_call"] = {"name": func["name"]}
            else:
                kwargs["function_call"] = "auto"
        except json.JSONDecodeError as e:
            return jsonify({"error": f"Invalid structural output JSON: {e}"}), 400

    # 5️⃣ POZIV ADVISOR-A I GENERISANJE ODGOVORA
    try:
        answer_response = advisor.client.chat_completions_create(**kwargs)
        msg = answer_response.choices[0].message

        if hasattr(msg, "function_call") and msg.function_call:
            answer = msg.function_call.arguments
        else:
            answer = msg.content

 # --- LOGOVANJE (USPEH) ---
        duration_ms = (time.time() - start_time) * 1000
        
        # Uzimamo tačne podatke o tokenima iz odgovora
        in_tokens = answer_response.usage.prompt_tokens
        out_tokens = answer_response.usage.completion_tokens
        
        AICostService.log_call(
            team_member_id=session.get('current_user_id', 'unknown'), # Ili team_id, zavisi šta pratiš
            model_name=advisor.myModel,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            execution_time_ms=duration_ms,
            prompt_text=prompt, # Čuvamo finalni prompt sa kontekstom
            ai_response=answer,       # Čuvamo odgovor
            status="success"
        )

        

        # 6️⃣ AŽURIRANJE ISTORIJE I ČUVANJE U SESIJI
        chat_history[str(user_id)].append({"role": "user", "content": prompt})
        chat_history[str(user_id)].append({"role": "assistant", "content": answer})
        
        session["chat_history"] = chat_history
        session.modified = True

        return jsonify({"answer": answer})

    except Exception as e:
        print(f"AI Error: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


@ai_bp.route('/ai/openai', methods=['POST'])
def call_openai():
    start_time = time.time() # 1. Početak merenja vremena
    # Instanciram advisor
    cli = MyOpenAI(api_key=AIConfig.get('OPENAI_API_KEY'))
    advisor = AIAdvisor(client=cli,myModel=AIConfig.get('OPENAI_MODEL'),temperature=AIConfig.get('OPENAI_DEFAULT_TEMP'))
    try:
        # Preuzimanje podataka iz request-a
        data = request.json
        prompt = data.get('prompt')
        model = data.get('model', 'gpt-4o-mini')        
        history = data.get('history', [])
        include_context = data.get('include_context', False)
        file_bytes_str = data.get('file_bytes',None)
        file_name = data.get('file_name',None)                            
        print(f"DEBUG:  data: {data}")
        print(f"DEBUG:  session: {session}")
        md_table = ''

        if file_bytes_str:
            file_bytes = base64.b64decode(file_bytes_str)
            #print('DEBUG: file bytes:',file_bytes)
            # Sada koristiš pandas da pročitaš bytes
            df = pd.read_excel(io.BytesIO(file_bytes))
            md_table = df.to_markdown()
        
        print('DEBUG: markdown file:',md_table)

# --- DOHVATANJE KONTEKSTA ---
        final_prompt = prompt
        if include_context:
            user_team_id = session['team_id']
            company_id = session['company_id']
            current_context_service = ContextService(team_id=user_team_id, company_id=company_id)
            context_data = current_context_service.get_context(prompt)
            final_prompt = f"Context from database:\n{context_data}\n\nUser Question: {prompt}"

        #defaultni setup za open AI
        messages = [
            {"role": "system", "content": "You are an assistant. Use global context for rules, focus your answers on active discussion context"}
        ]        
        #SETUP ZA OBRADU FAJLA
        if file_name:
            messages = [
                {"role": "system", "content": f"Help with file analyis. Here is file context:{md_table} "}
                ]        



        
        messages.extend(util.last_n_messages(history, 6))        
        messages.append({"role": "user", "content": final_prompt})

        answer_response = advisor.client.chat_completions_create(
        model=advisor.myModel,
        messages=messages,
        temperature=advisor.temperature
    )
        
        answer = answer_response.choices[0].message.content

        # --- LOGOVANJE (USPEH) ---
        duration_ms = (time.time() - start_time) * 1000
        
        # Uzimamo tačne podatke o tokenima iz odgovora
        in_tokens = answer_response.usage.prompt_tokens
        out_tokens = answer_response.usage.completion_tokens
        
        AICostService.log_call(
            team_member_id=session.get('current_user_id', 'unknown'), # Ili team_id, zavisi šta pratiš
            model_name=advisor.myModel,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            execution_time_ms=duration_ms,
            prompt_text=final_prompt, # Čuvamo finalni prompt sa kontekstom
            ai_response=answer,       # Čuvamo odgovor
            status="success"
        )


        return jsonify({
            'answer': answer,
            'model': model,
            'tokens_used': answer_response.usage.total_tokens
        })
        
    except Exception as e:
        # --- LOGOVANJE (GREŠKA) ---
        duration_ms = (time.time() - start_time) * 1000
        AICostService.log_call(
            team_member_id=session.get('user_id', 'unknown'),
            model_name=model,
            input_tokens=0,
            output_tokens=0,
            execution_time_ms=duration_ms,
            prompt_text=prompt,
            ai_response=None,
            status="error",
            error_msg=str(e)
        )
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/ai/deepseek', methods=['POST'])
def call_deepseek():
    start_time = time.time() # 1. Početak merenja vremena
    try:
        data = request.json
        prompt = data.get('prompt')
        history = data.get('history', [])
        include_context = data.get('include_context', False)
        file_bytes_str = data.get('file_bytes',None)
        file_name = data.get('file_name',None)                            
        print(f"DEBUG:  data: {data}")
        print(f"DEBUG:  session: {session}")
        md_table = ''

        if file_bytes_str:
            file_bytes = base64.b64decode(file_bytes_str)
            #print('DEBUG: file bytes:',file_bytes)
            # Sada koristiš pandas da pročitaš bytes
            df = pd.read_excel(io.BytesIO(file_bytes))
            md_table = df.to_markdown()
        
        print('DEBUG: markdown file:',md_table)
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # --- DOHVATANJE KONTEKSTA ---
        final_prompt = prompt
        if include_context:
            user_team_id = session['team_id']
            company_id = session['company_id']
            current_context_service = ContextService(team_id=user_team_id, company_id=company_id)
            context_data = current_context_service.get_context(prompt)
            final_prompt = f"Context from database:\n{context_data}\n\nUser Question: {prompt}"
        
        messages = [
            {"role": "system", "content": "You are an IT Director assistant. Use global context for rules, focus your answers on active discussion context"}
        ]
        #SETUP ZA OBRADU FAJLA
        if file_name:
            messages = [
                {"role": "system", "content": f"Help with file analyis. Here is file context:{md_table} "}
                ]        

        messages.extend(util.last_n_messages(history, 6))
        
        messages.append({"role": "user", "content": final_prompt})

        #print('DEBUG: aiconfig:',AIConfig.all())
        #print('DEBUG:deepseek key:',AIConfig.get('DEEPSEEK_API_KEY'))
        # DeepSeek API poziv
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={
              #  'Authorization': f'Bearer {config.Config.DEEPSEEK_API_KEY}',  STARI KOD DA VIDIM DA LI RADI GLOBAL CONFIG
                'Authorization': f'Bearer {AIConfig.get('DEEPSEEK_API_KEY')}',  
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 1000
            },
            timeout=30  # Dodaj timeout
        )
        
        # Proveri status odgovora
        response.raise_for_status()  # Baci exception za 4xx/5xx odgovore
        
        # Parsiraj JSON odgovor
        data = response.json()
        
        # Izvuči odgovor
        if 'choices' in data and len(data['choices']) > 0:
            answer = data['choices'][0]['message']['content']
            tokens_used = data.get('usage', {}).get('total_tokens', 0)
        # Ekstrakcija tokena iz usage objekta
            usage = data.get('usage', {})
            in_tokens = usage.get('prompt_tokens', 0)
            out_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)

            # --- LOGOVANJE (USPEH) ---
            duration_ms = (time.time() - start_time) * 1000
            print('DEBUG:deepseek duration:',duration_ms )
            print('DEBUG:deepseek usage:',usage )
            AICostService.log_call(
                team_member_id=session.get('current_user_id', 'unknown'),
                model_name='deepseek-chat',
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                execution_time_ms=duration_ms,
                prompt_text=final_prompt,
                ai_response=answer,
                status="success"
            )
            
            return jsonify({
                'answer': answer,
                'tokens_used': tokens_used,
                'model': 'deepseek-chat'
            })
        else:
            duration_ms = (time.time() - start_time) * 1000
            AICostService.log_call(
            team_member_id=session.get('current_user_id', 'unknown'),
            model_name='deepseek-chat',
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            execution_time_ms=duration_ms,
            prompt_text=final_prompt,
            ai_response=answer,
            status="error"
            )
            return jsonify({'error': 'No response from DeepSeek API'}), 500
    except Exception as e:
        # --- UNIVERZALNO LOGOVANJE GRESKE ---
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Određujemo specifičan status kod i poruku na osnovu tipa greške
        error_msg = str(e)
        status_code = 500
        
        if isinstance(e, requests.exceptions.Timeout):
            error_msg = "DeepSeek API request timeout"
            status_code = 504
        elif isinstance(e, requests.exceptions.RequestException):
            error_msg = f"DeepSeek API request failed: {str(e)}"
        elif isinstance(e, KeyError):
            error_msg = f"Invalid response format: {str(e)}"

        # JEDAN poziv loggera za sve greške
        print('DEBUG:duration:',duration_ms )
        AICostService.log_call(
            team_member_id=session.get('user_id', 'unknown'),
            model_name='deepseek-chat',
            input_tokens=0,
            output_tokens=0,
            execution_time_ms=(time.time() - start_time) * 1000,
            prompt_text=prompt,
            ai_response=None,
            status="error",
            error_msg=error_msg
        )

    return jsonify({'error': error_msg}), status_code          
    
@ai_bp.route('/ai/claude', methods=['POST'])
def call_claude():
    start_time = time.time() # 1. Početak merenja vremena
    try:
        data = request.json
        prompt = data.get('prompt', '').strip()
        include_context = data.get('include_context', False)
        # Obezbedi da history uvek bude lista, čak i ako JS pošalje null
        history = data.get('history') or [] 
        file_bytes_str = data.get('file_bytes',None)
        file_name = data.get('file_name',None)                            
        print(f"DEBUG:  data: {data}")
        print(f"DEBUG:  session: {session}")
        md_table = ''

        if file_bytes_str:
            file_bytes = base64.b64decode(file_bytes_str)
            #print('DEBUG: file bytes:',file_bytes)
            # Sada koristiš pandas da pročitaš bytes
            df = pd.read_excel(io.BytesIO(file_bytes))
            md_table = df.to_markdown()
        
        print('DEBUG: markdown file:',md_table)

        if not prompt:
            return jsonify({"error": "Prompt is empty"}), 400

                # --- DOHVATANJE KONTEKSTA ---
        final_prompt = prompt
        if include_context:
            user_team_id = session['team_id']
            company_id = session['company_id']
            current_context_service = ContextService(team_id=user_team_id, company_id=company_id)
            context_data = current_context_service.get_context(prompt)
            final_prompt = f"Context from database:\n{context_data}\n\nUser Question: {prompt}"

        if file_name:
            final_prompt = final_prompt +f"\n\n File content:{md_table}"

        systemDesc = "Ti si AI asistent koji odgovara jasno i precizno."

        # Filtriranje istorije: Claude ne dozvoljava prazne poruke ili pogrešne role
        formatted_messages = []
        for msg in util.last_n_messages(history, 6):
            if msg.get('role') and msg.get('content'):
                formatted_messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })

        # Dodajemo trenutni (finalni) prompt
        formatted_messages.append({
            "role": "user",
            "content": final_prompt
        })
        model_name = data.get("model") 
        if not model_name:
            model_name = "claude-3-5-sonnet-20240620" # Trenutno najstabilniji model

        payload = {
            "model": model_name, # Proveri ime modela
            "max_tokens": data.get("max_tokens", 1024),
            "temperature": data.get("temperature", 0.7),
            "system": systemDesc,
            "messages": formatted_messages
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": AIConfig.get('ANTHROPIC_API_KEY'),
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )

        # Ako dobiješ 400, ispiši tačan razlog iz Anthropic-a u konzolu servera
        if response.status_code != 200:
            print(f"Claude API Error: {response.text}")
            return jsonify({"error": response.json().get('error', {}).get('message', 'Unknown error')}), response.status_code

        response_data = response.json()        
        answer = response_data["content"][0]["text"]
        usage = response_data.get("usage", {})
        in_tokens = usage.get("input_tokens", 0)
        out_tokens = usage.get("output_tokens", 0)

        # --- LOGOVANJE USPEHA ---
        duration_ms = (time.time() - start_time) * 1000
        AICostService.log_call(
            team_member_id=session.get('current_user_id', 'unknown'),
            model_name=model_name,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            execution_time_ms=duration_ms,
            prompt_text=final_prompt,
            ai_response=answer,
            status="success"
        )

        # ... ostatak tvog koda za response_data ...
        answer = response_data["content"][0]["text"]
        usage = response_data.get("usage", {})

        return jsonify({
            "answer": answer,
            "tokens_used": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            "model": response_data.get("model", payload["model"])
        })

    except Exception as e:
        # --- UNIVERZALNO LOGOVANJE GREŠKE ---
        duration_ms = (time.time() - start_time) * 1000
        error_msg = str(e)
        
        AICostService.log_call(
            team_member_id=session.get('current_user_id', 'unknown'),
            model_name=model_name,
            input_tokens=0,
            output_tokens=0,
            execution_time_ms=duration_ms,
            prompt_text=prompt,
            ai_response=answer,
            status="success"
        )
        print(f"Server Error: {error_msg}")
        return jsonify({"error": error_msg}), 500

@ai_bp.route('/ai/gemini', methods=['POST'])
def call_gemini():
    start_time = time.time()      
    try:
        data = request.json
        prompt = data.get('prompt', '').strip()
        include_context = data.get('include_context', False)
        history = data.get('history') or []
        file_bytes_str = data.get('file_bytes', None)
        file_name = data.get('file_name', None)

        md_table = ''
        if file_bytes_str:
            file_bytes = base64.b64decode(file_bytes_str)
            df = pd.read_excel(io.BytesIO(file_bytes))
            md_table = df.to_markdown(index=False)

        if not prompt:
            return jsonify({"error": "Prompt is empty"}), 400

        # --- DOHVATANJE KONTEKSTA ---
        final_prompt = prompt
        if include_context:
            user_team_id = session.get('team_id')
            company_id = session.get('company_id')
            current_context_service = ContextService(team_id=user_team_id, company_id=company_id)
            context_data = current_context_service.get_context(prompt)
            final_prompt = f"Context from database:\n{context_data}\n\nUser Question: {prompt}"

        if file_name:
            final_prompt = f"{final_prompt}\n\nFile content ({file_name}):\n{md_table}"

        # --- KONFIGURACIJA GEMINI-JA ---
        genai.configure(api_key=AIConfig.get('GOOGLE_API_KEY'))
        

        requested_model = data.get("model") 
        temp =  AIConfig.get('GOOGLE_TEMPERATURE',0.7)
        if requested_model:
            if "pro" in requested_model.lower():
                model_name = AIConfig.get('GOOGLE_PRO_MODEL',"gemini-1.5-pro")
            else:
                model_name = AIConfig.get('GOOGLE_FAST_MODEL',"gemini-1.5-flash")

        system_instruction = "Ti si AI asistent koji odgovara jasno i precizno. Ne trosi vise od 4000 tokena"
        model_obj = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )

        # --- FORMATIRANJE ISTORIJE ---
        gemini_history = []
        for msg in util.last_n_messages(history, 6):
            role = "user" if msg.get('role') == "user" else "model"
            if msg.get('content'):
                gemini_history.append({
                    "role": role,
                    "parts": [msg['content']]
                })

        chat = model_obj.start_chat(history=gemini_history)

        generation_config = genai.types.GenerationConfig(
            max_output_tokens=data.get("max_tokens", 4096),
            temperature=data.get("temperature", temp)
        )

        """ print("--- Dostupni Google Modeli ---")
        try:
            for m in genai.list_models():
                # Proveravamo da li model podržava 'generateContent' metodu
                if 'generateContent' in m.supported_generation_methods:
                    print(f"Model Name: {m.name}")
                    print(f"Display Name: {m.display_name}")
                    print(f"Description: {m.description}")
                    print("-" * 30)
        except Exception as e:
            print(f"Greška prilikom listanja: {e}") """
        
        print('DEBUG Gemini, model:',model_name)
        print('DEBUG Gemini, generation-config:',generation_config)
        # --- API POZIV ---
        response = chat.send_message(final_prompt, generation_config=generation_config)
        
        answer = response.text
        usage = response.usage_metadata
        in_tokens = usage.prompt_token_count
        out_tokens = usage.candidates_token_count

        # --- LOGOVANJE USPEHA ---
        duration_ms = (time.time() - start_time) * 1000
        AICostService.log_call(
            team_member_id=session.get('user_id', 'unknown'),
            model_name=model_name,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            execution_time_ms=duration_ms,
            prompt_text=final_prompt,
            ai_response=answer,
            status="success"
        )

        return jsonify({
            "answer": answer,
            "tokens_used": in_tokens + out_tokens,
            "model": model_name
        })

    except Exception as e:
        # --- UNIVERZALNO LOGOVANJE GRESKE ---
        duration_ms = (time.time() - start_time) * 1000
        error_msg = str(e)
        
        AICostService.log_call(
            team_member_id=session.get('user_id', 'unknown'),
            model_name=model_name,
            input_tokens=0,
            output_tokens=0,
            execution_time_ms=duration_ms,
            prompt_text=prompt if prompt else "N/A",
            ai_response=None,
            status="error",
            error_msg=error_msg
        )
        print(f"Gemini Server Error: {error_msg}")
        return jsonify({"error": error_msg}), 500

#poseban poziv openAI koji uzima u obzir Func
def call_openai(messages, func=None):
    start_time = time.perf_counter() # Početak merenja
    print('DEBUG:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX usao u call open api')
    cli = MyOpenAI(api_key=AIConfig.get('OPENAI_API_KEY'))
    # Uzimamo model iz configa ili direktno
    model_name = AIConfig.get('OPENAI_MODEL')
    advisor = AIAdvisor(client=cli, myModel=model_name, temperature=AIConfig.get('OPENAI_DEFAULT_TEMP'))
    
    kwargs = {
        "model": advisor.myModel,
        "messages": messages,
        "temperature": advisor.temperature,
    }

    # ⬅️ function calling samo ako func postoji
    if func and func.get("text"):
        kwargs["functions"] = func["text"]
        if func.get("name") and func["name"] != "auto":
            kwargs["function_call"] = {"name": func["name"]}
        else:
            kwargs["function_call"] = "auto"

    try:
        # --- SAMO API POZIV SE MERI ---
        response = advisor.client.chat_completions_create(**kwargs)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        message = response.choices[0].message
        usage = response.usage # OpenAI usage objekat
        
        # Određujemo šta je finalni odgovor za log
        final_content = message.function_call.arguments if message.function_call else message.content

        print('DEBUG: final_content u structured:',final_content)
        
        # --- LOGOVANJE USPEHA ---
        # Pošto je ovo pomoćna metoda, session ['user_id'] uzimamo iz globalnog Flask session-a      
        AICostService.log_call(
            team_member_id=session.get('current_user_id', 'system_func'),
            model_name=advisor.myModel,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            execution_time_ms=duration_ms,
            prompt_text=messages[-1]['content'] if messages else "N/A",
            ai_response=final_content,
            status="success"
        )

        if message.function_call:
            return message.function_call.arguments  # JSON string
        return message.content  # plain text

    except Exception as e:
        # --- LOGOVANJE GREŠKE ---
        duration_ms = (time.perf_counter() - start_time) * 1000        
        AICostService.log_call(
            team_member_id=session.get('user_id', 'system_func'),
            model_name=model_name,
            input_tokens=0,
            output_tokens=0,
            execution_time_ms=duration_ms,
            prompt_text=messages[-1]['content'] if messages else "N/A",
            ai_response=None,
            status="error",
            error_msg=str(e)
        )
        raise e # Ponovo bacamo grešku da bi je pozivaoac obradio
  

def call_openai_structured(messages, function_desc):
    func = {
        "text": [{
            "name": function_desc["name"],
            "description": function_desc.get("description", ""),
            "parameters": function_desc["parameters"]
        }],
        "name": "auto"
    }

    result = call_openai(messages, func)

    
    if not result:
        raise Exception("No function_call returned")

    return json.loads(result)


@ai_bp.route("/ai/render-template", methods=["POST"])
def render_template_from_string():
    payload = request.json
    
    data = json.loads(payload.get("data",""))    
    template_str = payload.get("template", "")

    try:
        rendered = render_template_string(template_str, **data)
        #print(rendered)
        return rendered
        
    
    except Exception as e:
        return f"Template error: {str(e)}", 400
    


@ai_bp.route('/ai/render_item', methods=['POST'])
def render_item():

    
    data = request.json

    try:
        # 1️⃣ Extract input
        prompt = data["prompt"]
        function_desc = data["functionCallJsonDesc"]
        template_str = data["JinjaTemplate"]

        # 2️⃣ Prepare messages
        messages = [
            {"role": "user", "content": prompt}
        ]

        # 3️⃣ Call OpenAI (structured output)
        arguments = call_openai_structured(messages, function_desc)
        print('-----arguments-----')
        print(arguments)
        print('-----end arguments-----')

        # 4️⃣ Render Jinja template with AI output
        rendered = render_template_string(template_str, **arguments)

        return jsonify({
            "success": True,
            "rendered": rendered,
            "arguments": arguments,
            "function_name": function_desc.get("name")
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    


# Pretpostavljam da koristiš blueprint pod nazivom 'ai'
@ai_bp.route('/ai/save-prompt', methods=['POST'])
def save_prompt():
    from models import Prompt
    from datetime import datetime
    from database import db
    data = request.json

    # 1. Izvlačenje podataka iz requesta
    user_prompt = data.get('prompt')
    ai_response = data.get('response')
    full_history = data.get('history')
    dynamic_context = data.get('dynamic_context')
    #print(ai_response)
    model_used = data.get('model')
    
    # 2. Provera da li imamo osnovne podatke
    if not user_prompt or not ai_response:
        return jsonify({"error": "Missing prompt or response content"}), 400

    try:
        # 3. Kreiranje novog objekta po tvom modelu
        # Koristimo PascalCase nazive kolona kako su definisani u tvom modelu
        new_entry = Prompt()
        new_entry.Prompt = user_prompt
        new_entry.Model = model_used
        new_entry.ChatHistory = full_history # Čuvamo odgovor AI-a ovde
        new_entry.TeamMemberID = session.get('current_user_id') # Uzmi ID ulogovanog korisnika
        new_entry.SavedMessage = ai_response
        new_entry.CreatedDate = datetime.now()
        
        # Ovi statusi mogu biti fiksni ili ih možeš slati sa frontenda
        new_entry.StaticContextIncluded = True
        new_entry.DynamicContextIncluded =  dynamic_context

        # 4. Snimanje u bazu podataka
        db.session.add(new_entry)
        db.session.commit()

        return jsonify({"message": "Successfully saved to favorites!", "id": new_entry.ID}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error saving prompt: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500