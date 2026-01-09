import time

import requests
from bs4 import BeautifulSoup


# --- Pega tu función V6 aquí ---
def obtener_precio_web(nombre_producto):
    """
    VERSIÓN 6.1 - MODO "NARRADOR"
    """
    print(f"\n--- Iniciando búsqueda web para: '{nombre_producto}' ---")
    
    URL_BUSQUEDA = "https://cyglaser.com.ar/"
    params = {'s': nombre_producto, 'post_type': 'product'}
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
        
        # 1. Normalizamos el nombre que buscamos
        nombre_producto_norm = nombre_producto.strip().lower()
        print(f"Buscando coincidencia exacta para: [{nombre_producto_norm}]")

        # 2. Encontramos todos los "cards" de productos
        all_product_cards = soup.select("li.product")
        
        if not all_product_cards:
            print("-> DIAGNÓSTICO: No se encontraron 'li.product' (tarjetas de producto) en la página.")
            print("   (Probablemente la búsqueda devolvió '0 resultados')")
            
            # ... (Lógica de página única, por si acaso) ...
            precio_tag = soup.select_one("p.price ins .woocommerce-Price-amount.amount")
            if not precio_tag:
                tags_reg = soup.select("p.price .woocommerce-Price-amount.amount")
                if tags_reg: precio_tag = tags_reg[-1]
            
            if precio_tag:
                print("-> DIAGNÓSTICO: Se encontró un precio de 'página única'.")
                return precio_tag.get_text(strip=True)
            
            return "No disponible (Razón: 0 tarjetas)"

        print(f"-> Se encontraron {len(all_product_cards)} tarjetas de producto. Recorriendo...")

        # 3. Si SÍ hay una lista, la recorremos
        for i, card in enumerate(all_product_cards):
            
            title_tag = card.select_one("h2.woocommerce-loop-product__title")
            if not title_tag:
                print(f"  - Tarjeta {i+1}: Sin título. Saltando.")
                continue

            card_title = title_tag.get_text(strip=True).lower()
            print(f"  - Tarjeta {i+1}: Leyendo título: [{card_title}]")

            # 5. Comparamos
            if card_title == nombre_producto_norm:
                print(f"  -> ¡COINCIDENCIA ENCONTRADA! Extrayendo precio de esta tarjeta.")
                
                precio_tag = card.select_one("span.price ins .woocommerce-Price-amount.amount")
                if not precio_tag:
                    tags_reg = card.select("span.price .woocommerce-Price-amount.amount")
                    if tags_reg: precio_tag = tags_reg[-1]
                
                if precio_tag:
                    precio_texto = precio_tag.get_text(strip=True)
                    print(f"  -> PRECIO ENCONTRADO: {precio_texto}")
                    return precio_texto
                else:
                    print(f"  -> ERROR: Coincidencia de título, pero no se encontró precio en la tarjeta.")
                    return "Error (sin precio)"
            
            # (Si no coincide, el bucle sigue)

        # 6. Si terminamos el bucle...
        print("-> DIAGNÓSTICO: Se recorrieron todas las tarjetas. No hubo coincidencia exacta de título.")
        return "No disponible (Razón: Sin coincidencia)"

    except Exception as e:
        print(f"-> ERROR CRÍTICO: {e}")
        return f"Error ({type(e).__name__})"

# --- Prueba de Fuego ---
print("--- Iniciando PRUEBA DE NARRADOR ---")
start_time = time.time()

# ¡IMPORTANTE! 
# Reemplaza esto con el nombre EXACTO de un producto que
# sabes que está en tu DB y también en la web.
nombre_producto_test = "Bandeja 30×40 cm lisa"

precio_web = obtener_precio_web(nombre_producto_test)

print(f"\n--- FIN DE LA PRUEBA ---")
print(f"Nombre Buscado: {nombre_producto_test}")
print(f"Resultado Final: {precio_web}")
print(f"Tiempo: {time.time() - start_time:.2f} segundos")