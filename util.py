import traceback, json
from flask import flash, session, redirect,url_for
import logging

from functools import wraps
import tiktoken,bs4


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'current_user_name' not in session:
            flash("Please login first", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Konfiguracija logovanja
logging.basicConfig(
    filename='app_errors.log',   # ime fajla za logove
    level=logging.ERROR,          # loguje samo ERROR i kritične poruke
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def handle_error(e, db, friendly_message="Something went wrong!"):
    """
    Handles any exception by:
    - rolling back the DB session
    - logging the real error (console or file)
    - flashing a friendly message to the user
    """
    # Rollback session to avoid broken state
    db.session.rollback()

    # Log full traceback (for developers)
    print("=== ERROR ===")
    traceback.print_exc()
    print("=== END ERROR ===")
    logging.error("Exception occurred", exc_info=e)  # exc_info dodaje full traceback

    # Show friendly message to user
    flash(friendly_message, "danger")

def json_to_text(obj, indent=0):
    lines = []
    pad = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            lines.append(f"{pad}{k}:")
            lines.append(json_to_text(v, indent + 1))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            lines.append(f"{pad}- {json_to_text(item, indent + 1)}")
    else:
        lines.append(f"{pad}{obj}")
    return "\n".join(lines)

def json_to_toon(obj, parent="", lines=None):
    if lines is None:
        lines = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{parent}.{k}" if parent else k
            json_to_toon(v, key, lines)

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            json_to_toon(item, f"{parent}[{i}]", lines)

    else:
        lines.append(f"{parent} = {obj}")

    return lines


def json_to_toon2(obj, parent="", lines=None, meta=None):
    if lines is None:
        lines = []
        if meta:
            meta_line = " ".join(f"{k}={v}" for k, v in meta.items())
            lines.append(f"@meta {meta_line}")

    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{parent}.{k}" if parent else k
            json_to_toon(v, key, lines)

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            json_to_toon(item, f"{parent}[{i}]", lines)

    else:
        lines.append(f"{parent} = {obj}")

    return lines
def count_tokens(obj, model: str = "gpt-4o-mini") -> int:
    """
    Računa broj tokena za bilo koji ulaz (string, list, dict).
    """
    import tiktoken
    if not isinstance(obj, str):
        # Pretvori u JSON string ako nije string
        obj = json.dumps(obj, ensure_ascii=False)

    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(obj)
    return len(tokens)


def cleanHtml(pageHtml):
    #return cleanHtml2md(pageHtml)  # samo da probam kako radi sa MD fajlovima
    if isinstance(pageHtml, bytes):
        pageHtml = pageHtml.decode("utf-8", errors="ignore")
    if pageHtml:
        soup = bs4.BeautifulSoup(pageHtml, "html.parser")
    else:
        return ''        
    # 2️⃣ Očisti neželjeno
    # ukloni <script> i <style>
    for tag in soup(["script", "style"]):
        tag.decompose()

    # ukloni sve atribute iz tagova
    for tag in soup.find_all(True):
        tag.attrs = {}

    # ukloni sve komentare
    #for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
    #    comment.extract()
    
    
 
    # 4️⃣ Izvuci čist tekst
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    clean_text = "\n".join(lines)
    print('DEBUG CleanHtml: -----------')
    print('UKUPNO KARAKTERA:',len(clean_text))
    #print(clean_text)
    return clean_text

def last_n_messages(history, n=6):
    if not history:
        return []
    return history[-n:]

    """   
    ovo je napredni deo kad au letu kreiram FAISS chunks za sada mi treba clear HTML

   # 5️⃣ Podeli tekst u chunkove (za FAISS)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,       # reči po chunku
        chunk_overlap=50      # preklapanje
    )
    chunks = splitter.split_text(clean_text)

    # 6️⃣ Napravi embeddinge i FAISS bazu
    embeddings = OpenAIEmbeddings()
    db = FAISS.from_texts(chunks, embeddings)

    # 7️⃣ Sačuvaj FAISS bazu lokalno
    db.save_local("faiss_html_page")

    print("FAISS ready baza kreirana! Broj chunkova:", len(chunks)) """


def clean_to_float(value):
    """Pomoćna funkcija koja pretvara '5.000.000,00 €' u čist float 5000000.0"""
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        return value
    
    # Ako je string, uklanjamo sve osim cifara, zareza i tačke
    # Prvo uklanjamo simbol valute i razmake
    val_str = str(value).replace('€', '').replace(' ', '').strip()
    
    if not val_str:
        return 0

    try:
        # Logika za evropski format (5.000.000,00)
        # Ako imamo i tačku i zarez, tačka je separator hiljada
        if '.' in val_str and ',' in val_str:
            val_str = val_str.replace('.', '').replace(',', '.')
        # Ako imamo samo zarez, on je verovatno decimalni (50,00)
        elif ',' in val_str:
            val_str = val_str.replace(',', '.')
        # Ako imamo samo tačku (npr. 5.000), proveravamo da li je hiljada ili decimala
        elif '.' in val_str:
            parts = val_str.split('.')
            # Ako posle zadnje tačke ima više ili manje od 2 cifre, tretiramo kao hiljade
            if len(parts[-1]) != 2:
                val_str = val_str.replace('.', '')
        
        return float(val_str)
    except ValueError:
        return 0

#print(json_to_toon2(struct1.kanban_data))
#print('tokens_toon1:', count_tokens(json_to_toon2(struct1.kanban_data)))
#print('len',len(json_to_toon(struct1.kanban_data)),' tokens_toon:',count_tokens(json_to_toon(struct1.kanban_data)))
#print('tokens_toon2:',count_tokens(json_to_toon(struct1.kanban_data)))
#print(json_to_text(struct1.kanban_data))
#print('len',len(json_to_text(struct1.kanban_data)),' tokens_text:',count_tokens(json_to_text(struct1.kanban_data)))


#############################
# Funkcija koja pretvara html u markdown tako da moze context da se sredi
#############################
def cleanHtml2md(pageHtml):
    import html2text
    if isinstance(pageHtml, bytes):
        pageHtml = pageHtml.decode("utf-8", errors="ignore")
    
    if not pageHtml:
        return ''
    
    # --- FAZA 1: Priprema i čišćenje DOM-a ---
    soup = bs4.BeautifulSoup(pageHtml, "html.parser")
    
    # Ukloni skripte, stilove i nebitne elemente
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Ukloni sve elemente sa d-none klasom (tvoj zahtev)
    for hidden_tag in soup.find_all(class_="d-none"):
        hidden_tag.decompose()

    # --- FAZA 2: Konverzija u Markdown ---
    h = html2text.HTML2Text()
    
    # Podešavanja za bolji kontekst
    h.ignore_links = False         # Zadrži linkove (često bitni za kontekst)
    h.bypass_tables = False        # Ovo je KLJUČNO - pretvara HTML tabele u Markdown tabele
    h.ignore_images = True         # Slike nam ne trebaju za tekstualni AI
    h.body_width = 0               # Isključuje automatsko prelamanje redova
    h.heading_style = "ATX"        # Koristi # za naslove (standardni Markdown)

    # Pretvaramo očišćeni soup nazad u string pa u Markdown
    markdown_text = h.handle(str(soup))
    
    # --- FAZA 3: Post-processing ---
    # Uklanjamo višestruke prazne redove radi uštede tokena
    lines = [line for line in markdown_text.splitlines() if line.strip()]
    final_md = "\n".join(lines)
    
    print('DEBUG CleanHtml2md: -----------')
    print('UKUPNO KARAKTERA:',len(final_md))
    #print(final_md[:500] + "...") 
    
    return final_md

#metoda koja proverava da li je upit validan da bi se nasao u spisku
def validate_sql(query):
    import re
    q = query.lower().strip()
    
    # 1. Destruktivne komande (Security Gate)
    forbidden_commands = ['drop', 'delete', 'truncate', 'update', 'insert', 'alter', 'create']
    for word in forbidden_commands:
        if re.search(r'\b' + word + r'\b', q):
            return False, f"Komanda '{word.upper()}' nije dozvoljena."

    # 2. Lista dozvoljenih VIEW-ova
    # Ovde nabroj sve view-ove koje si napravio u bazi
    allowed_views = ['v_task', 'v_absence', 'v_taskcomments', 'v_budget']
    
    # Pronalazimo sve tabele/view-ove koje korisnik pominje (posle FROM ili JOIN)
    # Ovaj regex traži reči nakon FROM ili JOIN klauzula
    mentioned_tables = re.findall(r'\b(?:from|join)\s+([a-zA-Z0-9_]+)', q)
    
    if not mentioned_tables:
        return False, "Query must use FROM clause with proper View."

    for table in mentioned_tables:
        if table not in allowed_views:
            return False, f"Access to view '{table}' is not allowed. You can use only: {', '.join(allowed_views)}"

    # 3. Obavezan :team_id VISE NETREBA JER JE UGNJEZDEN
    #if ":team_id" not in q:
    #    return False, "Query must have ':team_id' filter."

    return True, ""

def rewrite_query_for_security(user_sql, allowed_views, team_id):
    import re
    modified_sql = user_sql

    #sredi user_sql
    user_sql = user_sql.strip()                
    if user_sql.endswith(';'):
        user_sql = user_sql[:-1]
    
    for view in allowed_views:
        # Regex koji traži ime view-a, ali pazi na granice reči (\b)
        # tako da ne zameni "v_task_extra" ako tražimo "v_task"
        pattern = r'\b' + re.escape(view) + r'\b'
        
        # Pravimo sigurnosni podupit (subquery)
        replacement = f"(SELECT * FROM {view} WHERE TeamID = {team_id}) as x"
        
        # Menjamo svako pojavljivanje view-a sa filtriranim podupitom
        modified_sql = re.sub(pattern, replacement, modified_sql, flags=re.IGNORECASE)
        
    return modified_sql

def get_allowed_views():
    from sqlalchemy import text
    from database import db
    # Upit koji lista sve tvoje view-ove
    sql = text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME LIKE 'v_%'")    
    try:
        result = db.session.execute(sql)
        # Pravimo listu: ['v_task', 'v_absence', ...]
        return [row[0] for row in result]
    except Exception as e:
        print(f"Greška pri dobavljanju view-ova: {e}")
        return []
    

import pandas as pd
import numpy as np
from scipy.stats import zscore
def audit_dataframe(
    df: pd.DataFrame,
    total_column="Total",
    tolerance=0.01,
    max_examples=20
):

    findings = {
        "rows_total": len(df),
        "total_mismatch": [],
        "outliers": [],
        "pattern_breaks": []
    }

    if total_column not in df.columns:
        raise ValueError(f"Kolona '{total_column}' ne postoji")

    # Samo numeričke kolone
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    if total_column not in numeric_cols:
        raise ValueError(f"Kolona '{total_column}' nije numerička")

    sum_cols = [c for c in numeric_cols if c != total_column]

    # 1️⃣ TOTAL mismatch
    df["_calc_total"] = df[sum_cols].sum(axis=1)
    mismatch_mask = abs(df["_calc_total"] - df[total_column]) > tolerance

    for idx, row in df[mismatch_mask].head(max_examples).iterrows():
        findings["total_mismatch"].append({
            "row_index": int(idx),
            "expected": float(row["_calc_total"]),
            "actual": float(row[total_column])
        })

    # 2️⃣ Outlier detection (Z-score)
    z = zscore(df[total_column].fillna(0))
    df["_z"] = z
    outlier_mask = abs(df["_z"]) > 3

    for idx, row in df[outlier_mask].head(max_examples).iterrows():
        findings["outliers"].append({
            "row_index": int(idx),
            "value": float(row[total_column]),
            "z_score": float(row["_z"])
        })

    # 3️⃣ Pattern break (nagla promena)
    diff = df[total_column].diff().abs()
    threshold = diff.mean() + 5 * diff.std()
    break_mask = diff > threshold

    for idx in df[break_mask].head(max_examples).index:
        findings["pattern_breaks"].append({
            "row_index": int(idx),
            "difference": float(diff.loc[idx])
        })

    findings["summary"] = {
        "total_mismatch_count": int(mismatch_mask.sum()),
        "outliers_count": int(outlier_mask.sum()),
        "pattern_break_count": int(break_mask.sum())
    }

    # cleanup pomoćne kolone
    df.drop(columns=["_calc_total", "_z"], inplace=True, errors="ignore")

    return findings

def audit_xls(
    file_path,
    sheet_name=0,
    total_column="Total",
    tolerance=0.01,
    chunksize=5000
):
    import pandas as pd
    import numpy as np
    from scipy.stats import zscore
    findings = {
        "rows_total": 0,
        "total_mismatch": [],
        "outliers": [],
        "pattern_breaks": []
    }

    for chunk in pd.read_excel(file_path, sheet_name=sheet_name, chunksize=chunksize):
        findings["rows_total"] += len(chunk)

        # Samo numeričke kolone
        numeric_cols = chunk.select_dtypes(include=np.number).columns.tolist()
        if total_column not in numeric_cols:
            raise ValueError(f"Kolona '{total_column}' ne postoji ili nije numerička")

        sum_cols = [c for c in numeric_cols if c != total_column]

        # 1️⃣ TOTAL mismatch
        chunk["calc_total"] = chunk[sum_cols].sum(axis=1)
        mismatch = abs(chunk["calc_total"] - chunk[total_column]) > tolerance

        for idx, row in chunk[mismatch].head(20).iterrows():
            findings["total_mismatch"].append({
                "row_index": int(idx),
                "expected": float(row["calc_total"]),
                "actual": float(row[total_column])
            })

        # 2️⃣ Outlier detection (Z-score)
        chunk["z"] = zscore(chunk[total_column].fillna(0))
        outliers = chunk[abs(chunk["z"]) > 3]

        for idx, row in outliers.head(20).iterrows():
            findings["outliers"].append({
                "row_index": int(idx),
                "value": float(row[total_column]),
                "z_score": float(row["z"])
            })

        # 3️⃣ Pattern break (nagla promena)
        diff = chunk[total_column].diff().abs()
        threshold = diff.mean() + 5 * diff.std()
        breaks = diff > threshold

        for idx in chunk[breaks].head(20).index:
            findings["pattern_breaks"].append({
                "row_index": int(idx),
                "difference": float(diff.loc[idx])
            })

    # Summary
    findings["summary"] = {
        "total_mismatch_count": len(findings["total_mismatch"]),
        "outliers_count": len(findings["outliers"]),
        "pattern_break_count": len(findings["pattern_breaks"])
    }

    return findings

def get_model_config(model_name):
    import config
    """
    Pronalazi i vraća ceo slog (dict) za traženi model iz price_list.
    Vraća None ako model ne postoji.
    """
    # price_list je tvoja lista iz config fajla
    # Ako je u drugoj klasi, koristi self.price_list ili AIConfig.price_list
    price_list = config.price_list
    result = next((item for item in price_list if item['model'] == model_name), None)
    
    """
    model_data = get_model_config('chatgpt-4o-latest')
    if model_data:
        in_p = model_data['input_price_per_1k']
        out_p = model_data['output_price_per_1k']
        provider = model_data['provider']
        print(f"Pronađen {model_data['model']} (Provider: {provider})")
    else:
        print("Model nije pronađen u cenovniku.")
    """

    