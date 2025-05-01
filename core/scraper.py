import logging
import time
from typing import List, Dict, Tuple, Optional

from core.browser_pool import BrowserPool
from core.parallel_executor import ParallelExecutor
from utils.html_parser import HtmlParser
from utils.file_handler import FileHandler
from utils.http_client import HttpClient
from utils.auth_manager import AuthManager
from exceptions.scraper_exceptions import ScraperException

logger = logging.getLogger(__name__)

class FoursquareScraper:
    """Clase principal del scraper con funcionalidad modular"""
    
    def __init__(self, max_workers=None, headless=True, max_retries=3, use_auth=False):
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.use_auth = use_auth
        
        # Inicializar componentes
        self.browser_pool = BrowserPool(max_workers, headless, max_retries)
        self.parallel_executor = ParallelExecutor(max_workers)
        self.parser = HtmlParser()
        self.file_handler = FileHandler()
        self.http_client = HttpClient()
        self.auth_manager = AuthManager()
    
    def create_initial_session(self) -> bool:
        """
        Inicia un navegador para que el usuario inicie sesión manualmente
        y guarda las cookies para uso futuro
        """
        return self.auth_manager.create_initial_session(self.browser_pool)
    
    def scrape_urls(self, url_file_pairs: List[Tuple[str, str]]) -> List[Optional[Dict]]:
        """Método público principal para iniciar el scraping"""
        return self.parallel_executor.execute(
            self._scrape_single_url,
            url_file_pairs
        )
    
    def _scrape_single_url(self, url: str, file_name: str, worker_id: int) -> Optional[Dict]:
        """Procesa una URL individual"""
        logger.info(f"Iniciando scrape de {url} (worker {worker_id})")
        
        for attempt in range(self.max_retries):
            try:
                # Obtener HTML (con autenticación si está activada)
                html = None
                if self.use_auth:
                    html = self.browser_pool.extract_page_html_with_auth(url, self.auth_manager, worker_id)
                else:
                    html = self.browser_pool.extract_page_html(url, worker_id)
                    
                if not html:
                    logger.warning(f"No se pudo obtener HTML de {url}")
                    return None
                
                # Encontrar venues
                venues = self.parser.find_venues(html)
                if not venues:
                    logger.warning(f"No se encontraron sitios en {url}")
                    return None
                
                logger.info(f"Procesando {len(venues)} sitios de {url}")
                
                # Parsear venues en paralelo
                parsed_venues = []
                for idx, venue in enumerate(venues):
                    parsed = self.parser.parse_venue(venue, url, idx)
                    if parsed:
                        parsed_venues.append(parsed)
                
                # Preparar y guardar datos
                data = self.file_handler.prepare_venue_data(parsed_venues, url)
                if self.file_handler.save_json(data, file_name):
                    return data
                return None
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Error persistente en {url}: {str(e)}")
                    raise ScraperException(f"Error al procesar {url}: {str(e)}")
                
                logger.warning(f"Reintento {attempt+1}/{self.max_retries} para {url}")
                time.sleep((attempt + 1) * 2)
    
    def close(self):
        """Cierra los recursos"""
        logger.info("Cerrando recursos del scraper")
        self.browser_pool.close()
        self.http_client.close()