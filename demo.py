import requests
import json

def fetch_ai_prices():
    # URL do "raw" verzije JSON fajla na GitHubu
    url = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
    
    # Mapiranje tvojih provajdera na LiteLLM nazive
    target_providers = {
        "openai": ["gpt-4", "gpt-3.5", "o1", "o3", "gpt-5"], # gpt-5 kad se pojavi
        "anthropic": ["claude"],
        "gemini": ["gemini"],
        "deepseek": ["deepseek"]
    }

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        filtered_prices = []

        for model_key, details in data.items():
            # Preskačemo meta-podatke (obično polje 'sample_spec')
            if model_key == "sample_spec":
                continue

            # Određujemo provajdera (LiteLLM ga često ima u 'litellm_provider' polju)
            provider = details.get('litellm_provider', '').lower()
            
            # Provjera da li model pripada nekom od tvoja 4 provajdera
            # Napomena: LiteLLM ponekad koristi 'google_inference' ili 'vertex_ai' za Gemini
            is_target = any(p in provider for p in ["openai", "anthropic", "google", "deepseek", "gemini"])

            if is_target:
                # LiteLLM cene su obično izražene po 1 tokenu
                # Množimo sa 1000 da dobijemo cenu po 1K tokena za tvoju tabelu
                input_p = details.get('input_cost_per_token', 0) * 1000
                output_p = details.get('output_cost_per_token', 0) * 1000
                
                # Dodajemo u listu samo ako model ima definisanu cenu
                if input_p > 0 or output_p > 0:
                    filtered_prices.append({
                        "model": model_key,
                        "input_price_per_1k": round(input_p, 8),
                        "output_price_per_1k": round(output_p, 8),
                        "provider": provider
                    })

        return filtered_prices

    except Exception as e:
        print(f"Greška prilikom povlačenja cena: {e}")
        return []

# --- TESTIRANJE ---
prices = fetch_ai_prices()
print(f"Pronađeno {len(prices)} modela.")

# Primer ispisa prvih 5:
for p in prices[:266]:
    print(p)