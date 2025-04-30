import os
import multiprocessing

# Configuraciones generales
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Configuración del scraper
DEFAULT_MAX_WORKERS = multiprocessing.cpu_count() * 2
DEFAULT_HEADLESS = True
DEFAULT_MAX_RETRIES = 3
MAX_SCROLL_CLICKS = 10
PAGE_LOAD_TIMEOUT = 30

# Configuración de User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
ACCEPT_LANGUAGE = "es-ES,es;q=0.9"

# Configuración de tiempos de espera (segundos)
WAIT_AFTER_PAGE_LOAD = 3
WAIT_BETWEEN_SCROLLS = 1.5
WAIT_AFTER_BUTTON_CLICK = 2
RETRY_DELAY_BASE = 2