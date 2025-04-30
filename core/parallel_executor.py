import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Callable, Any, Dict, Optional

from config.settings import DEFAULT_MAX_WORKERS

logger = logging.getLogger(__name__)

class ParallelExecutor:
    """Maneja la ejecución paralela de tareas"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or DEFAULT_MAX_WORKERS
    
    def execute(self, func: Callable, items: List[Tuple]) -> List[Any]:
        """Ejecuta una función en paralelo para múltiples elementos"""
        results = []
        
        logger.info(f"Iniciando ejecución paralela con {self.max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    func,
                    item[0],  # url
                    item[1],  # file
                    idx % self.max_workers  # worker_id
                ): item
                for idx, item in enumerate(items)
            }
            
            for future in as_completed(futures):
                item = futures[future]
                try:
                    results.append(future.result())
                    logger.info(f"Completado: {item[0]}")
                except Exception as e:
                    logger.error(f"Error en {item[0]}: {str(e)}")
                    results.append(None)
        
        return results
    
    def map_parallel(self, func: Callable, items: List) -> List[Any]:
        """Aplica una función a una lista de elementos en paralelo"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            return list(executor.map(func, items))