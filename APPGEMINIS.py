import sqlite3
import unicodedata

import requests  # Asegúrate de instalarlo
from bs4 import BeautifulSoup  # Asegúrate de instalarlo
from flask import Flask, jsonify, render_template, request
from rapidfuzz import fuzz

app = Flask(__name__)

DB_PATH = "precios.db"


# --- Función para normalizar texto (Tu función original) ---
def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")  # sin acentos
    texto = texto.replace("-", " ").replace("_", " ")
    while "  " in texto:
        texto = texto.replace("  ", " ")
    return texto.strip()

# --- ### INICIO FUNCIÓN DE SCRAPING (AÑADIDA) ### ---

# --- REEMPLAZA ESTA FUNCIÓN EN TU APP.PY ---
# (Asegúrate de tener "from rapidfuzz import fuzz" al principio)
# --- REEMPLAZA ESTA FUNCIÓN EN TU APP.PY ---
# (Asegúrate de tener "from rapidfuzz import fuzz" al principio)

# --- REEMPLAZA ESTA FUNCIÓN EN TU APP.PY ---
# (Asegúrate de tener "from rapidfuzz import fuzz" al principio)

def obtener_precio_web(search_query, target_name):
    """
    VERSIÓN 18: "Enfoque y Umbral"
    1. Solo busca dentro de <div id="primary">.
    2. Sube el umbral de similitud a 75%.
    """
    
    URL_BUSQUEDA = "https://cyglaser.com.ar/"
    nombre_busqueda = search_query.strip().replace("×", "x")
    params = {'s': nombre_busqueda, 'post_type': 'product'}
    
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Referer': 'https://www.google.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(URL_BUSQUEDA, headers=headers, params=params, timeout=10) 
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        target_name_norm = target_name.strip().lower().replace("×", "x")

        # --- MODO 1: ¿Nos redirigió a una página de producto? ---
        main_title_tag = soup.select_one("h2.product_title.entry-title")
        
        if main_title_tag:
            main_title = main_title_tag.get_text(strip=True).lower()
            score = fuzz.token_set_ratio(target_name_norm, main_title)
            
            if score > 80: # Umbral alto para redirección
                price_tag = soup.select_one("p.price")
                if price_tag:
                    return price_tag.get_text(strip=True)
                else:
                    return "Error (Pág. Sencilla, Sin Precio)"
            else:
                return f"No disponible (Redirección, Baja sim: {score}%)"

        # --- MODO 2: Es una página de lista ---
        
        # --- ### CAMBIO CLAVE (V18) - ENFOQUE ### ---
        # Buscamos SÓLO dentro del contenedor de contenido principal
        main_content = soup.select_one("#primary")
        if not main_content:
            # Si no hay #primary, usamos el body, pero es un fallback
            main_content = soup
        
        # Buscamos tarjetas SÓLO DENTRO de main_content
        all_product_cards = main_content.select("li.product")
        # --- ### FIN CAMBIO V18 ### ---
        
        if not all_product_cards:
            return "No disponible (0 resultados)"

        candidatos_web = []
        for card in all_product_cards:
            title_tag = card.select_one("li.title a")
            if not title_tag: 
                continue 
            
            card_title = title_tag.get_text(strip=True).lower()
            if not card_title:
                continue 
                
            score = fuzz.token_set_ratio(target_name_norm, card_title)
            candidatos_web.append({"score": score, "card": card, "title": card_title})

        if not candidatos_web:
            return "No disponible (Sin títulos)"

        candidatos_web.sort(key=lambda x: x["score"], reverse=True)
        best_match = candidatos_web[0]
        
        # --- ### CAMBIO CLAVE (V18) - UMBRAL ### ---
        # Subimos el umbral a 75%
        if best_match["score"] < 80:
        # --- ### FIN CAMBIO V18 ### ---
            best_title = best_match['title']
            return f"No disponible (Baja sim: {best_match['score']}% vs '{best_title}')"

        # ¡ÉXITO!
        best_card = best_match["card"]
        price_tag = best_card.select_one("span.price")
        
        if price_tag:
            return price_tag.get_text(strip=True)
        else:
            return "Error (sin precio)"

    except Exception:
        return "Error (Excepción)"

# --- FIN DE LA FUNCIÓN A REEMPLAZAR ---

@app.get("/")
def home():
    return render_template("index.html")

# --- ### TU RUTA ORIGINAL (INTACTA) ### ---
@app.get("/api")
def api_buscar():
    q = request.args.get("q", "").strip()
    if q == "":
        return jsonify([])

    q_norm = normalizar(q)
    tokens = q_norm.split()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    filtros = " OR ".join([f"nombre_norm LIKE ?" for _ in tokens])
    params = [f"%{t}%" for t in tokens]

    cursor.execute(f"SELECT codigo, nombre, precio, nombre_norm FROM productos WHERE {filtros}", params)
    candidatos = cursor.fetchall()
    conn.close()

    resultados = []
    for row in candidatos:
        nombre_norm = row["nombre_norm"]
        score_fuzzy = fuzz.token_set_ratio(q_norm, nombre_norm)
        matches = sum(1 for t in tokens if t in nombre_norm)
        relevancia = (score_fuzzy * 0.7) + (matches * 10)
        resultados.append({
            "codigo": row["codigo"],
            "nombre": row["nombre"],
            "precio": row["precio"],
            "score": relevancia
        })

    resultados.sort(key=lambda x: x["score"], reverse=True)

    return jsonify([
        {
            "codigo": r["codigo"],
            "nombre": r["nombre"],
            "precio": r["precio"]
        }
        for r in resultados
    ])
# --- ### FIN RUTA ORIGINAL ### ---


# --- ### NUEVA RUTA (LA "OTRA APP") ### ---
@app.get("/api/precio-web")
def api_buscar_web():
    # 'q' es el término de búsqueda del usuario
    q = request.args.get("q", "").strip()
    # 'target_name' es el nombre del producto de la DB
    target_name = request.args.get("target_name", "").strip()

    if q == "" or target_name == "":
        return jsonify({"precio_web": "N/A"})

    # Llamamos a nuestra función de scraping con AMBOS parámetros
    precio = obtener_precio_web(q, target_name)
    
    return jsonify({"precio_web": precio})
# --- ### FIN NUEVA RUTA ### ---


if __name__ == "__main__":
    print("Servidor iniciado en http://localhost:9090")
    app.run(host="0.0.0.0", port=9090, debug=True)