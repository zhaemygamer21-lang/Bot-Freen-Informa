import os, time, requests, threading, re
from http.server import BaseHTTPRequestHandler, HTTPServer

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# ENLACES INTEGRADOS EXACTAMENTE COMO LOS ENVIASTE (SIN CORTAR NI EDITAR)
FUENTES_RSS = {
    "CNN en Español": "https://cnnespanol.cnn.com/",
    "El Nacional": "https://www.elnacional.com/",
    "BBC Mundo": "https://www.bbc.com/mundo",
    "Telemundo Noticias": "https://www.telemundo.com/noticias",
    "Bangkok Post": "https://www.bangkokpost.com/",
    "Infobae America": "https://www.infobae.com/america/",
    "El Tiempo": "https://www.eltiempo.com/",
    "El Pais America": "https://elpais.com/america/"
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
    HTTPServer(("0.0.0.0", port), Servidor).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

def enviar_a_discord(link, titulo, fuente, imagen_url=None):
    payload = {"content": f"**🌍 NOTICIA EN DESARROLLO | ÚLTIMA HORA 📢**\n\n📢 **Fuente:** {fuente}\n📌 **Suceso:** {titulo}\n\n✨ Más información y detalles aquí:\n{link}"}
    if imagen_url: payload["embeds"] = [{"image": {"url": imagen_url}}]
    try: requests.post(WEBHOOK_URL, json=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    except: pass

def extraer_imagen(item_texto):
    for patron in [r'<media:content[^>]*url="([^"]+)"', r'<enclosure[^>]*url="([^"]+)"', r'<img[^>]*src="([^"]+)"']:
        match = re.search(patron, item_texto)
        if match: return match.group(1).strip()
    return None

def bucle_monitoreo():
    ultimas_noticias = {}
    while True:
        for nombre_fuente, url_rss in FUENTES_RSS.items():
            try:
                res = requests.get(url_rss, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=15)
                if res.status_code != 200 or "<item>" not in res.text: continue
                item = res.text[res.text.find("<item>"):res.text.find("</item>")+7]
                link = item[item.find("<link>")+6:item.find("</link>")].strip().replace("<![CDATA[", "").replace("]]>", "")
                title = item[item.find("<title>")+7:item.find("</title>")].strip().replace("<![CDATA[", "").replace("]]>", "")
                foto = extraer_imagen(item)
                if link and (nombre_fuente not in ultimas_noticias or link != ultimas_noticias[nombre_fuente]):
                    ultimas_noticias[nombre_fuente] = link
                    enviar_a_discord(link, title, nombre_fuente, foto)
                    time.sleep(2)
            except: pass
        time.sleep(300)

if __name__ == "__main__":
    bucle_monitoreo()
