from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin

from models.venue import Venue

logger = logging.getLogger(__name__)

class HtmlParser:
    """Clase para parsear el HTML de Foursquare"""
    
    def find_venues(self, html: str) -> List:
        """Encuentra todos los elementos de venue en el HTML"""
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find_all('div', class_='contentHolder')
    
    def parse_venue(self, venue, base_url: str, idx: int) -> Optional[Venue]:
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
            
            return Venue(
                id=idx + 1,
                puntuacion=puntuacion,
                nombre=nombre,
                categoria=categoria,
                direccion=direccion,
                url_sitio=url_sitio,
                usuario_reseña=usuario,
                fecha_reseña=fecha,
                contenido_reseña=contenido
            )
        except Exception as e:
            logger.error(f"Error parsing venue #{idx + 1}: {str(e)}")
            return None