# DynaScrappy - Dynamic Web Scraper

Un scraper dinámico e intuitivo que permite extraer archivos, imágenes, videos y texto de cualquier sitio web con una interfaz gráfica moderna.

---

## Integrantes del Equipo

- **Apaza Hilasaca Celia Patricia**
- **Condori Quispe Brayan Raul**
- **Machaca Mamani Jhenderson Aaron**
- **Quispe Cuellar Yamil Valente**

---

## Requisitos del Sistema

### Software Requerido

- **Python**: 3.9 o superior
- **Microsoft Edge**: Instalado en tu sistema (usado para navegación)
- **Git**: Para clonar el repositorio
- **Deno**: Runtime JavaScript utilizado por yt-dlp para la extracción actual de contenido de YouTube
- **FFmpeg**: Necesario para combinar vídeo y audio cuando yt-dlp descarga ambos streams por separado

### Dependencias Python

Las dependencias se instalan automáticamente. Las principales son:

- `customtkinter` - Interfaz gráfica moderna
- `playwright` - Automatización de navegador
- `requests` - Descargas HTTP
- `yt-dlp[default]` - Descarga de vídeos y extracción de contenido multimedia
- `yt-dlp-ejs` - Scripts EJS utilizados por yt-dlp para YouTube
- `beautifulsoup4` - Análisis y extracción de contenido HTML
- `tqdm` - Barras de progreso para descargas

---

## Guía de Instalación

### 1️. Clonar el Repositorio

Abre tu terminal y ejecuta:

```bash
git clone https://github.com/YamilV18/DynaScrappy-DynamicScraper.git
cd DynaScrappy-DynamicScraper
```

### 2. Instalar Dependencias

```bash
pip install customtkinter playwright requests beautifulsoup4 "yt-dlp[default]" tqdm
```

### 3. Instalar Deno

Deno es utilizado por `yt-dlp` como runtime JavaScript para resolver los desafíos de YouTube.

#### Windows

Desde PowerShell:

```powershell
irm https://deno.land/install.ps1 | iex
```

Después de la instalación, **cierra y vuelve a abrir PowerShell**.

Comprueba la instalación:

```powershell
deno --version
```

También puedes comprobar dónde está instalado:

```powershell
where.exe deno
```

La instalación oficial de Deno para Windows utiliza por defecto:

```text
%USERPROFILE%\.deno\bin\deno.exe
```



> **Versión mínima recomendada:** Deno 2.3.0 para las versiones actuales de `yt-dlp`.

---

### 4. Instalar FFmpeg

FFmpeg es necesario para que `yt-dlp` pueda combinar los streams de vídeo y audio cuando YouTube los proporciona por separado.

Por ejemplo, `yt-dlp` puede seleccionar:

```text
399 + 251
```

donde un formato corresponde al vídeo y otro al audio. FFmpeg se encarga de combinarlos en el archivo final.

#### Windows

La forma más sencilla es utilizar `winget`:

```powershell
winget install --id Gyan.FFmpeg -e
```

Después de la instalación, abre una nueva terminal y comprueba:

```powershell
ffmpeg -version
```

También puedes comprobar la ubicación:

```powershell
where.exe ffmpeg
```

Los builds de FFmpeg para Windows de Gyan están disponibles mediante gestores de paquetes como `winget`.

---

### 5. Configurar Playwright

Instala los navegadores requeridos por Playwright:

```bash
playwright install
```

El proyecto utiliza Microsoft Edge como navegador principal para la navegación automatizada.

---

## Cómo Usar

### Windows

El proyecto incluye el archivo:

```text
run.bat
```

Este archivo permite ejecutar la aplicación directamente sin tener que escribir manualmente el comando de Python.

Simplemente haz doble clic en:

```text
run.bat
```

El archivo ejecutará:

```bat
python .\main.py
```

También puedes ejecutarlo desde PowerShell:

```powershell
.\run.bat
```

### Ejecución manual en Windows

Si prefieres ejecutar el programa directamente mediante Python:

```powershell
python .\main.py
```

### Linux / macOS

```bash
python3 main.py
```

---

## Descarga de Vídeos

El scraper utiliza `yt-dlp` para gestionar plataformas de vídeo compatibles.

Para sitios que requieren extracción avanzada, `yt-dlp` se encarga de obtener los formatos disponibles.

En YouTube, el flujo actual requiere:

```text
YouTube
   ↓
yt-dlp
   ↓
Deno + EJS
   ↓
Obtención de formatos
   ↓
Vídeo + Audio
   ↓
FFmpeg
   ↓
Archivo final
```

Por este motivo, **Deno y FFmpeg son requisitos necesarios para disponer de la funcionalidad completa de descarga de vídeos**.

---

## Solución de Problemas

### `No supported JavaScript runtime could be found`

Comprueba que Deno esté instalado:

```powershell
deno --version
```

Si el comando no existe, instala Deno y reinicia la terminal.

También puedes comprobar:

```powershell
where.exe deno
```

Deno está habilitado por defecto por `yt-dlp`, por lo que normalmente no es necesario añadir una configuración adicional si `deno.exe` está disponible en el `PATH`.

---

### `Requested format is not available`

Primero comprueba que Deno esté funcionando:

```powershell
deno --version
```

Después actualiza `yt-dlp` y sus dependencias:

```powershell
python -m pip install -U "yt-dlp[default]"
```

---

### `ffmpeg is not installed`

Comprueba:

```powershell
ffmpeg -version
```

Si no se encuentra el comando, instala FFmpeg:

```powershell
winget install --id Gyan.FFmpeg -e
```

Después cierra y vuelve a abrir la terminal.

---

### `yt-dlp-ejs` no está instalado

Actualiza la instalación:

```powershell
python -m pip install -U "yt-dlp[default]"
```

Esto instala el paquete `yt-dlp-ejs` junto con las dependencias predeterminadas de `yt-dlp`.

---

## Actualizar Dependencias

Para actualizar `yt-dlp` y sus componentes:

```powershell
python -m pip install -U "yt-dlp[default]"
```

Para actualizar FFmpeg mediante `winget`:

```powershell
winget upgrade --id Gyan.FFmpeg -e
```

Para actualizar Deno:

```powershell
deno upgrade
```

---

## Estructura Básica del Proyecto

```text
DynaScrappy-DynamicScraper/
│
├── main.py
├── dynamic_scraper.py
├── dynamic_extractor.py
├── run.bat
├── README.md
│
└── universal_downloads/
    └── ...
```

La carpeta `universal_downloads` se utiliza para almacenar los recursos descargados por el scraper.

---

## Ejecución Rápida en Windows

Una vez instalados los requisitos:

```text
1. Clonar el repositorio
        ↓
2. Instalar dependencias Python
        ↓
3. Instalar Deno
        ↓
4. Instalar FFmpeg
        ↓
5. Instalar Playwright
        ↓
6. Ejecutar run.bat
```

Para ejecutar el programa posteriormente, basta con hacer doble clic en:

```text
run.bat
```

o ejecutar:

```powershell
.\run.bat
```

---