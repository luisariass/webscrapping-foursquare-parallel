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
WAIT_BETWEEN_ACTIONS = 1.0  # Tiempo entre acciones como clics
RETRY_DELAY_BASE = 2

# Configuración de autenticación
COOKIES_FILE = os.path.join(BASE_DIR, "data", "cookies_foursquare.pkl")
COOKIE_REFRESH_TIME = 2  # segundos para esperar después de cargar cookies
LOGIN_PAGE = "https://es.foursquare.com/login"

# Configuración específica para el scraper de reseñas
MAX_REVIEWS_PER_USER = 20  # Máximo de reseñas a extraer por usuario