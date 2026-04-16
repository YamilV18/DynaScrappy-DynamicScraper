import os
import time
import subprocess
import threading
import socket
import random
from tqdm import tqdm
from urllib.parse import urljoin
import requests
from playwright.sync_api import sync_playwright
from dynamic_extractor import ResourceExtractor
from concurrent.futures import ThreadPoolExecutor
import yt_dlp

class DynamicScraper:
    def __init__(self, base_dir='universal_downloads', port=9222, cancel_callback=None):
        self.base_dir = base_dir
        self.port = port
        self.extractor = ResourceExtractor()
        self.current_session_path = ""
        self.browser_process = None
        self.playwright = None
        self.browser_context = None
        self.session = requests.Session()
        self.cancel_callback = cancel_callback  # Función que retorna True si se solicitó cancelación
        # Lista de User-Agents para rotar
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36...'
        ]

    def _is_port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    def iniciar_navegador(self):
        if self._is_port_in_use(self.port):
            print(f"[!] El puerto {self.port} ya está en uso. Intentando conectar...")
        else:
            """Lanza el navegador una sola vez al inicio."""
            if self.browser_process is None:
                print("[*] Iniciando instancia persistente del navegador...")
                edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
                self.browser_process = subprocess.Popen([
                    edge_path,
                    f'--remote-debugging-port={self.port}',
                    '--user-data-dir=C:\\temp\\scraper_profile',
                    '--no-first-run'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)

    def _force_close_browser(self):
        """Mata el proceso del navegador y sus hijos."""
        if self.browser_process:
            print("[*] Terminando proceso del navegador...")
            try:
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.browser_process.pid)], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"[!] No se pudo cerrar el proceso: {e}")
            self.browser_process = None

    def run(self, url, mode='files', extensions=None):
        with sync_playwright() as p:
            try:
                # Conexión al navegador que ya está abierto
                browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{self.port}")
                context = browser.contexts[0]
                page = context.new_page()
                
                print(f"[*] Navegando a: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # ... (resto de tu lógica de títulos y carpetas) ...
                page_title = page.title() or "Sitio Sin Titulo"
                clean_name = ResourceExtractor.normalize_folder_name(page_title)
                site_path = os.path.join(self.base_dir, clean_name)
                self.current_session_path = os.path.join(site_path, mode)
                
                if not os.path.exists(self.current_session_path):
                    os.makedirs(self.current_session_path)
                
                print(f"[*] Carpeta de destino: {self.current_session_path}")
                # ------------------------------------

                if mode == 'images':
                    print("[*] Cargando imágenes (scroll)...")
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)

                print(f"\n[!] Navegador abierto en: {page_title}")
                
                content = page.content()
                resources = []
                
                if mode == 'files':
                    resources = self.extractor.find_links(content, url, extensions)
                    self._download_manager(resources, url)
                elif mode == 'images':
                    resources = self.extractor.find_images(content, url)
                    self._download_manager(resources, url)
                elif mode == 'videos':
                    # 1. Obtener la URL REAL que tiene el navegador en este segundo
                    # (Importante para YouTube Shorts y TikTok donde la URL cambia al hacer scroll)
                    
                    # Verificar si el usuario canceló antes de invocar yt-dlp
                    if self.cancel_callback and self.cancel_callback():
                        return
                    
                    current_url = page.url

                    if "tiktok.com/explore" in current_url or "youtube.com/shorts" in current_url:
                        # Intentamos obtener la URL del video que tiene el foco/reproducción
                        # En TikTok, el video activo suele actualizar la URL si haces clic en él
                        print(f"[*] Estás en una sección de exploración. Procesando el video activo...")
                        
                    self._universal_video_download(current_url) 
                    
                    # 2. Buscar videos estáticos en el DOM
                    video_links = self.extractor.find_videos(content, current_url)
                    
                    # 3. Sumar los interceptados (m3u8, mpd, etc.)
                    if hasattr(self, 'captured_videos') and self.captured_videos:
                        video_links.extend(list(self.captured_videos))
                    
                    video_links = list(set(video_links))

                    # 4. Lógica de decisión
                    if any(x in current_url for x in ['youtube.com', 'tiktok.com', 'twitch.tv']):
                        print(f"[*] Plataforma detectada. Procesando video actual: {current_url}")
                        self._universal_video_download(current_url)
                    
                    elif video_links:
                        with ThreadPoolExecutor(max_workers=2) as executor:
                            for v_link in video_links:
                                # CORRECCIÓN: Si es un blob, yt-dlp no puede leerlo. 
                                # Usamos la URL base de la página en su lugar.
                                if v_link.startswith('blob:'):
                                    print(f"[*] Blob detectado. Intentando extraer desde la URL de origen: {url}")
                                    executor.submit(self._universal_video_download, url)
                                elif any(x in v_link for x in ['youtube.com', 'youtu.be', 'tiktok.com']):
                                    executor.submit(self._universal_video_download, v_link)
                                else:
                                    executor.submit(self._download_video_segmented, v_link)
                elif mode == 'text':
                    text = self.extractor.find_text_blocks(content)
                    self._save_text(text, url)

                if resources:
                    print(f"[*] Se encontraron {len(resources)} recursos. Iniciando descarga...")
                    self._download_manager(resources, url)
                else:
                    if mode != 'text': print("[!] No se encontró contenido relevante para descargar.")
                page.close() # Solo cerramos la pestaña, no el navegador
                
            except Exception as e:
                print(f"[!] Error durante la extracción: {e}")

    def descargar_via_click(self, page, selector_boton):
        """
        Espera a que un clic dispare una descarga y la gestiona.
        """
        try:
            with page.expect_download(timeout=60000) as download_info:
                page.click(selector_boton)
            
            download = download_info.value
            # Guardar en tu carpeta configurada
            path = os.path.join(self.current_session_path, download.suggested_filename)
            download.save_as(path)
            print(f"[OK] Archivo JS guardado: {download.suggested_filename}")
            
        except Exception as e:
            print(f"[!] No se detectó descarga tras el clic: {e}")

    def _download_manager(self, links, base_url):
        """Gestiona las descargas usando un pool limitado de hilos."""
        # Limitamos a un máximo de 5 hilos para no saturar al servidor
        with ThreadPoolExecutor(max_workers=5) as executor:
            for link in links:
                # Verificar cancelación antes de enviar cada descarga
                if self.cancel_callback and self.cancel_callback():
                    print("[!] Descarga cancelada por el usuario.")
                    executor.shutdown(wait=False)
                    return
                full_url = urljoin(base_url, link)
                executor.submit(self._download_item, full_url)

    def _download_item_with_pbar(self, url, pbar):
        self._download_item(url)
        pbar.update(1)

    def _download_item(self, url):
        # Verificar cancelación antes de descargar
        if self.cancel_callback and self.cancel_callback():
            return
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': random.choice(self.user_agents)})
        """Descarga robusta con reintentos para conexiones móviles."""
        intentos_max = 3
        timeout_segundos = 30 # Aumentado para conexiones lentas
        
        # Nombre del archivo
        raw_filename = url.split('/')[-1].split('?')[0] or "archivo_desconocido"
        filename = os.path.join(self.current_session_path, raw_filename)

        with self.session.get(url, stream=True, timeout=timeout_segundos) as response:
            time.sleep(random.uniform(1, 3))

            for intento in range(intentos_max):
                # Verificar cancelación en cada intento
                if self.cancel_callback and self.cancel_callback():
                    if os.path.exists(filename):
                        os.remove(filename)
                    return
                
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                    
                    with requests.get(url, stream=True, timeout=timeout_segundos, headers=headers) as response:
                        response.raise_for_status()
                        
                        # Verificar si el servidor indica el tamaño del archivo
                        total_size = int(response.headers.get('content-length', 0))
                        
                        with open(filename, 'wb') as f:
                            downloaded_size = 0
                            for chunk in response.iter_content(chunk_size=8192):
                                # Verificar cancelación durante la descarga por chunks
                                if self.cancel_callback and self.cancel_callback():
                                    if os.path.exists(filename):
                                        os.remove(filename)
                                    return
                                
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                        
                        # VALIDACIÓN: ¿Se descargó completo?
                        if total_size != 0 and downloaded_size < total_size:
                            raise Exception(f"Descarga incompleta: {downloaded_size}/{total_size} bytes")
                    
                    print(f"  [OK] -> {os.path.basename(filename)}")
                    break

                except requests.exceptions.ConnectionError:
                    print(f"  [!] Bloqueo de conexión en: {url}. El servidor rechazó la petición.")
                    break # Sale de los reintentos para este archivo específico
                except Exception as e:
                    print(f"  [!] Intento {intento + 1} fallido para {url}: {e}")
                    if os.path.exists(filename):
                        os.remove(filename) # Borrar archivo corrupto para reintentar
                    
                    if intento < intentos_max - 1:
                        time.sleep(2) # Esperar un poco antes de reintentar
                    else:
                        print(f"  [ERROR FINAL] No se pudo descargar: {url}")

    def _download_video_segmented(self, url, num_chunks=4):
        """Descarga un video dividiéndolo en partes para mayor velocidad."""
        filename = os.path.join(self.current_session_path, os.path.basename(url).split('?')[0])
        
        # 1. Obtener el tamaño total del video
        head = self.session.head(url, allow_redirects=True)
        total_size = int(head.headers.get('content-length', 0))
        
        if total_size < 5000000: # Si es menor a 5MB, descarga normal
            return self._download_item(url)

        chunk_size = total_size // num_chunks
        threads = []
        
        print(f"[*] Descargando video en {num_chunks} segmentos: {os.path.basename(filename)}")

        start_time = time.time()

        def download_range(start, end, part_num):
            headers = {'Range': f'bytes={start}-{end}', 'User-Agent': random.choice(self.user_agents)}
            with self.session.get(url, headers=headers, stream=True) as r:
                with open(f"{filename}.part{part_num}", 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

        # 2. Lanzar hilos para cada segmento
        for i in range(num_chunks):
            start = i * chunk_size
            end = (i + 1) * chunk_size - 1 if i < num_chunks - 1 else total_size - 1
            t = threading.Thread(target=download_range, args=(start, end, i))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        # 3. Unir las partes
        with open(filename, 'wb') as final_file:
            for i in range(num_chunks):
                part_name = f"{filename}.part{i}"
                with open(part_name, 'rb') as pf:
                    final_file.write(pf.read())
                os.remove(part_name)
        print(f"  [OK] Video ensamblado: {os.path.basename(filename)}")
        end_time = time.time()
        print(f"[*] Tiempo total de descarga: {end_time - start_time:.2f} segundos.")

    def _save_text(self, text, url):
        """Guarda el texto en la carpeta 'text' del sitio."""
        filename = os.path.join(self.current_session_path, "contenido_extraido.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"FUENTE: {url}\n{'='*50}\n\n")
            f.write(text)
        print(f"[OK] Texto guardado en: {filename}")
    def cerrar_todo(self):
        """Cierre final del proceso del navegador."""
        if self.browser_process:
            print("\n[*] Cerrando navegador y limpiando procesos...")
            try:
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.browser_process.pid)], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
            self.browser_process = None
    def _scroll_to_bottom(self, page):
        """Hace scroll progresivo para activar lazy loading."""
        last_height = page.evaluate("document.body.scrollHeight")
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)  # Espera carga de red
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def catch_js_downloads(self, url):
        """
        Navega a la página y escucha eventos de red para capturar 
        descargas iniciadas por JavaScript.
        """
        self.current_session_path = self._prepare_folder(url)
        found_files = []

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://localhost:{self.port}")
            context = browser.contexts[0]
            page = context.new_page()

            # Listener: Se activa cada vez que la página recibe un recurso
            def handle_response(response):
                # Verificamos si el content-type es de un archivo o la URL tiene extensiones
                content_type = response.headers.get("content-type", "").lower()
                if "application/zip" in content_type or "application/octet-stream" in content_type:
                    print(f"[!] Recurso de descarga detectado: {response.url}")
                    found_files.append(response.url)

            page.on("response", handle_response)
            
            page.goto(url, wait_until="networkidle")
            
            # En el caso de CoolROM, el usuario tendría que hacer clic 
            # o tú podrías automatizar el clic en el botón de "Download Now"
            print("[*] Tienes 30 segundos para interactuar o esperar el inicio de la descarga...")
            time.sleep(30) 

            # Al finalizar, mandamos los links capturados al gestor de descargas
            if found_files:
                self._download_manager(list(set(found_files)), url)

    def verificar_tipo_real(self, url):
        """Verifica el Content-Type sin descargar el archivo completo."""
        try:
            response = self.session.head(url, allow_redirects=True, timeout=5)
            return response.headers.get('Content-Type')
        except:
            return None

    def _setup_interceptor(self, page):
        def handle_response(response):
            u = response.url
            # Buscamos el 'manifiesto' que contiene el video real
            if ".m3u8" in u or ".mpd" in u or "googlevideo.com/videoplayback" in u:
                if u not in self.captured_videos:
                    print(f"[!] Fuente real detectada: {u[:50]}...")
                    self.captured_videos.add(u)

        page.on("response", handle_response)

    def _universal_video_download(self, url):
        """Usa yt-dlp para manejar sitios complejos como YouTube."""
        ydl_opts = {
            'format': 'best', 
            'outtmpl': os.path.join(self.current_session_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                except Exception as e:
                    print(f"[!] Error en motor universal: {e}")
        except Exception as e:
            # Si falla (porque no es un sitio soportado), intentamos tu método segmentado
            print(f"[!] Motor universal falló, intentando descarga directa...")
            self._download_video_segmented(url)