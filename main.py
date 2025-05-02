import time
import logging
import argparse
from typing import List, Tuple

from config.loggin_config import setup_logging
from core.scraper import FoursquareScraper
from core.user_review_scraper import UserReviewScraper

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
         "turbaco.json"),
        ("https://es.foursquare.com/explore?mode=url&near=Cove%C3%B1as%2C%20Sucre%2C%20Colombia&nearGeoId=72057594041613648",
         "covenas_venues.json")
    ]

def get_sample_venue_reviews_targets() -> List[Tuple[str, str]]:
    """Define ejemplos de sitios para extraer reseñas de usuarios"""
    return [
        # He tomado URLs de los venues en tus archivos JSON como ejemplos
        ("https://es.foursquare.com/v/alqu%C3%ADmico/56ecf121498e3aa68341604b", 
         "reviews_alquimico.json"),
        ("https://es.foursquare.com/v/quero-arepa/553bdbd9498eb10d09931bbf",
         "reviews_quero_arepa.json"),
        ("https://es.foursquare.com/v/la-cocina-de-pepina/4ed91cf09adfe5cbdd99de2d",
         "reviews_cocina_pepina.json")
    ]

def parse_args():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Foursquare Scraper')
    parser.add_argument('--workers', type=int, help='Número de workers paralelos')
    parser.add_argument('--visible', action='store_true', help='Modo con navegador visible')
    parser.add_argument('--retries', type=int, default=3, help='Número máximo de reintentos')
    parser.add_argument('--auth', action='store_true', help='Usar autenticación con cookies')
    parser.add_argument('--setup-auth', action='store_true', help='Configurar autenticación inicial')
    parser.add_argument('--review-mode', action='store_true', help='Modo de extracción de reseñas de usuarios')
    parser.add_argument('--venue-url', type=str, help='URL específica de un venue para extraer reseñas')
    return parser.parse_args()

def main():
    """Punto de entrada principal del programa"""
    # Configurar logging
    setup_logging()
    
    # Parsear argumentos
    args = parse_args()
    
    if args.review_mode:
        # Modo de extracción de reseñas
        scraper = UserReviewScraper(
            max_workers=args.workers or 1,  # Por defecto un solo worker para este modo
            headless=not args.visible,
            max_retries=args.retries,
            use_auth=True  # Siempre usamos autenticación para este modo
        )
        
        # Si necesitamos configurar autenticación
        if args.setup_auth:
            success = scraper.auth_manager.create_initial_session(scraper.browser_pool)
            if success:
                logger.info("Configuración de autenticación completada con éxito")
            else:
                logger.error("Error en la configuración de autenticación")
            return
        
        # Determinar los targets
        if args.venue_url:
            # Si especificamos una URL de venue
            targets = [(args.venue_url, f"reviews_{args.venue_url.split('/')[-1]}.json")]
        else:
            # Usar lista predeterminada de venues para extraer reseñas
            targets = get_sample_venue_reviews_targets()
    else:
        # Modo normal de extracción de venues
        scraper = FoursquareScraper(
            max_workers=args.workers,
            headless=not args.visible,
            max_retries=args.retries,
            use_auth=args.auth
        )
        
        # Si solo queremos configurar la autenticación
        if args.setup_auth:
            success = scraper.create_initial_session()
            if success:
                logger.info("Configuración de autenticación completada con éxito")
            else:
                logger.error("Error en la configuración de autenticación")
            return
        
        # Obtener targets
        targets = get_default_targets()
    
    try:
        # Medir tiempo de ejecución
        start = time.time()
        
        # Ejecutar scraping según el modo
        if args.review_mode:
            results = scraper.scrape_venue_users_and_reviews(targets)
        else:
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
    # Ejemplos de comandos:
    # 1. Configurar autenticación:
    #    python main.py --setup-auth --visible
    
    # 2. Scraping normal de venues:
    #    python main.py --auth
    
    # 3. Scraping de reseñas y usuarios:
    #    python main.py --review-mode --auth
    
    # 4. Scraping de un venue específico:
    #    python main.py --review-mode --venue-url https://es.foursquare.com/v/alquimico/56ecf121498e3aa68341604b
    
    main()