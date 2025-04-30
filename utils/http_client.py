import requests
import logging
from typing import Dict, Optional

from config.settings import USER_AGENT, ACCEPT_LANGUAGE

logger = logging.getLogger(__name__)

class HttpClient:
    """Cliente HTTP para realizar peticiones"""
    
    def __init__(self):
        self.session = self._setup_session()
    
    def _setup_session(self):
        """Configura la sesión HTTP con headers adecuados"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept-Language': ACCEPT_LANGUAGE
        })
        return session
    
    def get(self, url: str, params: Dict = None) -> Optional[requests.Response]:
        """Realiza una petición GET con manejo de errores"""
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Error en solicitud a {url}: {str(e)}")
            return None
    
    def close(self):
        """Cierra la sesión HTTP"""
        try:
            self.session.close()
        except Exception as e:
            logger.error(f"Error al cerrar sesión HTTP: {str(e)}")