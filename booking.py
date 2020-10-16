#https://developers.google.com/sheets/api/quickstart/python 
import argparse
import requests
from bs4 import BeautifulSoup
import sys
import json
from core.ThreadScraper import ThreadScraperBooking
from core import core
from urllib.parse import quote_plus, unquote
from time import sleep

class Booking():
    def __init__(self):
        self.session = requests.Session()
        self.REQUEST_HEADER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36"}
        self.list_hotels_name = []

    def get_max_offset(self, soup):
        all_offset = 0
        pagination = soup.find_all('li', {'class': 'sr_pagination_item'})
        if len(pagination) > 0:
            all_offset = pagination[-1].get_text().splitlines()[-1]
        return all_offset

    def create_url(self, city, country, category, review, offset):
        """
            Buscar categoria Otros --> &nflt=class%3D0%3B
            Categora concatenada ----> &nflt=class%3D1%3Bclass%3D2%3B&rsf=
            puntuacion ---> &nflt=review_score%3D90%3B valores posibles 90,80,70,60
            nflt=review_score%3D60%3Bclass%3D5%3B&rsf=
        """
        payload = {}
        filter_search = "nflt="
        if category:
            if category != "-1":
                filter_search+= "class%3D{}%3B".format(str(category))

        if review:
            if review != "-1":
                filter_search+= "review_score%3D{}%3B".format(str(review))

        url = "https://www.booking.com/searchresults.es.html?" \
            "ss={city}%2C%20{country}&{filter}&offset={offset}" \
            .format(city=quote_plus(city), country=quote_plus(country), filter=filter_search,offset=offset)
        return url

    def process_data(self, city, country, category, review):
        offset = 0
        threads = []
        max_offset = 0
        
        starting_url = self.create_url(city, country, category, review, offset)
        response = requests.get(starting_url, headers=self.REQUEST_HEADER)
        soup = BeautifulSoup(response.text, "lxml")

        max_offset = int(self.get_max_offset(soup))
        print(starting_url)
        print("Numero de paginas", max_offset)
        if max_offset > 0:
            for i in range(int(max_offset)):
                t = ThreadScraperBooking(self.session, city, country, category,
                              review, offset, self.parsing_data)
                threads.append(t)
                offset += 25
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        else:
            t = ThreadScraperBooking(self.session, city, country, category,
                review, offset, self.parsing_data)
            threads.append(t)
            t.start()
            t.join()

        return ThreadScraperBooking.process_result

    def parsing_data(self, session, city, country, category, review, offset):
        result = []
        not_valid = ["APARTAMENTO", "APARTAMENTOS", "APARTAHOTEL", "DEPARTAMENTO", "APARTA", "CASA O CHALET", "CASAS Y CHALETS"]
        url = self.create_url(city, country, category, review, offset)

        try:
            response = session.get(url, headers=self.REQUEST_HEADER, timeout=10)
        except:
            try:
                response = session.get(url, headers=self.REQUEST_HEADER, timeout=10)
            except:
                return result

        soup = BeautifulSoup(response.text, "lxml")
    
        hotels = soup.select("#hotellist_inner div.sr_item.sr_item_new")
        for hotel in hotels:
            hotel_name = core.get_hotel_name(hotel)
            property_type = core.get_property_type_hotel(hotel).upper()
            if not property_type in not_valid:
                result.append(hotel_name)
        session.close()
        return result

    def retrieve_data(self, city, country, category, review):
        result = self.process_data(city, country, category, review)
        return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--country",
                        help='Usado para especificar el pais de busqueda',
                        default='')
    parser.add_argument("--city",
                        help='Usado para especificar la ciudad de busqueda',
                        default='')
    parser.add_argument("--category",
                        help='Usado para especificar la categoria',
                        default='')
    parser.add_argument("--review",
                        help='Usado para especificar la puntuacion',
                        default='')

    args = parser.parse_args()
    if args.country == '' and args.city == '':
        parser.error('Accion no permitida, use la opcion --city o --country')

    bk = Booking()
    res = bk.retrieve_data(args.city, args.country, args.category, args.review)
    print(res)  