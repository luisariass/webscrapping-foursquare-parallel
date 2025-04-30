import time
from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class Venue:
    """Modelo de datos para un venue de Foursquare"""
    id: int
    nombre: str
    categoria: str = "N/A"
    direccion: str = "N/A"
    puntuacion: str = "N/A"
    url_sitio: str = ""
    usuario_reseña: str = "N/A"
    fecha_reseña: str = "N/A"
    contenido_reseña: str = "N/A"
    fecha_extraccion: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    
    def to_dict(self) -> Dict:
        """Convierte el venue a un diccionario para serialización"""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "direccion": self.direccion,
            "puntuacion": self.puntuacion,
            "url_sitio": self.url_sitio,
            "usuario_reseña": self.usuario_reseña,
            "fecha_reseña": self.fecha_reseña,
            "contenido_reseña": self.contenido_reseña,
            "fecha_extraccion": self.fecha_extraccion
        }