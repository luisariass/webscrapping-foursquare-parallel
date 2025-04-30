import requests
from bs4 import BeautifulSoup
import os, json, time, tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from urllib.parse import urljoin
import multiprocessing
from typing import List, Dict, Tuple, Optional

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(processName)s - %(message)s',
    handlers=[
        logging.FileHandler('foursquare_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizedFoursquareScraper:
    def __init__(self, max_workers: int = None, headless: bool = True, max_retries: int = 3):
        self.max_workers = max_workers or multiprocessing.cpu_count() * 2
        self.headless = headless
        self.max_retries = max_retries
        self.driver_pool = self._init_driver_pool()
        self.session = self._setup_session()
        
    def _init_driver_pool(self):
        """Inicializa un pool de drivers Selenium"""
        return [self._setup_driver(i) for i in range(self.max_workers)]
    
    def _setup_driver(self, worker_id: int):
        """Configura un driver Selenium optimizado"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver
    
    def _setup_session(self):
        """Configura la sesión HTTP"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9'
        })
        return session
    
    def _scroll_page(self, driver, max_clicks: int = 10):
        """Hace scroll para cargar más resultados"""
        clicks = 0
        while clicks < max_clicks:
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                
                boton = driver.find_element(By.XPATH, '//button[contains(text(), "Ver más resultados")]')
                driver.execute_script("arguments[0].click();", boton)
                clicks += 1
                logger.info(f"Cargando más resultados (#{clicks})")
                time.sleep(2)
            except NoSuchElementException:
                break
            except Exception as e:
                logger.warning(f"Error al hacer scroll: {str(e)}")
                break
    
    def _get_with_retry(self, driver, url: str, retry: int = 0):
        """Intenta cargar la página con reintentos"""
        try:
            driver.get(url)
            time.sleep(2 + retry)
            return True
        except TimeoutException:
            if retry < self.max_retries:
                logger.warning(f"Timeout, reintentando ({retry + 1}/{self.max_retries})")
                return self._get_with_retry(driver, url, retry + 1)
            logger.error(f"Timeout persistente en {url}")
            return False
        except Exception as e:
            logger.error(f"Error al cargar {url}: {str(e)}")
            return False
    
    def extract_page_html(self, url: str, worker_id: int = 0) -> Optional[str]:
        """Obtiene el HTML completo de la página"""
        driver = self.driver_pool[worker_id % self.max_workers]
        
        try:
            if not self._get_with_retry(driver, url):
                return None
                
            time.sleep(3)
            self._scroll_page(driver)
            return driver.page_source
        except Exception as e:
            logger.error(f"Error en worker {worker_id}: {str(e)}")
            return None
    
    def parse_venue(self, venue, base_url: str, idx: int) -> Optional[Dict]:
        """Extrae los campos específicos de cada sitio"""
        try:
            # Extracción de datos básicos
            score = venue.find('div', class_='venueScore positive')
            name_tag = venue.find('h2')
            category = venue.find('span', class_='venueDataItem')
            address = venue.find('div', class_='venueAddress')
            review = venue.find('p', class_='tipText')
            
            # Procesamiento de campos requeridos
            puntuacion = score.get_text(strip=True) if score else "N/A"
            
            name_link = name_tag.find('a') if name_tag else None
            nombre = name_link.get_text(strip=True) if name_link else (
                name_tag.get_text(strip=True) if name_tag else "N/A")
            
            categoria = category.get_text(strip=True).replace('•', '').strip() if category else "N/A"
            direccion = address.get_text(strip=True) if address else "N/A"
            
            url_tag = name_link if name_link else venue.find('a')
            url_sitio = urljoin(base_url, url_tag['href']) if url_tag and url_tag.has_attr('href') else ""
            
            # Procesamiento de reseña
            usuario = "N/A"
            fecha = "N/A"
            contenido = "N/A"
            
            if review:
                author = review.find('span', class_='tipAuthor')
                if author:
                    user_tag = author.find('a', class_='userName')
                    if user_tag:
                        usuario = user_tag.get_text(strip=True)
                    
                    full_text = author.get_text(separator=' ', strip=True)
                    user_text = user_tag.get_text(strip=True) if user_tag else ""
                    date_text = full_text.replace(user_text, '', 1).strip()
                    fecha = date_text[1:].strip() if date_text.startswith('•') else date_text
                
                full_review = review.get_text(separator=' ', strip=True)
                author_text = author.get_text(separator=' ', strip=True) if author else ""
                contenido = full_review.replace(author_text, '', 1).strip()
            
            return {
                "id": idx + 1,
                "puntuacion": puntuacion,
                "nombre": nombre,
                "categoria": categoria,
                "direccion": direccion,
                "url_sitio": url_sitio,
                "usuario_reseña": usuario,
                "fecha_reseña": fecha,
                "contenido_reseña": contenido,
                "fecha_extraccion": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"Error parsing venue #{idx + 1}: {str(e)}")
            return None
    
    def process_venues(self, html: str, url: str, json_file: str, worker_id: int = 0) -> Optional[Dict]:
        """Procesa todos los sitios de una página"""
        if not html:
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        venues = soup.find_all('div', class_='contentHolder')
        
        if not venues:
            logger.warning(f"No se encontraron sitios en {url}")
            return None
        
        logger.info(f"Procesando {len(venues)} sitios (worker {worker_id})")
        
        # Procesamiento en paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(
                lambda x: self.parse_venue(x[1], url, x[0]),
                enumerate(venues)
            ))
        
        valid_results = [r for r in results if r is not None]
        
        data = {
            "metadata": {
                "fuente": url,
                "total": len(valid_results),
                "fecha": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "sitios": valid_results
        }
        
        # Guardado seguro del JSON
        os.makedirs('data', exist_ok=True)
        temp_file = os.path.join(tempfile.mkdtemp(), 'temp.json')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            final_path = os.path.join('data', json_file)
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_file, final_path)
            
            logger.info(f"Datos guardados en {final_path}")
            return data
        except Exception as e:
            logger.error(f"Error guardando datos: {str(e)}")
            return None
    
    def scrape_urls(self, url_file_pairs: List[Tuple[str, str]]) -> List[Optional[Dict]]:
        """Procesa múltiples URLs en paralelo"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._scrape_single_url,
                    url,
                    file,
                    idx % self.max_workers
                ): (url, file)
                for idx, (url, file) in enumerate(url_file_pairs)
            }
            
            for future in as_completed(futures):
                url, file = futures[future]
                try:
                    results.append(future.result())
                    logger.info(f"Completado: {url}")
                except Exception as e:
                    logger.error(f"Error en {url}: {str(e)}")
                    results.append(None)
        
        return results
    
    def _scrape_single_url(self, url: str, file: str, worker_id: int) -> Optional[Dict]:
        """Procesa una URL individual"""
        for attempt in range(self.max_retries):
            try:
                html = self.extract_page_html(url, worker_id)
                if html:
                    return self.process_venues(html, url, file, worker_id)
                return None
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep((attempt + 1) * 2)
    
    def close(self):
        """Libera recursos"""
        try:
            for driver in self.driver_pool:
                try:
                    driver.quit()
                except Exception:
                    pass
            self.session.close()
        except Exception as e:
            logger.error(f"Error al cerrar: {str(e)}")

# Ejemplo de uso
if __name__ == "__main__":
    targets = [
        ("https://es.foursquare.com/explore?mode=url&near=Cartagena%20de%20Indias%2C%20Bol%C3%ADvar%2C%20Colombia&nearGeoId=72057594041615174", 
         "cartagena_venues.json"),
        ("https://es.foursquare.com/explore?mode=url&near=Santa%20Marta%2C%20Magdalena&nearGeoId=72057594041596541", 
         "santa_marta_venues.json"),
        ("http://es.foursquare.com/explore?mode=url&ne=10.561735%2C-75.370502&q=Santa%20Cruz%20de%20Mompox&sw=10.333159%2C-75.658894", 
         "mompox_venues.json"),
        ("https://es.foursquare.com/explore?mode=url&ne=10.634965%2C-75.06443&q=Turbaco&sw=10.177753%2C-75.641212", "turbaco.json")
    ]
    
    scraper = OptimizedFoursquareScraper(max_workers=4, headless=True)
    
    try:
        start = time.time()
        results = scraper.scrape_urls(targets)
        duration = time.time() - start
        
        success = sum(1 for r in results if r is not None)
        logger.info(f"Scraping completado en {duration:.2f}s - {success}/{len(targets)} exitosos")
    finally:
        scraper.close()