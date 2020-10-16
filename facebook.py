import requests, re
from core import core
from time import sleep
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from googlesearch import filter_result
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.utils import get_user_agent_list, get_random_user_agent, get_random_sleep

class Facebook(object):
    def __init__(self, items, city):
        self.items = items
        #self.hotels = ["Altuen Hotel Suite & Spa"]
        self.city = city
        self.base_url = "https://www.facebook.com/"
        self.session = requests.Session()
        self.REQUEST_HEADER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36"}
        self.user_agents_list = get_user_agent_list()
    
    def get_driver(self, mode="VER"):
        from selenium import webdriver
        import os, sys
        options = webdriver.ChromeOptions()
        install_folder = os.path.abspath(os.path.split(__file__)[0])
        if sys.platform == 'win32':
            exec_path = "%s\\drivers\\chromedriver.exe"%install_folder
        else:
            exec_path = "%s/drivers/chromedriver"%install_folder

        if mode.upper() == "OCULTO":
            options.add_argument("--disable-logging")
            options.add_argument("window-size=1400,700")
            options.add_argument('headless')
        
        return webdriver.Chrome(executable_path=exec_path, chrome_options=options)
    
    def get_links(self, soup, stop=None):
        links = []
        try:
            anchors = soup.find(id='search').findAll('a')
        except AttributeError:
            # Remove links of the top bar.
            gbar = soup.find(id='gbar')
            if gbar:
                gbar.clear()
            anchors = soup.findAll('a')

        cont = 1
        for a in anchors:
            try:
                link = a['href']
            except KeyError:
                continue

            # Filter invalid links and links pointing to Google itself.
            link = filter_result(link)
            if not link:
                continue

            if "facebook" in link:
                links.append(link)

            if stop and cont >= stop:
                break
            cont+=1

        return links
    
    def search_google_driver(self, query, stop=None):
        driver = self.get_driver()
        query = quote_plus(query)
        url = "https://www.google.com/search?q=%s"%query
        driver.get(url)
        sleep(5)
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        links = self.get_links(soup, stop)
        return links
    
    def search_google(self, query, stop=None):
        query = quote_plus(query)
        url = "https://www.google.com/search?q=%s"%query
        header = get_random_user_agent(self.user_agents_list)
        try:
            response = requests.get(url, headers={"User-Agent": header}, timeout=10)
        except:
            try:
                header = get_random_user_agent(self.user_agents_list)
                response = requests.get(url, headers={"User-Agent": header}, timeout=10)
            except:
                return []
        if response.status_code == 429:
            raise Exception("Google bloqueo tu ip")

        soup = BeautifulSoup(response.text, 'lxml')
        links = self.get_links(soup, stop)
        return links
        
    def scrapper_facebook_hotel_driver(self):
        for item in self.items:
            name = item
            query = "{}+{}+facebook+inicio".format(name, self.city)
            links = self.search_google_driver(query)
            item["links"] = links

        with ThreadPoolExecutor(max_workers=5) as executor:
            for item in self.items:
                name = item
                query = '"{}"+{}+facebook'.format(name, self.city)
                threads.append(executor.submit(self.parsing_data, self.session, query, name, self.city, "driver", item["links"]))

        for task in as_completed(threads):
            results.append(task.result())

        return results
        
    def scrapper_facebook_hotel(self):
        threads = []
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for item in self.items:
                name = item
                query = '"{}"+{}+facebook'.format(name, self.city)
                threads.append(executor.submit(self.parsing_data, self.session, query, name, self.city, "consola", []))

        for task in as_completed(threads):
            results.append(task.result())

        return results

    def scraping_facebook_tripadvisor(self, name):
        try:
            query = "{}+{}+facebook+inicio".format(name, self.city)
            data = self.parsing_data(self.session, query, name, self.city, "consola", [])
            return data
        except Exception as e:
            print(e)
            return {}

    def parsing_data(self, session, query, name, city, source, links):
        list_url = []
        not_valid = ['/public/', '/post/', "/videos"]
        if source == "driver":
            results = links
        else:
            s = get_random_sleep()
            sleep(s)
            results = self.search_google(query, stop=4)
        for result in results:
            valid = [n for n in not_valid if n in result ]
            if len(valid) == 0:
                list_url.append(result)

        if len(list_url) == 0:
            #print(name, "Sin resultados en google")
            return {"name": name, "city": city, "email": "", "telephone": ""}

        data_find = False
        aux = []
        print(list_url)
        for url in list_url:
            is_find, info = self.try_extracting_data(url, name, city, session)
            if is_find == True:
                aux.append(info)
                data_find = True
                #return info
                #break
                   
        if data_find == False:
            return info
        else:        
            for r in aux:
                if r["title"] == name.strip().lower():
                    return r
            
            return aux[0]
  
    def validate_title(self, name, title):
        regex = re.compile(r'%s.*'%name.lower())
        return regex.findall(title)

    def try_extracting_data(self, url, name, city, session):
        url_split = url.split("/")
        info = {}
        info["name"] = name
        info["city"] = city
        if url_split[3] != "pages":
            _id = url_split[3]
            starting_url =  "{}pg/{}/about/?ref=page_internal".format(self.base_url, _id)         
        elif url_split[3] == "pages" and url_split[4] == "category":
            _id = url_split[6]
            starting_url =  "{}pg/{}/about/?ref=page_internal".format(self.base_url, _id)
        else:
            #print(name, url, "Es una pagina")
            return False, {"name": name, "city": city, "email": "", "telephone": ""}

        header = get_random_user_agent(self.user_agents_list)
        try:
            response = session.get(starting_url, headers={"User-Agent": header}, timeout=10)
        except Exception as e:
            print("ocurrio un error %s"%e)
            try:
                sleep(5)
                header = get_random_user_agent(self.user_agents_list)
                response = session.get(starting_url, headers={"User-Agent": header}, timeout=10)
            except Exception as e:
                print("ocurrio error 2 %s"%e)
                return False, {"name": name, "city": city, "email": "", "telephone": ""}
        
        #print(starting_url)
        soup = BeautifulSoup(response.text, 'lxml')#,'html.parser')
        category = core.get_category_facebook(soup)
        title = core.get_title_facebook(soup)

        isHotel = self.validate_title(name, title)

        if category and len(isHotel) > 0:
            info["telephone"] = core.get_tel_facebook(soup)
            info["email"] = core.get_mail_facebook(soup)
            info["title"] = title
            session.close() 
            if info["email"] == "":
                return False, info
            
            return True, info
        else:
            return False, {"name": name, "city": city, "email": "", "telephone": ""}

def scrapper_facebook(url):
    base_url = "https://www.facebook.com/"
    url_split = url.split("/")
    if url_split[3] != "pages":
        _id = url_split[3]
        starting_url =  "{}pg/{}/about/?ref=page_internal".format(base_url, _id)
    else:
        return ''
    header = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36"}
    try:
        response = requests.get(starting_url, headers=header, timeout=10)
        soup = BeautifulSoup(response.text, 'lxml')#,'html.parser')
        email = core.get_mail_facebook(soup)
        return email
    except:
        return ''

# def test(h):
#     hotels = []
#     hotels.append(h)
#     fb = Facebook(hotels, "roma")
#     r = fb.scrapper_facebook_hotel()
#     print(r)

# import sys
# test(sys.argv[-1])
