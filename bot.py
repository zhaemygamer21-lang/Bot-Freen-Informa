import os, time, requests, threading, re
from http.server import BaseHTTPRequestHandler, HTTPServer

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# TUS 9 RUTAS COPIADAS EXACTAMENTE LETRA POR LETRA COMO LAS MANDASTE
PAGINAS_WEB = [
    "https://cnnespanol.cnn.com/",
    "https://www.elnacional.com/",
    "https://www.bangkokpost.com/",
    "https://www.eltiempo.com/",
    "https://www.bbc.com/mundo",
    "https://www.telemundo.com/noticias",
    "https://www.eluniversal.com.mx/",
    "https://amp.milenio.com/",
    "https://elpais.com/mexico/"
]

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

def enviar_a_discord(texto_alerta, url_origen):
    payload = {
        "content": f"**🌍 NOTICIA EN DESARROLLO | ÚLTIMA HORA FREEN INFORMA 📢**\n\n📌 **Actualización detectada en:** {url_origen}\n📝 **Contenido nuevo:** {texto_alerta}"
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    except:
        pass

def limpiar_html(html_puro):
    # Remueve scripts, estilos y etiquetas para extraer el texto plano de la pagina
    texto = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html_puro)
    texto = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', texto)
    texto = re.sub(r'<[^>]+>', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def bucle_monitoreo():
    estados_anteriores = {}
    print("Iniciando rastreador directo de paginas web...")
    
    while True:
        for url in PAGINAS_WEB:
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code != 200: continue
                
                texto_limpio = limpiar_html(res.text)
                # Tomamos un fragmento del texto de la portada para monitorear variaciones
                resumen_actual = texto_limpio[:400]
                
                if url not in estados_anteriores:
                    estados_anteriores[url] = resumen_actual
                    # Envio inicial forzado para que veas actividad de inmediato al guardar
                    enviar_a_discord(resumen_actual[:150] + "...", url)
                    continue
                
                if resumen_actual != estados_anteriores[url]:
                    estados_anteriores[url] = resumen_actual
                    enviar_a_discord(resumen_actual[:150] + "...", url)
                    time.sleep(2)
            except:
                pass
        time.sleep(300) # Revisa las 9 webs cada 5 minutos

if __name__ == "__main__":
    bucle_monitoreo()
