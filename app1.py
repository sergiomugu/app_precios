import requests
from dbfread import DBF
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Ruta al archivo DBF local
DBF_PATH = r'd:\consulta_cyglaser\arbi.dbf'

# URL del sitio WordPress (para consultar precios web)
WORDPRESS_API = 'https://cyglaser.com.ar/wp-json/wp/v2/productos'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['GET'])
def buscar():
    query = request.args.get('q', '').strip().upper()
    resultados_local = []
    resultados_web = []

    if not query:
        return render_template('resultados.html', query=query, resultados_local=[], resultados_web=[])

    # ---- BUSQUEDA LOCAL EN DBF ----
    for reg in DBF(DBF_PATH, encoding='latin-1'):
        if query in str(reg.get('ART_CODI', '')).upper() or query in str(reg.get('ART_NOMB', '')).upper():
            resultados_local.append(reg)

    # ---- BUSQUEDA EN WORDPRESS ----
    try:
        resp = requests.get(WORDPRESS_API, params={'search': query}, timeout=5)
        if resp.status_code == 200:
            resultados_web = resp.json()
    except Exception as e:
        print("Error consultando WordPress:", e)

    return render_template('resultados.html',
                           query=query,
                           resultados_local=resultados_local,
                           resultados_web=resultados_web)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=True)
