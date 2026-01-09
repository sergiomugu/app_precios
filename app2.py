import win32com.client
from flask import Flask, render_template_string, request

app = Flask(__name__)

# Ruta a tu carpeta donde está ARBI.DBF
RUTA_DBF = r"D:\consulta_cyglaser"

# Crear conexión ADO con VFPOLEDB
db = win32com.client.Dispatch("ADODB.Connection")
db.Open(fr"Provider=VFPOLEDB.1;Data Source={RUTA_DBF};")

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Consulta de Precios</title>
    <style>
        body {
            font-family: Arial;
            background: #f2f2f2;
            padding: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 0 10px #aaa;
            max-width: 500px;
            margin: auto;
        }
        input[type=text]{
            width: 100%;
            padding: 12px;
            font-size: 18px;
            margin-bottom: 10px;
        }
        button {
            width: 100%;
            padding: 12px;
            font-size: 18px;
            background: #0078ff;
            color: white;
            border: none;
            border-radius: 8px;
        }
        table {
            width: 100%;
            margin-top: 20px;
            border-collapse: collapse;
        }
        th, td {
            border-bottom: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        th {
            background: #0078ff;
            color: white;
        }
    </style>
</head>
<body>

<div class="card">
    <h2>Consulta de Precios</h2>
    <form method="GET">
        <input type="text" name="q" placeholder="Buscar código o nombre..." required>
        <button type="submit">Buscar</button>
    </form>

    {% if productos %}
    <table>
        <tr>
            <th>Código</th>
            <th>Nombre</th>
            <th>Precio</th>
        </tr>
        {% for p in productos %}
        <tr>
            <td>{{ p.codigo }}</td>
            <td>{{ p.nombre }}</td>
            <td>${{ "%.2f"|format(p.precio) }}</td>
        </tr>
        {% endfor %}
    </table>
    {% endif %}
</div>

</body>
</html>
"""


@app.route("/", methods=["GET"])
def buscar():
    q = request.args.get("q", "").strip()
    productos = []

    if q:
        rs = win32com.client.Dispatch("ADODB.Recordset")

        consulta = f"""
            SELECT ART_CODI, ART_NOMB, ART_PREC
            FROM ARBI
            WHERE ART_NOMB LIKE '%{q}%' 
               OR ART_CODI LIKE '%{q}%'
        """

        rs.Open(consulta, db)

        while not rs.EOF:
            codigo = rs.Fields("ART_CODI").Value
            nombre = rs.Fields("ART_NOMB").Value
            precio = rs.Fields("ART_PREC").Value

            productos.append({
                "codigo": codigo,
                "nombre": nombre,
                "precio": float(precio) if precio is not None else 0
            })

            rs.MoveNext()

        rs.Close()

    return render_template_string(HTML, productos=productos)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090, debug=True)
