import os, time, requests, threading, re
from http.server import BaseHTTPRequestHandler, HTTPServer

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# TUS 9 ENLACES PLANOS COPIADOS EXACTAMENTE LETRA POR LETRA COMO LOS MANDASTE
Ruta_1 = "https://cnnespanol.cnn.com/"
Ruta_2 = "https://www.elnacional.com/"
Ruta_3 = "https://www.bangkokpost.com/"
Ruta_4 = "https://www.eltiempo.com/"
Ruta_5 = "https://www.bbc.com/mundo"
Ruta_6 = "https://www.telemundo.com/noticias"
Ruta_7 = "https://www.eluniversal.com.mx/"
Ruta_8 = "https://amp.milenio.com/"
Ruta_9 = "https://elpais.com/mexico/"

FUENTES_WEB = {
    "CNN en Español": Ruta_1,
    "El Nacional": Ruta_2,
    "Bangkok Post": Ruta_3,
    "El Tiempo": Ruta_4,
    "BBC Mundo": Ruta_5,
    "Telemundo Noticias": Ruta_6,
    "El Universal": Ruta_7,
    "Milenio": Ruta_8,
    "El Pais Mexico": Ruta_9
}

class Servidor(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Freen informa Activo")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), Servidor).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

def enviar_a_discord(link, titulo, resumen, fuente, imagen_url=None):
    payload = {
        "content": f"**🌍 NOTICIA EN DESARROLLO | ÚLTIMA HORA FREEN INFORMA 📢**\n📌 **Fuente:** {fuente}",
        "embeds": [{
            "title": titulo if titulo else "Nueva actualizacion de ultima hora",
            "description": resumen if resumen else "Haz clic en el enlace para leer los detalles completos de este suceso.",
            "url": link,
            "color": 15158332
        }]
    }
    if imagen_url and imagen_url.startswith("http"):
        payload["embeds"][0]["image"] = {"url": imagen_url}
    try:
        requests.post(WEBHOOK_URL, json=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    except:
        pass

def analizar_pagina(html_puro, url_base):
    # Busca el primer bloque de enlace con texto e imagen para armar la tarjeta visual completa
    try:
        # Extraccion de imagen
        img_match = re.search(r'<img[^>]+src="([^"]+)"', html_puro)
        foto = img_match.group(1).strip() if img_match else None
        if foto and foto.startswith("//"): foto = "https:" + foto
        
        # Extraccion de texto y links
        bloques = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>', html_puro)
        for link, contenido in bloques:
            if not link.startswith("http") and link.startswith("/"):
                link = url_base.rstrip('/') + link
            if not link.startswith("http"): continue
            
            texto = re.sub(r'<[^>]+>', ' ', contenido)
            texto = re.sub(r'\s+', ' ', texto).strip()
            
            if len(texto) > 40 and not any(x in texto.lower() for x in ["términos", "privacidad", "cookies", "contacto", "anuncie"]):
                titulo = texto[:90]
                resumen = texto[90:340] if len(texto) > 90 else "Haz clic en el enlace para conocer la cobertura completa de este suceso mundial."
                return [(link, titulo, resumen, foto)]
    except:
        pass
    return []

def bucle_monitoreo():
    ultimas_noticias = {}
    print("Iniciando escaneo masivo con tarjetas y fotos...")
    while True:
        for nombre_fuente, url in FUENTES_WEB.items():
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code != 200: continue
                
                noticias = analizar_pagina(res.text, url)
                for link, titulo, resumen, foto in noticias:
                    if nombre_fuente not in ultimas_noticias or link != ultimas_noticias[nombre_fuente]:
                        ultimas_noticias[nombre_fuente] = link
                        enviar_a_discord(link, titulo, resumen, nombre_fuente, foto)
                        time.sleep(2)
            except:
                pass
        time.sleep(300)

if __name__ == "__main__":
    bucle_monitoreo()
