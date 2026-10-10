import os
import time
import requests
import threading
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# RED DE MONITOREO INTERNACIONAL MASIVO
FUENTES_RSS = {
    "BBC Mundo (Internacional)": "https://bbci.co.uk",
    "CNN en Español (Mundial)": "https://cnn.com",
    "Reuters Latam (Global)": "https://reutersagency.com",
    "Infobae (LATAM General)": "https://infobae.com",
    "El Universal (Mexico)": "https://eluniversal.com.mx",
    "El Tiempo (Colombia)": "https://eltiempo.com"
}

class Servidor(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot de Noticias Generales Activo")

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
        "content": f"**🌍 NOTICIA EN DESARROLLO | ÚLTIMA HORA 📢**\n\n📢 **Fuente:** {fuente}\n📌 **Suceso:** {titulo}\n\n✨ Más información y detalles aquí:\n{link}"
    }
    if imagen_url:
        payload["embeds"] = [{"image": {"url": imagen_url}}]

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        print(f"Envio a Discord - Estatus: {res.status_code}")
    except Exception as e:
        print(f"Error al enviar a Discord: {e}")

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
                
                if link_actual:
                    # Si es la primera vez que ve la fuente o el enlace es diferente, envía de inmediato
                    if nombre_fuente not in ultimas_noticias or link_actual != ultimas_noticias[nombre_fuente]:
                        ultimas_noticias[nombre_fuente] = link_actual
                        enviar_a_discord(link_actual, titulo_actual, nombre_fuente, foto_actual)
                        time.sleep(2) # Pausa de seguridad entre envíos
            except Exception as e:
                print(f"Error en fuente {nombre_fuente}: {e}")
        time.sleep(300) # Revisa cada 5 minutos

if __name__ == "__main__":
    bucle_monitoreo()
