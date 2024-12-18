from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
import getpass
import logging
from datetime import datetime
import random
import pyautogui

class FacebookCommentClicker:
    def __init__(self, urls, scroll_count=100, click_delay=2):
        self.setup_logging()
        self.urls = urls
        self.max_scroll_count = scroll_count
        self.click_delay = click_delay
        self.user = getpass.getuser()
        self.comment_boxes = set()
        self.comentarios_respuestas = []
        
    def setup_logging(self):
        log_directory = "facebook_logs"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        log_filename = os.path.join(log_directory, f'facebook_comments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        try:
            
            service = Service(ChromeDriverManager().install())
            options = webdriver.ChromeOptions()
            
            # Configuración de datos de usuario para evitar inicios de sesión manuales
            user_data_dir = f"C:\\Users\\{self.user}\\AppData\\Local\\Google\\Chrome\\User Data"
            user_data_dir = f"C:\\Users\\{self.user}\\AppData\\Local\\Google\\Chrome\\User Data"
            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument("--profile-directory=Default")
            options.add_argument("--disable-notifications")
            
            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            self.logger.error(f"Error al configurar el driver: {e}")
            raise
    def click_main_page(self, driver):
        """Realiza un clic en la página principal para activar el scrolling"""
        try:
            # Esperar a que la página esté completamente cargada
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Hacer clic en un área segura de la página principal
            body = driver.find_element(By.TAG_NAME, 'body')
            actions = ActionChains(driver)
            actions.move_to_element_with_offset(body, 100, 100)  # Click en una posición segura
            actions.click()
            actions.perform()
            
            time.sleep(1)  # Pequeña pausa después del clic
            self.logger.info("Clic realizado en la página principal")
            return True
        except Exception as e:
            self.logger.error(f"Error al hacer clic en la página principal: {e}")
            return False

    def is_element_clickable(self, element):
        try:
            return element.is_displayed() and element.is_enabled()
        except:
            return False

    def click_comment_box(self, driver, element, current_scroll_count):
        try:
            actions = ActionChains(driver)
            
            # Scroll suave hasta el elemento
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                element
            )
            time.sleep(1.5)  # Espera para que el scroll termine
            
            # Verificar si el elemento está en el viewport
            viewport_script = """
                var elem = arguments[0];
                var rect = elem.getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.left >= 0 &&
                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                );
            """
            is_in_viewport = driver.execute_script(viewport_script, element)
            
            if not is_in_viewport:
                self.logger.info("Elemento no está en el viewport, ajustando posición...")
                driver.execute_script(
                    "window.scrollBy(0, -100);"  # Ajuste fino de la posición
                )
                time.sleep(1)
            
            # Resaltar el elemento antes del clic
            driver.execute_script("""
                arguments[0].style.border = '3px solid green';
                arguments[0].style.backgroundColor = 'lightgreen';
            """, element)
            
            # Mover el mouse y hacer clic
            actions.move_to_element(element)
            actions.click()
            actions.perform()
            
            time.sleep(random.uniform(1, 2))
            
            # Determinar tipo de comentario y generar respuesta
            tipo_comentario = "Positivo" if current_scroll_count < self.max_scroll_count * 0.5 else "Neutro"
            respuesta = responder_comentario(tipo_comentario)
            comentario = element.get_attribute("aria-label") or "Comentario sin texto"
            
            # Guardar el comentario y la respuesta
            self.comentarios_respuestas.append({
                "Comentario": comentario,
                "Respuesta": respuesta,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Escribir el comentario usando pyautogui
            pyautogui.typewrite(respuesta)
            time.sleep(0.5)
            pyautogui.press('enter')
            
            self.logger.info(f"Comentario realizado: {respuesta}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al hacer clic en el elemento: {e}")
            return False

    def find_and_click_comment_boxes(self, driver, current_scroll_count):
        comment_selectors = [
            "div[contenteditable='true'][role='textbox']",
            "div[aria-label*='coment']",
            "div[aria-label*='comment']",
            "div[aria-label*='Escribe un comentario']",
            "div[aria-label*='Write a comment']"
        ]
        
        for selector in comment_selectors:
            try:
                elements = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                
                for element in elements:
                    element_identifier = f"{element.get_attribute('id')}_{element.get_attribute('class')}_{element.get_attribute('aria-label')}"
                    
                    if element_identifier not in self.comment_boxes:
                        self.comment_boxes.add(element_identifier)
                        
                        if self.click_comment_box(driver, element, current_scroll_count):
                            # Esperar un momento y hacer clic en la sección de respuesta
                            time.sleep(2)
                            self.click_reply_to_comment(driver)
                            return True
                            
            except TimeoutException:
                continue
            except Exception as e:
                self.logger.error(f"Error al buscar selector {selector}: {e}")
                continue
        
        return False

    def click_reply_to_comment(self, driver):
        try:
            # Intentar encontrar el botón de responder al comentario
            reply_button_selectors = [
                "span[aria-label*='Responder']",
                "span[aria-label*='Reply']"
            ]
            for selector in reply_button_selectors:
                try:
                    reply_buttons = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    for button in reply_buttons:
                        if self.is_element_clickable(button):
                            button.click()
                            time.sleep(1)
                            self.logger.info("Clic realizado en el botón de responder al comentario")
                            return
                except TimeoutException:
                    continue
                except Exception as e:
                    self.logger.error(f"Error al intentar hacer clic en el botón de responder con selector {selector}: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"Error al hacer clic en el botón de responder al comentario: {e}")

    def perform_scroll(self, driver):
        try:
            # Realizar scroll suave
            scroll_height = random.randint(300, 500)  # Altura de scroll variable
            driver.execute_script(f"window.scrollBy({{top: {scroll_height}, left: 0, behavior: 'smooth'}});")
            time.sleep(random.uniform(1.5, 2.5))  # Pausa variable
            return True
        except Exception as e:
            self.logger.error(f"Error durante el scroll: {e}")
            return False

    def navigate_to_next_post(self, driver):
        try:
            # Intentar encontrar y hacer clic en el botón "Siguiente publicación" o similar
            next_post_selectors = [
                "a[aria-label='Siguiente']",  # Selector del botón de siguiente publicación (ejemplo)
                "a[aria-label='Next']"
            ]
            for selector in next_post_selectors:
                try:
                    next_post_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    next_post_button.click()
                    time.sleep(3)  # Esperar a que cargue la siguiente publicación
                    self.logger.info("Navegación a la siguiente publicación realizada con éxito")
                    return True
                except TimeoutException:
                    continue
                except Exception as e:
                    self.logger.error(f"Error al intentar navegar a la siguiente publicación con selector {selector}: {e}")
                    continue
            return False
        except Exception as e:
            self.logger.error(f"Error durante la navegación a la siguiente publicación: {e}")
            return False

    def scan_and_click_page(self, driver):
        try:
            current_scroll_count = 0
            
            # Clic inicial en la página principal
            if not self.click_main_page(driver):
                self.logger.error("No se pudo hacer clic inicial en la página principal")
                return
            
            time.sleep(3)  # Espera inicial
            
            while current_scroll_count < self.max_scroll_count:
                # Intentar encontrar y hacer clic en una caja de comentarios
                if self.find_and_click_comment_boxes(driver, current_scroll_count):
                    self.logger.info(f"Comentario realizado en scroll #{current_scroll_count}")
                
                # Realizar scroll
                if not self.perform_scroll(driver):
                    break
                
                current_scroll_count += 1
                
                # Pausa aleatoria entre iteraciones
                time.sleep(random.uniform(1, 2))
                
                # Navegar a la siguiente publicación después de cierto número de scrolls
                if current_scroll_count % 5 == 0:
                    if not self.navigate_to_next_post(driver):
                        self.logger.info("No se pudo navegar a la siguiente publicación, terminando el escaneo")
                        break
            
            self.logger.info(f"Escaneo finalizado después de {current_scroll_count} scrolls")
            
        except Exception as e:
            self.logger.error(f"Error durante el escaneo: {e}")

    def run(self):
        driver = None
        try:
            driver = self.setup_driver()
            
            for url in self.urls:
                self.logger.info(f"Iniciando navegación a {url}")
                driver.get(url)
                
                # Espera inicial para carga de página
                time.sleep(5)
                
                # Realizar el escaneo y comentarios
                self.scan_and_click_page(driver)
                
                # Guardar estadísticas de esta URL
                self.logger.info(f"Comentarios realizados en {url}: {len(self.comentarios_respuestas)}")
                
                # Espera antes de pasar a la siguiente URL
                time.sleep(random.uniform(3, 5))
            
        except Exception as e:
            self.logger.error(f"Error en la ejecución principal: {e}")
        finally:
            if driver:
                driver.quit()
                self.logger.info("Navegador cerrado correctamente")

def responder_comentario(tipo):
    respuestas = {
        "Positivo": ["¡Gracias por tu buen comentario!", "¡Nos alegra que te haya gustado!","que buen comentario"],
        "Negativo": ["Lamentamos que no te haya gustado.", "Gracias por tu crítica, mejoraremos."],
        "Neutro": ["Gracias por tu opinión.", "Valoramos tus comentarios."]
    }
    return random.choice(respuestas.get(tipo, ["Gracias por tu comentario."]))
if __name__ == "__main__":
    urls = [
        "https://web.facebook.com/profeMikhailKrasnov"
    ]
    
    clicker = FacebookCommentClicker(urls=urls, scroll_count=5, click_delay=2)
    clicker.run()
