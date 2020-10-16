import queue
import sys, os
import requests
import argparse
import pandas as pd
from core import core
from time import sleep
from selenium import webdriver
from bs4 import BeautifulSoup
from core.utils import message_api
from googleSheets import Googlesheet
from selenium.webdriver.common.by import By
from facebook import scrapper_facebook
from facebook import Facebook
from selenium.webdriver.support.ui import WebDriverWait
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.support import expected_conditions as EC
from core.utils import get_user_agent_list, get_random_user_agent

class Tripadvisor(object):
    def __init__(self, city, opcion, precio="media", fecha="29/07/2020", mode="ver"):
        precios = {"alta":"Restaurantes elegantes", "media": "Gama media", "baja":"Restaurantes económicos"}
        self.city = city
        self.fecha = fecha
        self.precio = precios[precio]
        self.opcion = opcion.upper()
        self.session = requests.Session()
        self.REQUEST_HEADER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36"}
        self.user_agents_list = get_user_agent_list()
        self.url = "https://www.tripadvisor.com.ar/Search?q={}".format(city)
        self.base_url = "https://www.tripadvisor.co"
        self.time_wait = 10
        self.driver = self.get_driver(mode)
        self.wait = WebDriverWait(self.driver, 20)        
        self.driver.maximize_window()

    def get_driver(self, mode):
        #mode = "VER"
        options = webdriver.ChromeOptions()
        install_folder = os.path.abspath(os.path.split(__file__)[0])
        if sys.platform == 'win32':
            exec_path = "%s\\drivers\\chromedriver.exe"%install_folder
            options.add_argument("--log-level=3")
        else:
            exec_path = "%s/drivers/chromedriver"%install_folder

        if mode.upper() == "OCULTO":
            #options.add_argument("--disable-logging")
            options.add_argument("window-size=1400,700")
            options.add_argument('headless')
        
        return webdriver.Chrome(executable_path=exec_path, chrome_options=options)
               
    def create_urls(self):
        self.driver.get(self.url)
        sleep(self.time_wait)
        #Buscar ubicaciones .search-filter
        xpath_ubication = '//*[@id="search-filters"]/ul/li[7]/a'
        try:
            element = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_ubication))).click()
        except Exception as e:
            element = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_ubication))).click()

        sleep(self.time_wait)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        try:
            firts_result = soup.select(".prw_rup.prw_search_search_results.ajax-content")[0]
            search = firts_result.select(".result-content-columns")[0].attrs
            url_search = search["onclick"].split("'")[3].split("-")
            url_restaurants = "{}/Restaurants-{}-{}.html".format(self.base_url, url_search[1], url_search[2])
            url_tours = "{}/Attractions-{}-Activities-{}.html".format(self.base_url, url_search[1], url_search[2])
            return url_restaurants, url_tours
        except Exception as e:
            raise Exception("Ocurrio el error %s"%e)

    def pagination(self):
        pag = self.driver.find_elements_by_css_selector(".pageNum")
        if len(pag) == 0:
            return 1
        return int(pag[-1].text)
    
    def encuestaClose(self):
        encuesta = self.driver.find_elements_by_css_selector("._26xCMGoF.toYy1402")
        if len(encuesta) > 0:
            print("Cerrando encuesta")
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "._3VKU_-kL"))).click()
        else:
            print("Encuesta no presente")

    def next(self):
        sleep(self.time_wait)
        while True:
            try:
                next_page = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav.next"))).click()
            except Exception as e:
                print("Error next click", e)
                sleep(2)
            else:
                break
        #next_page = self.driver.find_elements_by_css_selector(".nav.next")
        #next_page[0].click()
        sleep(self.time_wait)
        return

    def parsing_data_restaurant(self, url, name, session):
        fb = Facebook([], self.city)
        restaurant_info = {}
        restaurant_info["name"] = name
        header = get_random_user_agent(self.user_agents_list)
        try:
            # response = requests.get(url, headers={"User-Agent": header})
            response = session.get(url, headers={"User-Agent": header},timeout=5)
        except requests.exceptions.RequestException as e:
            print("Ocurrio un error")
            try:
                header = get_random_user_agent(self.user_agents_list)
                response = session.get(url, headers={"User-Agent": header},timeout=5)
            except:
                return restaurant_info

        soup = BeautifulSoup(response.text, "lxml")
        restaurant_info["name"] = core.get_restaurant_name(soup)
        restaurant_info["telephone"] = core.get_restaurant_tel(soup)
        restaurant_info["email"] = core.get_restaurant_mail(soup)
        restaurant_info["website"] = core.get_restaurant_website(soup)
        
        if restaurant_info["email"] == "":
            if "facebook" in restaurant_info["website"]:
                restaurant_info["email"] = scrapper_facebook(restaurant_info["website"])
            else:
                data = fb.scraping_facebook_tripadvisor(restaurant_info["name"])
                restaurant_info["email"] = data.get("email", "")
        del fb
        return restaurant_info

    def parsing_data_tours(self, url, name,session):
        fb = Facebook([], self.city)
        tour_info = {}
        tour_info["name"] = name
        header = get_random_user_agent(self.user_agents_list)
        try:
            #response = requests.get(url, headers={"User-Agent": header})
            response = session.get(url, headers={"User-Agent": header},timeout=5)
        except requests.exceptions.RequestException as e:
            print("Ocurrio un error")
            try:
                header = get_random_user_agent(self.user_agents_list)
                response = session.get(url, headers={"User-Agent": header},timeout=5)
            except:
                print("Ocurrio un segundo error")
                return tour_info
        
        soup = BeautifulSoup(response.text, "lxml")
        tour_info["name"] = core.get_tour_name(soup)
        tour_info["telephone"] = core.get_tour_tel(soup)
        tour_info["email"] = core.get_tour_mail(soup)
        tour_info["website"] = core.get_tour_website(soup)
        if tour_info["email"] == "":
            if "facebook" in tour_info["website"]:
                tour_info["email"] = scrapper_facebook(tour_info["website"])
            else:
                data = fb.scraping_facebook_tripadvisor(tour_info["name"])
                tour_info["email"] = data.get("email", "")
        del fb
        return tour_info

    def handler_Multithreading(self, list_url, parsing_function, session):
        results = []
        threads = []
        with ThreadPoolExecutor(max_workers=25) as executor:
            for url in list_url:
                name = url["name"]
                url = self.base_url + url["href"]
                threads.append(executor.submit(parsing_function, url, name, session))

        for task in as_completed(threads):
            results.append(task.result())

        print("Finalizando")
        return results

    def generator_urls(self, last_page, selector_type, selector):
        cont = 1
        stop = None
        while not stop:
            list_urls = []
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            list_items = soup.select(selector_type)
            for item in list_items:
                href = item.find_all(href=True)[0]["href"]
                name = selector(item)
                #list_urls.append({"name":name})
                list_urls.append({"name": name, "href":href})

            print("Pagina %i de %i:"%(cont, last_page))
            yield list_urls

            if cont == last_page:
                stop = True
            cont+=1
            if cont <= last_page:
                self.next()

    def search_restaurants(self, url):
        gs = Googlesheet()
        self.driver.get(url)
        sleep(self.time_wait)
        #Selector para buscar la categoria del restautante, Gama Media etc
        items = self.driver.find_elements_by_css_selector("._1TxySsqs")
        print("Selecinando restaurante %s"%self.precio)
        for item in items:
            if item.text == self.precio:
                item.click()
                break
        sleep(self.time_wait)
        last_page = self.pagination()
        self.encuestaClose()

        gs.get_all_values("Restaurantes")
        restaurants = self.generator_urls(last_page, "._1llCuDZj", core.get_restaurant_name_list)
        for restaurant in restaurants:
            gs.find_restaurants(restaurant)
            if gs.cont_restaurants == 70:
                break
        self.driver.quit()  
        print("Ejecutando hilos") 
        res = self.handler_Multithreading(gs.restaurants_to_insert, self.parsing_data_restaurant, self.session)      
        print("Guardando datos en Google sheets")
        msg = gs.save_restaurants(res, self.fecha, self.city)
        del gs
        return msg

    def search_tours(self, url):
        gs = Googlesheet()
        self.driver.get(url)
        sleep(self.time_wait)
        # Selector para buscar la opcion de Tour
        items = self.driver.find_elements_by_css_selector("._18Y-JSUs")
        for item in items:
            if item.text == "Tours":
                item.click()
                break
        sleep(self.time_wait)
        # Selector para buscar por empresa
        operadores = self.driver.find_elements_by_css_selector("._3s_k1zxI")
        operadores[0].click()
        sleep(self.time_wait)
        last_page = self.pagination()
        self.encuestaClose()

        gs.get_all_values("Tours")
        tours = self.generator_urls(last_page, "._2X44Y8hm", core.get_tour_name_list)
        for tour in tours:
            gs.find_tours(tour)
            if gs.cont_tours == 70:
                break

        self.driver.quit()
        print("Ejecutando hilos")
        tours = self.handler_Multithreading(gs.tours_to_insert, self.parsing_data_tours, self.session)
        print("Guardando datos en Google sheets")
        msg = gs.save_tours(tours, self.fecha, self.city)
        del gs
        return msg
    
    def main(self):
        number_try = 0
        while True:
            try:
                print("Creando URLs")
                url_restaurants, url_tours = self.create_urls()
            except:
                number_try += 1
            else:
                break

            if number_try > 5:
                self.driver.quit()
                return "Se realizaron varios intentos"

        if self.opcion == "RESTAURANTES":
            print("Buscando la lista de Restaurantes")
            msg = self.search_restaurants(url_restaurants)
            return msg
        elif self.opcion == "TOURS":
            print("Buscando la lista de Tours")
            msg = self.search_tours(url_tours)
            return msg
        else:
            return "Actividad no valida"
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--city",
                        help='Usado para especificar la ciudad busqueda',
                        default='', required=True)
    parser.add_argument("--opcion",
                        help='Especificar la actividad de busqueda: Restaurantes, Tours',
                        default='', required=True)
    parser.add_argument("--precio",
                        help='Precio del restaurante',
                        default='media')
    parser.add_argument("--fecha",
                         help='Fecha',
                        default='30/07/2020')
    parser.add_argument("--mode",
                         help='Opcion para ver el scrapping Oculto o ver',
                        default='Oculto')
    args = parser.parse_args()
    tp = Tripadvisor(args.city, args.opcion, args.precio, args.fecha, args.mode)
    #tp = Tripadvisor("bariloche", "restaurantes", "30/08/2020", "oculto")
    tp.main()
