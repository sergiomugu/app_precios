
import sqlite3
import unicodedata

from dbfread import DBF

DBF_PATH = r"D:\consulta_cyglaser\ARBI.DBF"
SQLITE_DB = r"D:\consulta_cyglaser\precios.db"

# --- Función para normalizar texto ---
def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")  # quitar acentos
    texto = texto.replace("-", " ").replace("_", " ")

    # quitar espacios dobles
    while "  " in texto:
        texto = texto.replace("  ", " ")

    return texto.strip()


# Leer la DBF
table = DBF(DBF_PATH, load=True, encoding='latin1')

# Conectar SQLite
conn = sqlite3.connect(SQLITE_DB)
cur = conn.cursor()

# Crear tabla nueva
cur.execute("DROP TABLE IF EXISTS productos;")
cur.execute("""
CREATE TABLE productos (
    codigo TEXT,
    nombre TEXT,
    nombre_norm TEXT,
    precio REAL
);
""")

# Insertar datos
for row in table:
    codigo = row["ART_CODI"]
    nombre = row["ART_NOMB"]
    precio = row["ART_PREC"]

    nombre_norm = normalizar(nombre)

    cur.execute("""
        INSERT INTO productos (codigo, nombre, nombre_norm, precio)
        VALUES (?, ?, ?, ?)
    """, (codigo, nombre, nombre_norm, precio))

conn.commit()
conn.close()

print("✔ Conversión completa → precios.db generado con columna 'nombre_norm'.")
