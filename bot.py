import os
import time
import requests
import threading
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# PALABRAS CLAVE PARA DETECTAR TRAGEDIAS Y ALERTAS ROJAS
PALABRAS_ALERTA = [
    "tragedia", "alerta", "terremoto", "accidente", "urgente", "fallece", "muere", "muertos",
    "atentado", "explosion", "bomba", "guerra", "tsunami", "sismo", "huracan", "incendio",
    "ultima hora", "breaking", "urgencia", "colision", "derrumbe", "ataque", "desastre", "urgentes"
]

# RED DE MONITOREO INTERNACIONAL (MUNDO, LATAM Y TAILANDIA)
FUENTES_RSS = {
    "BBC Mundo (Internacional)": "https://bbci.co.uk",
    "CNN en Español (Mundial)": "https://cnn.com",
    "Reuters Latam (Global)": "https://reutersagency.com",
    "Infobae (LATAM General)": "https://infobae.com",
    "El Universal (México/Latam)": "https://eluniversal.com.mx",
    "El Tiempo (Colombia/Sudam)": "https://eltiempo.com",
    "Bangkok Post (Tailandia)": "https://bangkokpost.com"
}

class Servidor(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot de Alertas Internacionales Activo")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), Servidor)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

def enviar_a_discord(link, titulo, fuente, imagen_url=None):
    payload = {
        "content": f"**🚨 ÚLTIMA HORA | NOTICIA MUNDIAL 🌍**\n\n📢 **Fuente:** {fuente}\n📌 **Suceso:** {titulo}\n\n✨ Más información y detalles aquí:\n{link}"
    }
    
    if imagen_url:
        payload["embeds"] = [{"image": {"url": imagen_url}}]

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
    except Exception:
        pass

def extraer_imagen(item_texto):
    try:
        url_match = re.search(r'<media:content[^>]*url="([^"]+)"', item_texto)
        if not url_match:
            url_match = re.search(r'<enclosure[^>]*url="([^"]+)"', item_texto)
        if not url_match:
            url_match = re.search(r'<img[^>]*src="([^"]+)"', item_texto)
        if url_match:
            return url_match.group(1).strip()
    except Exception:
        pass
    return None

def es_noticia_urgente(texto_a_revisar):
    texto_minusculas = texto_a_revisar.lower()
    for palabra in PALABRAS_ALERTA:
        if palabra in texto_minusculas:
            return True
    return False

def bucle_monitoreo():
    ultimas_noticias = {}
    print("Iniciando escaneo masivo de noticias globales...")
    
    while True:
        for nombre_fuente, url_rss in FUENTES_RSS.items():
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                response = requests.get(url_rss, headers=headers, timeout=15)
                if response.status_code != 200 or "<item>" not in response.text:
                    continue
                    
                texto = response.text
                primer_item = texto[texto.find("<item>"):texto.find("</item>")+7]
                
                inicio_link = primer_item.find("<link>") + 6
                fin_link = primer_item.find("</link>")
                link_actual = primer_item[inicio_link:fin_link].strip().replace("<![CDATA[", "").replace("]]>", "")
                
                inicio_title = primer_item.find("<title>") + 7
                fin_title = primer_item.find("</title>")
                titulo_actual = primer_item[inicio_title:fin_title].strip().replace("<![CDATA[", "").replace("]]>", "")
                
                foto_actual = extraer_imagen(primer_item)
                
                if not link_actual:
                    continue
                if nombre_fuente not in ultimas_noticias:
                    ultimas_noticias[nombre_fuente] = link_actual
                    continue
                if link_actual != ultimas_noticias[nombre_fuente]:
                    ultimas_noticias[nombre_fuente] = link_actual
                    
                    # Filtro de noticias mundiales de impacto
                    if es_noticia_urgente(titulo_actual):
                        enviar_a_discord(link_actual, titulo_actual, nombre_fuente, foto_actual)
            except Exception:
                pass
        time.sleep(300)  # Revisa noticias urgentes cada 5 minutos debido a la rapidez de las agencias

if __name__ == "__main__":
    bucle_monitoreo()
