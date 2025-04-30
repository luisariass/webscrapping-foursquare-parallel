import logging
import os

def setup_logging(log_file="foursquare_scraper.log", level=logging.INFO):
    """Configura el sistema de logging para el scraper"""
    
    log_format = '%(asctime)s - %(levelname)s - %(processName)s - %(message)s'
    
    # Asegurarse de que el directorio de logs existe
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar los handlers
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
    
    # Aplicar la configuración
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )
    
    return logging.getLogger(__name__)