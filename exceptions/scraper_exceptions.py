class ScraperException(Exception):
    """Excepción base para errores del scraper"""
    pass

class ExtractorException(ScraperException):
    """Error durante la extracción de datos"""
    pass

class ParserException(ScraperException):
    """Error durante el parseo de HTML"""
    pass

class SaveException(ScraperException):
    """Error al guardar datos"""
    pass

class BrowserException(ScraperException):
    """Error relacionado con el navegador"""
    pass