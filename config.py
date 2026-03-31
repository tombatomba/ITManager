from datetime import datetime
from urllib.parse import quote_plus

class Config:
    """Osnovna konfiguracija aplikacije."""
    SECRET_KEY = "neki_veoma_tajni_kljuc_12345"
    
    # Konfiguracija za SQL Server
    # SERVER = ".\\SQLEXPRESS"
    # DATABASE = "ElPatron"
    # LOGIN = "bane"
    # PASSWORD = "Administrator.11"
    # ODBC_DRIVER = "ODBC Driver 17 for SQL Server"

    SQLALCHEMY_DATABASE_URI = (
        (
            "mssql+pyodbc://bane:Administrator.12@.\\SQLEXPRESS/ElPatron?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes"
        )
        #"mssql+pyodbc://ITmanagerLogin:EstimatedTimeMinutes.1@demo?driver=ODBC+Driver+18+for+SQL+Server"
        #"mssql+pyodbc://admin25:Tomic.branislav%40.1@demo2?driver=ODBC+Driver+18+for+SQL+Server"
    )


    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #---------------------
    # OPEN AI CONFIG
    #---------------------
    OPENAI_API_KEY = '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'
    OPENAI_URL = "https://api.openai.com/v1/chat/completions"
    OPENAI_MODEL="gpt-4.1-mini"
    OPENAI_INTRO="Answer as short as possible on given language"


    #---------------------
    # DS CONFIG
    #---------------------

    DEEPSEEK_API_KEY = 'sk-5f5bcbefe0384002874bda60d3f22a1d';
    DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions'; 
    DEEPSEEK_TEMPERATURE=0.7
    DEEPSEEK_INTRO = "Answer as short as possible on given language"



    ANTHROPIC_API_KEY = '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'

    MODEL_TEMPS = {
    'gpt-4o-mini': 0.2,
    'gpt-4o': 1.0,
    'gpt-5o-mini': 1.0,
    'gpt-4-turbo': 0.7,
    'gpt-3.5-turbo': 0.7,
    'gpt-4': 0.7,
    'gpt-4-32k': 0.7,
    'claude-3-opus': 0.7,
    'claude-3-sonnet': 0.7,
    'claude-3-haiku': 0.2,
    'gemini-pro': 0.7,
    'llama-3-70b': 0.7,
    'llama-3-8b': 0.2,
    'mixtral-8x7b': 0.7,
    'codellama': 0.2
    }

price_list = [
    {'model': 'babbage-002', 'input_price_per_1k': 0.0004, 'output_price_per_1k': 0.0004, 'provider': 'text-completion-openai'}
    ,{'model': 'chatgpt-4o-latest', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.015, 'provider': 'openai'}
    ,{'model': 'gpt-4o-transcribe-diarize', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'claude-3-5-haiku-20241022', 'input_price_per_1k': 0.0008, 'output_price_per_1k': 0.004, 'provider': 'anthropic'}
    ,{'model': 'claude-3-5-haiku-latest', 'input_price_per_1k': 0.001, 'output_price_per_1k': 0.005, 'provider': 'anthropic'}
    ,{'model': 'claude-haiku-4-5-20251001', 'input_price_per_1k': 0.001, 'output_price_per_1k': 0.005, 'provider': 'anthropic'}
    ,{'model': 'claude-haiku-4-5', 'input_price_per_1k': 0.001, 'output_price_per_1k': 0.005, 'provider': 'anthropic'}
    ,{'model': 'claude-3-5-sonnet-20240620', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'anthropic'}
    ,{'model': 'claude-3-5-sonnet-20241022', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'anthropic'}
    ,{'model': 'claude-3-5-sonnet-latest', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'anthropic'}
    ,{'model': 'claude-3-7-sonnet-20250219', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'anthropic'}
    ,{'model': 'claude-3-7-sonnet-latest', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'anthropic'}
    ,{'model': 'claude-3-haiku-20240307', 'input_price_per_1k': 0.00025, 'output_price_per_1k': 0.00125, 'provider': 'anthropic'}
    ,{'model': 'claude-3-opus-20240229', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'anthropic'}
    ,{'model': 'claude-3-opus-latest', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'anthropic'}
    ,{'model': 'claude-4-opus-20250514', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'anthropic'}
    ,{'model': 'claude-4-sonnet-20250514', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'anthropic'}
    ,{'model': 'claude-sonnet-4-5', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'anthropic'}
    ,{'model': 'claude-sonnet-4-5-20250929', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'anthropic'}
    ,{'model': 'claude-sonnet-4-6', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'anthropic'}
    ,{'model': 'claude-opus-4-1', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'anthropic'}
    ,{'model': 'claude-opus-4-1-20250805', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'anthropic'}
    ,{'model': 'claude-opus-4-20250514', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'anthropic'}
    ,{'model': 'claude-opus-4-5-20251101', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.025, 'provider': 'anthropic'}
    ,{'model': 'claude-opus-4-5', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.025, 'provider': 'anthropic'}
    ,{'model': 'claude-opus-4-6', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.025, 'provider': 'anthropic'}
    ,{'model': 'claude-opus-4-6-20260205', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.025, 'provider': 'anthropic'}
    ,{'model': 'claude-sonnet-4-20250514', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'anthropic'}
    ,{'model': 'codex-mini-latest', 'input_price_per_1k': 0.0015, 'output_price_per_1k': 0.006, 'provider': 'openai'}
    ,{'model': 'deepseek-chat', 'input_price_per_1k': 0.00028, 'output_price_per_1k': 0.00042, 'provider': 'deepseek'}
    ,{'model': 'deepseek-reasoner', 'input_price_per_1k': 0.00028, 'output_price_per_1k': 0.00042, 'provider': 'deepseek'}
    ,{'model': 'davinci-002', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.002, 'provider': 'text-completion-openai'}
    ,{'model': 'deepseek/deepseek-chat', 'input_price_per_1k': 0.00028, 'output_price_per_1k': 0.00042, 'provider': 'deepseek'}
    ,{'model': 'deepseek/deepseek-coder', 'input_price_per_1k': 0.00014, 'output_price_per_1k': 0.00028, 'provider': 'deepseek'}
    ,{'model': 'deepseek/deepseek-r1', 'input_price_per_1k': 0.00055, 'output_price_per_1k': 0.00219, 'provider': 'deepseek'}
    ,{'model': 'deepseek/deepseek-reasoner', 'input_price_per_1k': 0.00028, 'output_price_per_1k': 0.00042, 'provider': 'deepseek'}
    ,{'model': 'deepseek/deepseek-v3', 'input_price_per_1k': 0.00027, 'output_price_per_1k': 0.0011, 'provider': 'deepseek'}
    ,{'model': 'deepseek/deepseek-v3.2', 'input_price_per_1k': 0.00028, 'output_price_per_1k': 0.0004, 'provider': 'deepseek'}
    ,{'model': 'ft:babbage-002', 'input_price_per_1k': 0.0016, 'output_price_per_1k': 0.0016, 'provider': 'text-completion-openai'}
    ,{'model': 'ft:davinci-002', 'input_price_per_1k': 0.012, 'output_price_per_1k': 0.012, 'provider': 'text-completion-openai'}
    ,{'model': 'ft:gpt-3.5-turbo', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.006, 'provider': 'openai'}
    ,{'model': 'ft:gpt-3.5-turbo-0125', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.006, 'provider': 'openai'}
    ,{'model': 'ft:gpt-3.5-turbo-0613', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.006, 'provider': 'openai'}
    ,{'model': 'ft:gpt-3.5-turbo-1106', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.006, 'provider': 'openai'}
    ,{'model': 'ft:gpt-4-0613', 'input_price_per_1k': 0.03, 'output_price_per_1k': 0.06, 'provider': 'openai'}
    ,{'model': 'ft:gpt-4o-2024-08-06', 'input_price_per_1k': 0.00375, 'output_price_per_1k': 0.015, 'provider': 'openai'}
    ,{'model': 'ft:gpt-4o-2024-11-20', 'input_price_per_1k': 0.00375, 'output_price_per_1k': 0.015, 'provider': 'openai'}
    ,{'model': 'ft:gpt-4o-mini-2024-07-18', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0012, 'provider': 'openai'}
    ,{'model': 'ft:gpt-4.1-2025-04-14', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.012, 'provider': 'openai'}
    ,{'model': 'ft:gpt-4.1-mini-2025-04-14', 'input_price_per_1k': 0.0008, 'output_price_per_1k': 0.0032, 'provider': 'openai'}
    ,{'model': 'ft:gpt-4.1-nano-2025-04-14', 'input_price_per_1k': 0.0002, 'output_price_per_1k': 0.0008, 'provider': 'openai'}
    ,{'model': 'ft:o4-mini-2025-04-16', 'input_price_per_1k': 0.004, 'output_price_per_1k': 0.016, 'provider': 'openai'}
    ,{'model': 'gemini/gemini-live-2.5-flash-preview-native-audio-09-2025', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.002, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-robotics-er-1.5-preview', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-embedding-001', 'input_price_per_1k': 0.00015, 'output_price_per_1k': 0, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-1.5-flash', 'input_price_per_1k': 7.5e-05, 'output_price_per_1k': 0.0003, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-1.5-flash-001', 'input_price_per_1k': 7.5e-05, 'output_price_per_1k': 0.0003, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-1.5-flash-002', 'input_price_per_1k': 7.5e-05, 'output_price_per_1k': 0.0003, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-1.5-flash-latest', 'input_price_per_1k': 7.5e-05, 'output_price_per_1k': 0.0003, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-1.5-pro', 'input_price_per_1k': 0.0035, 'output_price_per_1k': 0.0105, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-1.5-pro-001', 'input_price_per_1k': 0.0035, 'output_price_per_1k': 0.0105, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-1.5-pro-002', 'input_price_per_1k': 0.0035, 'output_price_per_1k': 0.0105, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-1.5-pro-exp-0801', 'input_price_per_1k': 0.0035, 'output_price_per_1k': 0.0105, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-1.5-pro-latest', 'input_price_per_1k': 0.0035, 'output_price_per_1k': 0.00105, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.0-flash', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0004, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.0-flash-001', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0004, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.0-flash-lite', 'input_price_per_1k': 7.5e-05, 'output_price_per_1k': 0.0003, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.0-flash-lite-preview-02-05', 'input_price_per_1k': 7.5e-05, 'output_price_per_1k': 0.0003, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.0-flash-live-001', 'input_price_per_1k': 0.00035, 'output_price_per_1k': 0.0015, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.0-flash-preview-image-generation', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0004, 'provider': 'gemini'}      
    ,{'model': 'gemini/gemini-2.5-flash', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-flash-image-preview', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.03, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-3-pro-image-preview', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.012, 'provider': 'gemini'}
    ,{'model': 'gemini/deep-research-pro-preview-12-2025', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.012, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-flash-lite', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0004, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-flash-lite-preview-09-2025', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0004, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-flash-preview-09-2025', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-flash-latest', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-flash-lite-latest', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0004, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-flash-lite-preview-06-17', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0004, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-flash-preview-04-17', 'input_price_per_1k': 0.00015, 'output_price_per_1k': 0.0006, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-flash-preview-05-20', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-flash-preview-tts', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-pro', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-computer-use-preview-10-2025', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-3-pro-preview', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.012, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-3-flash-preview', 'input_price_per_1k': 0.0005, 'output_price_per_1k': 0.003, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-3.1-pro-preview', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.012, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-3.1-pro-preview-customtools', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.012, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-pro-preview-03-25', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-pro-preview-05-06', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-pro-preview-06-05', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-pro-preview-tts', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-gemma-2-27b-it', 'input_price_per_1k': 0.00035, 'output_price_per_1k': 0.00105, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-gemma-2-9b-it', 'input_price_per_1k': 0.00035, 'output_price_per_1k': 0.00105, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-pro', 'input_price_per_1k': 0.00035, 'output_price_per_1k': 0.00105, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-pro-vision', 'input_price_per_1k': 0.00035, 'output_price_per_1k': 0.00105, 'provider': 'gemini'}
    ,{'model': 'gpt-3.5-turbo', 'input_price_per_1k': 0.0005, 'output_price_per_1k': 0.0015, 'provider': 'openai'}
    ,{'model': 'gpt-3.5-turbo-0125', 'input_price_per_1k': 0.0005, 'output_price_per_1k': 0.0015, 'provider': 'openai'}
    ,{'model': 'gpt-3.5-turbo-0301', 'input_price_per_1k': 0.0015, 'output_price_per_1k': 0.002, 'provider': 'openai'}
    ,{'model': 'gpt-3.5-turbo-0613', 'input_price_per_1k': 0.0015, 'output_price_per_1k': 0.002, 'provider': 'openai'}
    ,{'model': 'gpt-3.5-turbo-1106', 'input_price_per_1k': 0.001, 'output_price_per_1k': 0.002, 'provider': 'openai'}
    ,{'model': 'gpt-3.5-turbo-16k', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.004, 'provider': 'openai'}
    ,{'model': 'gpt-3.5-turbo-16k-0613', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.004, 'provider': 'openai'}
    ,{'model': 'gpt-3.5-turbo-instruct', 'input_price_per_1k': 0.0015, 'output_price_per_1k': 0.002, 'provider': 'text-completion-openai'}
    ,{'model': 'gpt-3.5-turbo-instruct-0914', 'input_price_per_1k': 0.0015, 'output_price_per_1k': 0.002, 'provider': 'text-completion-openai'}
    ,{'model': 'gpt-4', 'input_price_per_1k': 0.03, 'output_price_per_1k': 0.06, 'provider': 'openai'}
    ,{'model': 'gpt-4-0125-preview', 'input_price_per_1k': 0.01, 'output_price_per_1k': 0.03, 'provider': 'openai'}
    ,{'model': 'gpt-4-0314', 'input_price_per_1k': 0.03, 'output_price_per_1k': 0.06, 'provider': 'openai'}
    ,{'model': 'gpt-4-0613', 'input_price_per_1k': 0.03, 'output_price_per_1k': 0.06, 'provider': 'openai'}
    ,{'model': 'gpt-4-1106-preview', 'input_price_per_1k': 0.01, 'output_price_per_1k': 0.03, 'provider': 'openai'}
    ,{'model': 'gpt-4-1106-vision-preview', 'input_price_per_1k': 0.01, 'output_price_per_1k': 0.03, 'provider': 'openai'}
    ,{'model': 'gpt-4-32k', 'input_price_per_1k': 0.06, 'output_price_per_1k': 0.12, 'provider': 'openai'}
    ,{'model': 'gpt-4-32k-0314', 'input_price_per_1k': 0.06, 'output_price_per_1k': 0.12, 'provider': 'openai'}
    ,{'model': 'gpt-4-32k-0613', 'input_price_per_1k': 0.06, 'output_price_per_1k': 0.12, 'provider': 'openai'}
    ,{'model': 'gpt-4-turbo', 'input_price_per_1k': 0.01, 'output_price_per_1k': 0.03, 'provider': 'openai'}
    ,{'model': 'gpt-4-turbo-2024-04-09', 'input_price_per_1k': 0.01, 'output_price_per_1k': 0.03, 'provider': 'openai'}
    ,{'model': 'gpt-4-turbo-preview', 'input_price_per_1k': 0.01, 'output_price_per_1k': 0.03, 'provider': 'openai'}
    ,{'model': 'gpt-4-vision-preview', 'input_price_per_1k': 0.01, 'output_price_per_1k': 0.03, 'provider': 'openai'}
    ,{'model': 'gpt-4.1', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.008, 'provider': 'openai'}
    ,{'model': 'gpt-4.1-2025-04-14', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.008, 'provider': 'openai'}
    ,{'model': 'gpt-4.1-mini', 'input_price_per_1k': 0.0004, 'output_price_per_1k': 0.0016, 'provider': 'openai'}
    ,{'model': 'gpt-4.1-mini-2025-04-14', 'input_price_per_1k': 0.0004, 'output_price_per_1k': 0.0016, 'provider': 'openai'}
    ,{'model': 'gpt-4.1-nano', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0004, 'provider': 'openai'}
    ,{'model': 'gpt-4.1-nano-2025-04-14', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0004, 'provider': 'openai'}
    ,{'model': 'gpt-4.5-preview', 'input_price_per_1k': 0.075, 'output_price_per_1k': 0.15, 'provider': 'openai'}
    ,{'model': 'gpt-4.5-preview-2025-02-27', 'input_price_per_1k': 0.075, 'output_price_per_1k': 0.15, 'provider': 'openai'}
    ,{'model': 'gpt-4o', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-4o-2024-05-13', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.015, 'provider': 'openai'}
    ,{'model': 'gpt-4o-2024-08-06', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-4o-2024-11-20', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-4o-audio-preview', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-4o-audio-preview-2024-10-01', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-4o-audio-preview-2024-12-17', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-4o-audio-preview-2025-06-03', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-audio', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-audio-2025-08-28', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-audio-mini', 'input_price_per_1k': 0.0006, 'output_price_per_1k': 0.0024, 'provider': 'openai'}
    ,{'model': 'gpt-audio-mini-2025-10-06', 'input_price_per_1k': 0.0006, 'output_price_per_1k': 0.0024, 'provider': 'openai'}
    ,{'model': 'gpt-audio-mini-2025-12-15', 'input_price_per_1k': 0.0006, 'output_price_per_1k': 0.0024, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini', 'input_price_per_1k': 0.00015, 'output_price_per_1k': 0.0006, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-2024-07-18', 'input_price_per_1k': 0.00015, 'output_price_per_1k': 0.0006, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-audio-preview', 'input_price_per_1k': 0.00015, 'output_price_per_1k': 0.0006, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-audio-preview-2024-12-17', 'input_price_per_1k': 0.00015, 'output_price_per_1k': 0.0006, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-realtime-preview', 'input_price_per_1k': 0.0006, 'output_price_per_1k': 0.0024, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-realtime-preview-2024-12-17', 'input_price_per_1k': 0.0006, 'output_price_per_1k': 0.0024, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-search-preview', 'input_price_per_1k': 0.00015, 'output_price_per_1k': 0.0006, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-search-preview-2025-03-11', 'input_price_per_1k': 0.00015, 'output_price_per_1k': 0.0006, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-transcribe', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.005, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-tts', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-4o-realtime-preview', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.02, 'provider': 'openai'}
    ,{'model': 'gpt-4o-realtime-preview-2024-10-01', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.02, 'provider': 'openai'}
    ,{'model': 'gpt-4o-realtime-preview-2024-12-17', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.02, 'provider': 'openai'}
    ,{'model': 'gpt-4o-realtime-preview-2025-06-03', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.02, 'provider': 'openai'}
    ,{'model': 'gpt-4o-search-preview', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-4o-search-preview-2025-03-11', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-4o-transcribe', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-image-1.5', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-image-1.5-2025-12-16', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5.1', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5.1-2025-11-13', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5.1-chat-latest', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5.2', 'input_price_per_1k': 0.00175, 'output_price_per_1k': 0.014, 'provider': 'openai'}
    ,{'model': 'gpt-5.2-2025-12-11', 'input_price_per_1k': 0.00175, 'output_price_per_1k': 0.014, 'provider': 'openai'}
    ,{'model': 'gpt-5.2-chat-latest', 'input_price_per_1k': 0.00175, 'output_price_per_1k': 0.014, 'provider': 'openai'}
    ,{'model': 'gpt-5.2-pro', 'input_price_per_1k': 0.021, 'output_price_per_1k': 0.168, 'provider': 'openai'}
    ,{'model': 'gpt-5.2-pro-2025-12-11', 'input_price_per_1k': 0.021, 'output_price_per_1k': 0.168, 'provider': 'openai'}
    ,{'model': 'gpt-5-pro', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.12, 'provider': 'openai'}
    ,{'model': 'gpt-5-pro-2025-10-06', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.12, 'provider': 'openai'}
    ,{'model': 'gpt-5-2025-08-07', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5-chat', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5-chat-latest', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5-codex', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5.1-codex', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5.1-codex-max', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5.1-codex-mini', 'input_price_per_1k': 0.00025, 'output_price_per_1k': 0.002, 'provider': 'openai'}
    ,{'model': 'gpt-5.2-codex', 'input_price_per_1k': 0.00175, 'output_price_per_1k': 0.014, 'provider': 'openai'}
    ,{'model': 'gpt-5.3-codex', 'input_price_per_1k': 0.00175, 'output_price_per_1k': 0.014, 'provider': 'openai'}
    ,{'model': 'gpt-5-mini', 'input_price_per_1k': 0.00025, 'output_price_per_1k': 0.002, 'provider': 'openai'}
    ,{'model': 'gpt-5-mini-2025-08-07', 'input_price_per_1k': 0.00025, 'output_price_per_1k': 0.002, 'provider': 'openai'}
    ,{'model': 'gpt-5-nano', 'input_price_per_1k': 5e-05, 'output_price_per_1k': 0.0004, 'provider': 'openai'}
    ,{'model': 'gpt-5-nano-2025-08-07', 'input_price_per_1k': 5e-05, 'output_price_per_1k': 0.0004, 'provider': 'openai'}
    ,{'model': 'gpt-image-1', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0, 'provider': 'openai'}
    ,{'model': 'gpt-image-1-mini', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0, 'provider': 'openai'}
    ,{'model': 'gpt-realtime', 'input_price_per_1k': 0.004, 'output_price_per_1k': 0.016, 'provider': 'openai'}
    ,{'model': 'gpt-realtime-mini', 'input_price_per_1k': 0.0006, 'output_price_per_1k': 0.0024, 'provider': 'openai'}
    ,{'model': 'gpt-realtime-2025-08-28', 'input_price_per_1k': 0.004, 'output_price_per_1k': 0.016, 'provider': 'openai'}
    ,{'model': 'o1', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.06, 'provider': 'openai'}
    ,{'model': 'o1-2024-12-17', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.06, 'provider': 'openai'}
    ,{'model': 'o1-mini', 'input_price_per_1k': 0.0011, 'output_price_per_1k': 0.0044, 'provider': 'openai'}
    ,{'model': 'o1-mini-2024-09-12', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.012, 'provider': 'openai'}
    ,{'model': 'o1-preview', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.06, 'provider': 'openai'}
    ,{'model': 'o1-preview-2024-09-12', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.06, 'provider': 'openai'}
    ,{'model': 'o1-pro', 'input_price_per_1k': 0.15, 'output_price_per_1k': 0.6, 'provider': 'openai'}
    ,{'model': 'o1-pro-2025-03-19', 'input_price_per_1k': 0.15, 'output_price_per_1k': 0.6, 'provider': 'openai'}
    ,{'model': 'o3', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.008, 'provider': 'openai'}
    ,{'model': 'o3-2025-04-16', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.008, 'provider': 'openai'}
    ,{'model': 'o3-deep-research', 'input_price_per_1k': 0.01, 'output_price_per_1k': 0.04, 'provider': 'openai'}
    ,{'model': 'o3-deep-research-2025-06-26', 'input_price_per_1k': 0.01, 'output_price_per_1k': 0.04, 'provider': 'openai'}
    ,{'model': 'o3-mini', 'input_price_per_1k': 0.0011, 'output_price_per_1k': 0.0044, 'provider': 'openai'}
    ,{'model': 'o3-mini-2025-01-31', 'input_price_per_1k': 0.0011, 'output_price_per_1k': 0.0044, 'provider': 'openai'}
    ,{'model': 'o3-pro', 'input_price_per_1k': 0.02, 'output_price_per_1k': 0.08, 'provider': 'openai'}
    ,{'model': 'o3-pro-2025-06-10', 'input_price_per_1k': 0.02, 'output_price_per_1k': 0.08, 'provider': 'openai'}
    ,{'model': 'o4-mini', 'input_price_per_1k': 0.0011, 'output_price_per_1k': 0.0044, 'provider': 'openai'}
    ,{'model': 'o4-mini-2025-04-16', 'input_price_per_1k': 0.0011, 'output_price_per_1k': 0.0044, 'provider': 'openai'}
    ,{'model': 'o4-mini-deep-research', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.008, 'provider': 'openai'}
    ,{'model': 'o4-mini-deep-research-2025-06-26', 'input_price_per_1k': 0.002, 'output_price_per_1k': 0.008, 'provider': 'openai'}
    ,{'model': 'text-embedding-3-large', 'input_price_per_1k': 0.00013, 'output_price_per_1k': 0.0, 'provider': 'openai'}
    ,{'model': 'text-embedding-3-small', 'input_price_per_1k': 2e-05, 'output_price_per_1k': 0.0, 'provider': 'openai'}
    ,{'model': 'text-embedding-ada-002', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0, 'provider': 'openai'}
    ,{'model': 'text-embedding-ada-002-v2', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0, 'provider': 'openai'}
    ,{'model': 'vertex_ai/claude-3-5-haiku', 'input_price_per_1k': 0.001, 'output_price_per_1k': 0.005, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-3-5-haiku@20241022', 'input_price_per_1k': 0.001, 'output_price_per_1k': 0.005, 'provider': 'vertex_ai-anthropic_models'} 
    ,{'model': 'vertex_ai/claude-haiku-4-5@20251001', 'input_price_per_1k': 0.001, 'output_price_per_1k': 0.005, 'provider': 'vertex_ai-anthropic_models'} 
    ,{'model': 'vertex_ai/claude-3-5-sonnet', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-3-5-sonnet-v2', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}      
    ,{'model': 'vertex_ai/claude-3-5-sonnet-v2@20241022', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-3-5-sonnet@20240620', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-3-7-sonnet@20250219', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-3-haiku', 'input_price_per_1k': 0.00025, 'output_price_per_1k': 0.00125, 'provider': 'vertex_ai-anthropic_models'}        
    ,{'model': 'vertex_ai/claude-3-haiku@20240307', 'input_price_per_1k': 0.00025, 'output_price_per_1k': 0.00125, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-3-opus', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-3-opus@20240229', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'vertex_ai-anthropic_models'}    
    ,{'model': 'vertex_ai/claude-3-sonnet', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-3-sonnet@20240229', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}  
    ,{'model': 'vertex_ai/claude-opus-4', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-opus-4-1', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-opus-4-1@20250805', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'vertex_ai-anthropic_models'}  
    ,{'model': 'vertex_ai/claude-opus-4-5', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.025, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-opus-4-5@20251101', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.025, 'provider': 'vertex_ai-anthropic_models'}  
    ,{'model': 'vertex_ai/claude-opus-4-6', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.025, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-opus-4-6@default', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0.025, 'provider': 'vertex_ai-anthropic_models'}   
    ,{'model': 'vertex_ai/claude-sonnet-4-5', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-sonnet-4-6', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-sonnet-4-5@20250929', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-opus-4@20250514', 'input_price_per_1k': 0.015, 'output_price_per_1k': 0.075, 'provider': 'vertex_ai-anthropic_models'}    
    ,{'model': 'vertex_ai/claude-sonnet-4', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}
    ,{'model': 'vertex_ai/claude-sonnet-4@20250514', 'input_price_per_1k': 0.003, 'output_price_per_1k': 0.015, 'provider': 'vertex_ai-anthropic_models'}  
    ,{'model': 'vertex_ai/deepseek-ai/deepseek-v3.1-maas', 'input_price_per_1k': 0.00135, 'output_price_per_1k': 0.0054, 'provider': 'vertex_ai-deepseek_models'}
    ,{'model': 'vertex_ai/deepseek-ai/deepseek-v3.2-maas', 'input_price_per_1k': 0.00056, 'output_price_per_1k': 0.00168, 'provider': 'vertex_ai-deepseek_models'}
    ,{'model': 'vertex_ai/deepseek-ai/deepseek-r1-0528-maas', 'input_price_per_1k': 0.00135, 'output_price_per_1k': 0.0054, 'provider': 'vertex_ai-deepseek_models'}
    ,{'model': 'vertex_ai/openai/gpt-oss-120b-maas', 'input_price_per_1k': 0.00015, 'output_price_per_1k': 0.0006, 'provider': 'vertex_ai-openai_models'}  
    ,{'model': 'vertex_ai/openai/gpt-oss-20b-maas', 'input_price_per_1k': 7.5e-05, 'output_price_per_1k': 0.0003, 'provider': 'vertex_ai-openai_models'}   
    ,{'model': 'gpt-4o-mini-tts-2025-03-20', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-tts-2025-12-15', 'input_price_per_1k': 0.0025, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-transcribe-2025-03-20', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.005, 'provider': 'openai'}
    ,{'model': 'gpt-4o-mini-transcribe-2025-12-15', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.005, 'provider': 'openai'}
    ,{'model': 'gpt-5-search-api', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-5-search-api-2025-10-14', 'input_price_per_1k': 0.00125, 'output_price_per_1k': 0.01, 'provider': 'openai'}
    ,{'model': 'gpt-realtime-mini-2025-10-06', 'input_price_per_1k': 0.0006, 'output_price_per_1k': 0.0024, 'provider': 'openai'}
    ,{'model': 'gpt-realtime-mini-2025-12-15', 'input_price_per_1k': 0.0006, 'output_price_per_1k': 0.0024, 'provider': 'openai'}
    ,{'model': 'chatgpt-image-latest', 'input_price_per_1k': 0.005, 'output_price_per_1k': 0, 'provider': 'openai'}
    ,{'model': 'gemini/gemini-2.0-flash-lite-001', 'input_price_per_1k': 7.5e-05, 'output_price_per_1k': 0.0003, 'provider': 'gemini'}
    ,{'model': 'gemini-2.5-flash-native-audio-latest', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini-2.5-flash-native-audio-preview-09-2025', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini-2.5-flash-native-audio-preview-12-2025', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-flash-native-audio-latest', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini/gemini-2.5-flash-native-audio-preview-09-2025', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}  
    ,{'model': 'gemini/gemini-2.5-flash-native-audio-preview-12-2025', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}  
    ,{'model': 'gemini-2.5-flash-preview-tts', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini-flash-latest', 'input_price_per_1k': 0.0003, 'output_price_per_1k': 0.0025, 'provider': 'gemini'}
    ,{'model': 'gemini-flash-lite-latest', 'input_price_per_1k': 0.0001, 'output_price_per_1k': 0.0004, 'provider': 'gemini'}    
]

