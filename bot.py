import os, time, requests, threading, re
from http.server import BaseHTTPRequestHandler, HTTPServer

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# TUS 9 ENLACES PLANOS CONFIGURADOS EXACTAMENTE COMO LOS MANDASTE
FUENTES_WEB = {
    "CNN en Español": "https://cnnespanol.cnn.com/",
    "El Nacional": "https://www.elnacional.com/",
    "Bangkok Post": "https://www.bangkokpost.com/",
    "El Tiempo": "https://www.eltiempo.com/",
    "BBC Mundo": "https://www.bbc.com/mundo",
    "Telemundo Noticias": "https://www.telemundo.com/noticias",
    "El Universal": "https://www.eluniversal.com.mx/",
    "Milenio": "https://amp.milenio.com/",
    "El Pais Mexico": "https://elpais.com/mexico/"
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

def enviar_a_discord(link, titulo, resumen, fuente):
    payload = {
        "content": f"**🌍 NOTICIA EN DESARROLLO | ÚLTIMA HORA FREEN INFORMA 📢**\n📌 **Fuente:** {fuente}",
        "embeds": [{
            "title": titulo,
            "description": resumen if resumen else "Haz clic en el enlace para leer los detalles completos de este suceso.",
            "url": link,
            "color": 15158332
        }]
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    except:
        pass

def buscar_titulos_y_resumenes(html_puro):
    # Busca bloques de encabezados comunes con sus parrafos adyacentes para armar tarjetas
    enlaces_encontrados = []
    bloques = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>', html_puro)
    
    for link, contenido in bloques:
        if not link.startswith("http"): continue
        texto = re.sub(r'<[^>]+>', ' ', contenido)
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        if len(texto) > 25 and not any(x in texto.lower() for x in ["términos", "privacidad", "cookies", "contacto"]):
            titulo = texto[:80]
            resumen = texto[80:330] if len(texto) > 80 else "Haz clic en el enlace para conocer los detalles del reporte."
            enlaces_encontrados.append((link, titulo, resumen))
            if len(enlaces_encontrados) >= 1: break
            
    return enlaces_encontrados

def bucle_monitoreo():
    ultimas_noticias = {}
    print("Iniciando escaneo inteligente de portales web...")
    
    while True:
        for nombre_fuente, url in FUENTES_WEB.items():
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code != 200: continue
                
                noticias = buscar_titulos_y_resumenes(res.text)
                for link, titulo, resumen in noticias:
                    if nombre_fuente not in ultimas_noticias or link != ultimas_noticias[nombre_fuente]:
                        ultimas_noticias[nombre_fuente] = link
                        enviar_a_discord(link, titulo, resumen, nombre_fuente)
                        time.sleep(2)
            except:
                pass
        time.sleep(300)

if __name__ == "__main__":
    bucle_monitoreo()
