from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
import getpass
import logging
from datetime import datetime
import random

class FacebookCommentClicker:
    def __init__(self, urls, scroll_count=100, click_delay=2, max_comments=8):
        self.setup_logging()
        self.urls = urls
        self.max_scroll_count = scroll_count
        self.click_delay = click_delay
        self.max_comments = max_comments  # Número máximo de comentarios
        self.user = getpass.getuser()
        self.comentarios_respuestas = []
        self.processed_elements = set()  # Conjunto para elementos procesados

    def setup_logging(self):
        log_directory = "facebook_logs"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        log_filename = os.path.join(
            log_directory, 
            f'facebook_comments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
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
            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument("--profile-directory=Default")
            options.add_argument("--disable-notifications")

            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            self.logger.error(f"Error al configurar el driver: {e}")
            raise

    def click_comment_box(self, driver, element):
        try:
            # Verificar si el elemento ya fue procesado
            if element in self.processed_elements:
                return False

            # Marcar el elemento como procesado
            self.processed_elements.add(element)

            # Realizar acciones de clic y comentario
            actions = ActionChains(driver)
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                element
            )
            time.sleep(1)

            # Hacer clic y agregar estilo visual
            actions.move_to_element(element)
            actions.click()
            actions.perform()
            time.sleep(1)

            tipo_comentario = "Positivo"  # Puedes personalizar este comportamiento
            respuesta = responder_comentario(tipo_comentario)

            element.send_keys(respuesta)
            time.sleep(0.5)
            element.send_keys(Keys.RETURN)

            self.comentarios_respuestas.append({
                "Respuesta": respuesta,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self.logger.info(f"Comentario realizado: {respuesta}")
            return True
        except Exception as e:
            self.logger.error(f"Error al comentar: {e}")
            return False

    def scan_and_click_page(self, driver):
        try:
            current_scroll_count = 0
            comments_made = 0

            while current_scroll_count < self.max_scroll_count and comments_made < self.max_comments:
                # Buscar cuadros de comentarios
                elements = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true'][role='textbox']")
                for element in elements:
                    if comments_made >= self.max_comments:
                        break

                    # Intentar hacer clic en el cuadro de comentario
                    if self.click_comment_box(driver, element):
                        comments_made += 1

                # Realizar scroll para cargar más publicaciones
                if comments_made < self.max_comments:
                    self.perform_scroll(driver)
                current_scroll_count += 1

            self.logger.info(f"Se realizaron {comments_made} comentarios.")
        except Exception as e:
            self.logger.error(f"Error durante el escaneo: {e}")

    def perform_scroll(self, driver):
        try:
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
        except Exception as e:
            self.logger.error(f"Error durante el scroll: {e}")

    def run(self):
        driver = None
        try:
            driver = self.setup_driver()
            for url in self.urls:
                self.logger.info(f"Iniciando navegación a {url}")
                driver.get(url)
                time.sleep(5)
                self.scan_and_click_page(driver)
        except Exception as e:
            self.logger.error(f"Error en la ejecución principal: {e}")
        finally:
            if driver:
                driver.quit()
                self.logger.info("Navegador cerrado correctamente")


def responder_comentario(tipo):
    respuestas = {
    "Positivo": [
        "¡Gracias por tu buen comentario!",
        "¡Nos alegra que te haya gustado!",
        "Es genial saber que estamos cumpliendo tus expectativas.",
        "¡Apreciamos mucho tu entusiasmo!",
        "Gracias por tu apoyo, nos motiva a seguir trabajando con dedicación.",
        "Es un placer recibir comentarios tan positivos como el tuyo.",
        "¡Nos encanta que lo hayas disfrutado!",
        "Tu reconocimiento nos inspira a seguir mejorando.",
        "¡Gracias por destacar nuestro esfuerzo!",
        "Nos llena de satisfacción saber que estás contento con nuestra labor."
    ],
    "Negativo": [
        "Lamentamos que no te haya gustado.",
        "Gracias por tu crítica, trabajaremos para mejorar.",
        "Tomaremos en cuenta tus observaciones para seguir creciendo.",
        "Sentimos no haberte dado una mejor experiencia.",
        "Agradecemos que nos compartas tus comentarios para aprender y mejorar.",
        "Lamentamos que no hayamos cumplido tus expectativas, trabajaremos en ello.",
        "Tu opinión es importante para nosotros, haremos ajustes necesarios.",
        "Gracias por señalar esto, lo revisaremos a fondo.",
        "Lamentamos que esta vez no hayamos estado a la altura.",
        "Estamos comprometidos a mejorar y agradecemos tu honestidad."
    ],
    "Neutro": [
        "Gracias por tu opinión.",
        "Valoramos tus comentarios.",
        "Agradecemos que compartas tu punto de vista.",
        "Tomaremos nota de lo que nos dices.",
        "Tu opinión nos ayuda a reflexionar y avanzar.",
        "Gracias por darnos tu perspectiva.",
        "Es importante para nosotros conocer lo que piensas.",
        "Tus comentarios nos permiten evaluar lo que estamos haciendo.",
        "Gracias por tomarte el tiempo de compartir tu experiencia.",
        "Valoramos todas las opiniones, gracias por la tuya."
    ]
        }
    return random.choice(respuestas.get(tipo, ["Gracias por tu comentario."]))

if __name__ == "__main__":
    # Lista de URLs de páginas de Facebook
    urls = [
        "https://www.facebook.com/profeMikhailKrasnov",
        "https://www.facebook.com/AlcaldiaTunja"
    ]
    # Inicialización del script con las URLs y configuraciones
    clicker = FacebookCommentClicker(urls=urls, scroll_count=10, click_delay=2, max_comments=8)
    clicker.run()

