import logging
import time
import multiprocessing
from typing import List, Optional, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import (
    DEFAULT_MAX_WORKERS, DEFAULT_HEADLESS, MAX_SCROLL_CLICKS,
    USER_AGENT, PAGE_LOAD_TIMEOUT, WAIT_AFTER_PAGE_LOAD,
    WAIT_BETWEEN_SCROLLS, WAIT_AFTER_BUTTON_CLICK, LOGIN_PAGE, 
    COOKIE_REFRESH_TIME
)

logger = logging.getLogger(__name__)

class BrowserPool:
    """Gestiona un pool de navegadores para paralelismo"""
    
    def __init__(self, max_workers: int = None, headless: bool = True, max_retries: int = 3):
        self.max_workers = max_workers or DEFAULT_MAX_WORKERS
        self.headless = headless
        self.max_retries = max_retries
        # Inicialización perezosa - solo almacenamos los drivers cuando realmente se necesitan
        self.drivers: Dict[int, webdriver.Chrome] = {}
    
    def _setup_driver(self, worker_id: int) -> webdriver.Chrome:
        """Configura un driver Selenium optimizado"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"user-agent={USER_AGENT}")
        # Desactivar banderas de automatización para evitar detección
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        # Eliminar propiedad webdriver para evitar detección
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    def get_driver(self, worker_id: int) -> webdriver.Chrome:
        """Obtiene un driver del pool basado en el worker_id, creándolo si no existe"""
        worker_id = worker_id % self.max_workers  # Asegurar que esté en el rango correcto
        
        # Crear el driver solo si no existe para este worker_id
        if worker_id not in self.drivers:
            logger.info(f"Creando nuevo driver para worker {worker_id}")
            self.drivers[worker_id] = self._setup_driver(worker_id)
            
        return self.drivers[worker_id]
    
    def create_auth_driver(self) -> webdriver.Chrome:
        """Crea un driver específico para autenticación (siempre visible)"""
        # Guardamos el estado actual del modo headless
        original_headless = self.headless
        # Forzamos visibilidad para autenticación
        self.headless = False
        
        # Crear un driver especial para autenticación
        auth_driver = self._setup_driver(0)
        
        # Restauramos el estado original
        self.headless = original_headless
        
        return auth_driver
    
    # Resto de métodos permanecen iguales
    
    def scroll_page(self, driver: webdriver.Chrome, max_clicks: int = MAX_SCROLL_CLICKS) -> None:
        """Hace scroll para cargar más resultados"""
        clicks = 0
        while clicks < max_clicks:
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(WAIT_BETWEEN_SCROLLS)
                
                boton = driver.find_element(By.XPATH, '//button[contains(text(), "Ver más resultados")]')
                driver.execute_script("arguments[0].click();", boton)
                clicks += 1
                logger.info(f"Cargando más resultados (#{clicks})")
                time.sleep(WAIT_AFTER_BUTTON_CLICK)
            except NoSuchElementException:
                logger.debug("No se encontró botón de 'Ver más resultados'")
                break
            except Exception as e:
                logger.warning(f"Error al hacer scroll: {str(e)}")
                break
    
    def get_with_retry(self, driver: webdriver.Chrome, url: str, retry: int = 0) -> bool:
        """Intenta cargar la página con reintentos"""
        try:
            driver.get(url)
            time.sleep(2 + retry)
            return True
        except TimeoutException:
            if retry < self.max_retries:
                logger.warning(f"Timeout, reintentando ({retry + 1}/{self.max_retries})")
                return self.get_with_retry(driver, url, retry + 1)
            logger.error(f"Timeout persistente en {url}")
            return False
        except Exception as e:
            logger.error(f"Error al cargar {url}: {str(e)}")
            return False
    
    def extract_page_html_with_auth(self, url: str, auth_manager, worker_id: int = 0) -> Optional[str]:
        """Obtiene el HTML completo de la página usando autenticación"""
        driver = self.get_driver(worker_id)
        
        try:
            # Primero navegamos a la página de inicio de sesión
            if not self.get_with_retry(driver, LOGIN_PAGE):
                logger.error("No se pudo cargar la página de inicio de sesión")
                return None
                
            # Cargar cookies (autenticación guardada)
            if not auth_manager.load_cookies(driver):
                logger.error("No se pudieron cargar las cookies. Ejecuta create_initial_session primero.")
                return None
            
            # Refrescar para aplicar las cookies
            driver.refresh()
            time.sleep(COOKIE_REFRESH_TIME)
            
            # Navegar a la URL deseada
            if not self.get_with_retry(driver, url):
                logger.error(f"No se pudo cargar la URL: {url}")
                return None
            
            # Comprobar si estamos autenticados correctamente
            if not auth_manager.is_session_valid(driver):
                logger.error("La sesión no es válida o ha expirado. Ejecuta create_initial_session de nuevo.")
                return None
                
            time.sleep(WAIT_AFTER_PAGE_LOAD)
            self.scroll_page(driver)
            return driver.page_source
        except Exception as e:
            logger.error(f"Error en worker {worker_id} al extraer HTML con autenticación: {str(e)}")
            return None
    
    def extract_page_html(self, url: str, worker_id: int = 0) -> Optional[str]:
        """Obtiene el HTML completo de la página sin autenticación"""
        driver = self.get_driver(worker_id)
        
        try:
            if not self.get_with_retry(driver, url):
                return None
                
            time.sleep(WAIT_AFTER_PAGE_LOAD)
            self.scroll_page(driver)
            return driver.page_source
        except Exception as e:
            logger.error(f"Error en worker {worker_id} al extraer HTML: {str(e)}")
            return None
    
    def close(self) -> None:
        """Cierra todos los drivers"""
        logger.info("Cerrando pool de drivers")
        for worker_id, driver in self.drivers.items():
            try:
                driver.quit()
                logger.debug(f"Driver {worker_id} cerrado correctamente")
            except Exception as e:
                logger.warning(f"Error al cerrar driver {worker_id}: {str(e)}")
        self.drivers = {}