import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import unicodedata

class ResourceExtractor:
    """Clase agnóstica para identificar recursos en el DOM."""
    
    @staticmethod
    def find_links(html_content, base_url, extensions=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set() # Usar set evita duplicados desde el inicio
        ext_pattern = extensions if extensions else ['pdf', 'csv', 'zip', 'xlsx', 'docx']
        
        # Regex mejorada para ignorar parámetros de consulta complejos
        regex = re.compile(rf".*\.({ '|'.join(ext_pattern) })(\?.*)?$", re.IGNORECASE)

        for a in soup.find_all('a', href=True):
            href = urljoin(base_url, a['href']) # Convertir a absoluta de una vez
            if regex.match(href):
                links.add(href)
        return list(links)

    @staticmethod
    def find_images(html_content, base_url):
        """Busca todas las fuentes de imágenes en la página."""
        soup = BeautifulSoup(html_content, 'html.parser')
        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src:
                # Esto convierte rutas relativas en absolutas
                full_path = urljoin(base_url, src.split(' ')[0])
                images.append(full_path)
        return list(set(images))

    @staticmethod
    def find_text_blocks(html_content):
        """Extrae bloques de texto significativos (párrafos, títulos)."""
        soup = BeautifulSoup(html_content, 'html.parser')
        # Eliminar scripts y estilos
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Obtener texto limpio
        lines = (line.strip() for line in soup.get_text().splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)
    
    def normalize_folder_name(name):
        """Limpia el nombre de la página para que sea una carpeta válida."""
        # Quitar tildes y normalizar unicode
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
        # Reemplazar caracteres ilegales (\ / : * ? " < > |) por un guion
        name = re.sub(r'[\\/:*?"<>|]', '-', name)
        # Quitar espacios al inicio/final y puntos extra
        return name.strip().strip('.')
    
    @staticmethod
    def find_videos(html_content, base_url):
        """Busca fuentes de video en etiquetas <video>, <source> y enlaces directos."""
        soup = BeautifulSoup(html_content, 'html.parser')
        videos = []
        
        # 1. Buscar en etiquetas de video de HTML5
        for video_tag in soup.find_all(['video', 'source']):
            src = video_tag.get('src') or video_tag.get('data-src')
            if src:
                videos.append(urljoin(base_url, src))
        
        # 2. Buscar enlaces <a> que apunten a extensiones de video comunes
        video_extensions = ['mp4', 'webm', 'ogg', 'mov', 'avi']
        pattern = re.compile(rf".*\.({ '|'.join(video_extensions) })(\?.*)?$", re.IGNORECASE)
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if pattern.match(href):
                videos.append(urljoin(base_url, href))
                
        return list(set(videos))