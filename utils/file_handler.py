import os
import json
import tempfile
import logging
import time
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class FileHandler:
    """Clase para manejar operaciones de archivos"""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
    
    def save_json(self, data: Dict, filename: str) -> bool:
        """Guarda datos en formato JSON de manera segura"""
        try:
            # Crear directorio temporal para evitar escrituras parciales
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, 'temp.json')
            
            # Escribir a archivo temporal
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # Mover a ubicación final
            final_path = os.path.join(self.base_dir, filename)
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_file, final_path)
            
            logger.info(f"Datos guardados en {final_path}")
            return True
        except Exception as e:
            logger.error(f"Error guardando datos en {filename}: {str(e)}")
            return False
    
    def prepare_venue_data(self, venues: List, url: str) -> Dict:
        """Prepara la estructura de datos para los venues"""
        valid_venues = [v.to_dict() for v in venues if v is not None]
        
        return {
            "metadata": {
                "fuente": url,
                "total": len(valid_venues),
                "fecha": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "sitios": valid_venues
        }