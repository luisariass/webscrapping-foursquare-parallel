import time
import logging
import argparse
from typing import List, Tuple

from config.loggin_config import setup_logging
from core.scraper import FoursquareScraper

logger = logging.getLogger(__name__)

def get_default_targets() -> List[Tuple[str, str]]:
    """Define los targets predeterminados para scraping"""
    return [
        ("https://es.foursquare.com/explore?mode=url&near=Cartagena%20de%20Indias%2C%20Bol%C3%ADvar%2C%20Colombia&nearGeoId=72057594041615174", 
         "cartagena_venues.json"),
        ("https://es.foursquare.com/explore?mode=url&near=Santa%20Marta%2C%20Magdalena&nearGeoId=72057594041596541", 
         "santa_marta_venues.json"),
        ("http://es.foursquare.com/explore?mode=url&ne=10.561735%2C-75.370502&q=Santa%20Cruz%20de%20Mompox&sw=10.333159%2C-75.658894", 
         "mompox_venues.json"),
        ("https://es.foursquare.com/explore?mode=url&ne=10.634965%2C-75.06443&q=Turbaco&sw=10.177753%2C-75.641212", 
         "turbaco.json")
    ]

def parse_args():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Foursquare Venue Scraper')
    parser.add_argument('--workers', type=int, help='Número de workers paralelos')
    parser.add_argument('--visible', action='store_true', help='Modo con navegador visible')
    parser.add_argument('--retries', type=int, default=3, help='Número máximo de reintentos')
    return parser.parse_args()

def main():
    """Punto de entrada principal del programa"""
    # Configurar logging
    setup_logging()
    
    # Parsear argumentos
    args = parse_args()
    
    # Obtener targets
    targets = get_default_targets()
    
    # Crear instancia del scraper
    scraper = FoursquareScraper(
        max_workers=args.workers,
        headless=not args.visible,
        max_retries=args.retries
    )
    
    try:
        # Medir tiempo de ejecución
        start = time.time()
        
        # Ejecutar scraping
        results = scraper.scrape_urls(targets)
        
        # Calcular estadísticas
        duration = time.time() - start
        success = sum(1 for r in results if r is not None)
        
        logger.info(f"Scraping completado en {duration:.2f}s - {success}/{len(targets)} exitosos")
    except KeyboardInterrupt:
        logger.warning("Proceso interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error en el proceso de scraping: {str(e)}")
    finally:
        # Liberar recursos
        scraper.close()

if __name__ == "__main__":
    main()