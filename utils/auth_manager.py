import os
import pickle
import logging
import time
from selenium import webdriver
from typing import Optional

from config.settings import USER_AGENT, COOKIES_FILE

logger = logging.getLogger(__name__)

class AuthManager:
    """Maneja la autenticación y cookies para el scraper"""
    
    def __init__(self, cookies_file: str = COOKIES_FILE):
        self.cookies_file = cookies_file
    
    def save_cookies(self, driver: webdriver.Chrome) -> bool:
        """Guarda las cookies del navegador después de iniciar sesión manualmente"""
        try:
            cookies_dir = os.path.dirname(self.cookies_file)
            if cookies_dir and not os.path.exists(cookies_dir):
                os.makedirs(cookies_dir)
                
            pickle.dump(driver.get_cookies(), open(self.cookies_file, "wb"))
            logger.info(f"Cookies guardadas en {self.cookies_file}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar cookies: {str(e)}")
            return False
    
    def load_cookies(self, driver: webdriver.Chrome) -> bool:
        """Carga cookies previamente guardadas"""
        try:
            if not os.path.exists(self.cookies_file):
                logger.error(f"Archivo de cookies no encontrado: {self.cookies_file}")
                return False
                
            cookies = pickle.load(open(self.cookies_file, "rb"))
            for cookie in cookies:
                # Algunos atributos pueden causar errores, los eliminamos
                if 'expiry' in cookie:
                    del cookie['expiry']
                driver.add_cookie(cookie)
            logger.info(f"Cookies cargadas desde {self.cookies_file}")
            return True
        except Exception as e:
            logger.error(f"Error al cargar cookies: {str(e)}")
            return False
    
    def is_session_valid(self, driver: webdriver.Chrome) -> bool:
        """Verifica si la sesión cargada es válida"""
        page_source = driver.page_source.lower()
        current_url = driver.current_url.lower()
        
        is_login_page = "login" in current_url or "iniciar sesión" in page_source
        return not is_login_page
    
    def create_initial_session(self, browser_pool) -> bool:
        """
        Inicia un navegador para que el usuario inicie sesión manualmente
        y guarda las cookies para uso futuro
        """
        try:
            # Usar un navegador visible (no headless)
            original_headless = browser_pool.headless
            browser_pool.headless = False
            
            driver = browser_pool._setup_driver(0)
            
            # Navegar a la página de inicio de sesión
            driver.get("https://es.foursquare.com/login")
            
            # Instrucciones para el usuario
            print("\n==== INICIO DE SESIÓN MANUAL EN FOURSQUARE ====")
            print("1. En el navegador que se ha abierto, inicia sesión en Foursquare")
            print("2. Una vez iniciada la sesión correctamente, presiona Enter aquí")
            input("Presiona Enter cuando hayas iniciado sesión... ")
            
            # Guardar cookies
            success = self.save_cookies(driver)
            
            # Cerrar el navegador
            driver.quit()
            
            # Restaurar configuración original
            browser_pool.headless = original_headless
            
            if success:
                print("Sesión guardada exitosamente. Ahora puedes ejecutar el scraper.")
            else:
                print("Error al guardar la sesión.")
            
            return success
            
        except Exception as e:
            logger.error(f"Error al crear sesión inicial: {str(e)}")
            print(f"Error al crear sesión inicial: {str(e)}")
            return False