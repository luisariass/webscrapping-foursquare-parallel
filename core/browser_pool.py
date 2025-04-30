import logging
import time
import multiprocessing
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import (
    DEFAULT_MAX_WORKERS, DEFAULT_HEADLESS, MAX_SCROLL_CLICKS,
    USER_AGENT, PAGE_LOAD_TIMEOUT, WAIT_AFTER_PAGE_LOAD,
    WAIT_BETWEEN_SCROLLS, WAIT_AFTER_BUTTON_CLICK
)

logger = logging.getLogger(__name__)

class BrowserPool:
    """Gestiona un pool de navegadores para paralelismo"""
    
    def __init__(self, max_workers: int = None, headless: bool = True, max_retries: int = 3):
        self.max_workers = max_workers or DEFAULT_MAX_WORKERS
        self.headless = headless
        self.max_retries = max_retries
        self.drivers = self._init_driver_pool()
    
    def _init_driver_pool(self) -> List[webdriver.Chrome]:
        """Inicializa un pool de drivers Selenium"""
        logger.info(f"Inicializando pool con {self.max_workers} drivers")
        return [self._setup_driver(i) for i in range(self.max_workers)]
    
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
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        return driver
    
    def get_driver(self, worker_id: int) -> webdriver.Chrome:
        """Obtiene un driver del pool basado en el worker_id"""
        return self.drivers[worker_id % self.max_workers]
    
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
    
    def extract_page_html(self, url: str, worker_id: int = 0) -> Optional[str]:
        """Obtiene el HTML completo de la página"""
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
        for driver in self.drivers:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Error al cerrar driver: {str(e)}")