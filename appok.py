import sqlite3
import unicodedata

from flask import Flask, jsonify, render_template, request
from rapidfuzz import fuzz

app = Flask(__name__)

DB_PATH = "precios.db"   # asegurate que el archivo existe en la misma carpeta


# --- Función para normalizar texto ---
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

@app.get("/")
def home():
    return render_template("index.html")
@app.get("/api")
def api_buscar():
    q = request.args.get("q", "").strip()
    if q == "":
        return jsonify([])

    q_norm = normalizar(q)
    tokens = q_norm.split()  # MULTI-PALABRAS

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Prefiltro rápido con LIKE
    filtros = " OR ".join([f"nombre_norm LIKE ?" for _ in tokens])
    params = [f"%{t}%" for t in tokens]

    cursor.execute(f"SELECT codigo, nombre, precio, nombre_norm FROM productos WHERE {filtros}", params)
    candidatos = cursor.fetchall()
    conn.close()

    # Calcular similitud
    resultados = []
    for row in candidatos:
        nombre = row["nombre"]
        nombre_norm = row["nombre_norm"]

        score_fuzzy = fuzz.token_set_ratio(q_norm, nombre_norm)
        matches = sum(1 for t in tokens if t in nombre_norm)

        relevancia = (score_fuzzy * 0.7) + (matches * 10)

        resultados.append({
            "codigo": row["codigo"],
            "nombre": nombre,
            "precio": row["precio"],
            "score": relevancia
        })

    resultados.sort(key=lambda x: x["score"], reverse=True)

    # devolver sin score
    return jsonify([
        {
            "codigo": r["codigo"],
            "nombre": r["nombre"],
            "precio": r["precio"]
        }
        for r in resultados
    ])



if __name__ == "__main__":
    print("Servidor iniciado en http://localhost:9090")
    app.run(host="0.0.0.0", port=9090, debug=True)
