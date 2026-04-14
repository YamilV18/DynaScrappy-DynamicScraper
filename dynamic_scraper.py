import os
import time
import subprocess
import threading
from urllib.parse import urljoin
import requests
from playwright.sync_api import sync_playwright
from dynamic_extractor import ResourceExtractor

class DynamicScraper:
    def __init__(self, base_dir='universal_downloads', port=9222):
        self.base_dir = base_dir
        self.port = port
        self.extractor = ResourceExtractor()
        self.current_session_path = ""
        self.browser_process = None  # Para rastrear el proceso de Edge

    def _launch_browser(self):
        """Lanza Edge o Chrome con depuración remota (técnica SENAMHI)."""
        edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
        self.browser_process = subprocess.Popen([
            edge_path,
            f'--remote-debugging-port={self.port}',
            '--user-data-dir=C:\\temp\\scraper_profile',
            '--no-first-run',
            '--no-default-browser-check'
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
        self._launch_browser()
        
        with sync_playwright() as p:
            browser = None
            try:
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
                input(">>> Realiza los ajustes necesarios y presiona ENTER para extraer...")
                
                content = page.content()
                
                if mode == 'files':
                    resources = self.extractor.find_links(content, url, extensions)
                    self._download_manager(resources, url)
                elif mode == 'images':
                    resources = self.extractor.find_images(content, url)
                    self._download_manager(resources, url)
                elif mode == 'text':
                    text = self.extractor.find_text_blocks(content)
                    self._save_text(text, url)

                browser.close()

                input("\n>>> Tarea finalizada. Presiona ENTER para cerrar el navegador y volver al menú...")
            except Exception as e:
                print(f"[!] Error: {e}")
            finally:
                if browser:
                    print("[*] Cerrando navegador...")
                    browser.close()
                self._force_close_browser()

    def _download_manager(self, links, base_url):
        """Gestiona las descargas usando hilos para eficiencia."""
        threads = []
        for link in links:
            full_url = urljoin(base_url, link)
            t = threading.Thread(target=self._download_item, args=(full_url,))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()

    def _download_item(self, url):
        """Descarga usando la ruta de la sesión actual."""
        try:
            # Nombre del archivo basado en la URL
            raw_filename = url.split('/')[-1].split('?')[0] or "index.html"
            filename = os.path.join(self.current_session_path, raw_filename)
            
            response = requests.get(url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                print(f"  [OK] -> {os.path.basename(filename)}")
        except Exception as e:
            print(f"  [!] Error descargando {url}: {e}")

    def _save_text(self, text, url):
        """Guarda el texto en la carpeta 'text' del sitio."""
        filename = os.path.join(self.current_session_path, "contenido_extraido.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"FUENTE: {url}\n{'='*50}\n\n")
            f.write(text)
        print(f"[OK] Texto guardado en: {filename}")