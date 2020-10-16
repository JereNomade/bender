import argparse
import requests
import simplejson
from time import sleep
from booking import Booking
from facebook import Facebook
from datetime import datetime
from core.utils import message_api
from tripadvisor import Tripadvisor
from googleSheets import Googlesheet
from urllib.parse import quote_plus, unquote

class Controller(object):
    def __init__(self, city, country, category, review, precio, fecha, scraper, debug, mode):
        self.city = city
        self.country = country
        self.category = category
        self.review = review
        self.precio = precio
        self.scraper = scraper
        self.fecha = fecha
        self.debug = debug
        self.mode = "oculto"

    def debug_msg(self, msg):
        if self.debug == "yes":
            print(msg)
        else:
            message_api(msg)

    def scrapper_tripadvisor_restaurants(self):
        tp_r = Tripadvisor(self.city, "Restaurantes", precio=self.precio, fecha=self.fecha, mode=self.mode)
        msg = tp_r.main()
        del tp_r
        self.debug_msg(msg)
        return 
    
    def scrapper_tripadvisor_tours(self):
        tp_t = Tripadvisor(self.city, "tours", precio=self.precio, fecha=self.fecha, mode=self.mode)
        msg = tp_t.main()
        del tp_t
        self.debug_msg(msg)
        return

    def scrapper_booking(self):
        bk = Booking()
        hotels = bk.retrieve_data(self.city, self.country, self.category, self.review)
        print("hoteles encontrados", len(hotels))
        self.debug_msg("Finalizado")
        gs = Googlesheet()
        gs.get_all_values("Hospedajes")
        gs.find_hotels(hotels)
        hotels_insert = gs.hotel_to_insert
        print("hotels_insert", len(hotels_insert))
        print("hoteles a insertar", len(hotels_insert))
        print(hotels_insert)
        self.debug_msg("Facebook")
        fb = Facebook(hotels_insert, self.city)
        data_hotel = fb.scrapper_facebook_hotel()
        print(data_hotel)
        msg = gs.save_hotels(data_hotel, self.fecha, self.city)
        self.debug_msg(msg)
        
    def runner(self):
        list_scraper = self.scraper.split(",")[:-1]
        ban = False
        try:
            if "HOTELES" in list_scraper:
                ban = True
                self.debug_msg("Booking")
                self.scrapper_booking()
            if "RESTAURANTES" in list_scraper:
                if ban:
                    self.debug_msg("Favor esperar 2 minutos.")
                    sleep(120)
                ban = True
                self.debug_msg("Tripadvisor - Restaurante")
                self.scrapper_tripadvisor_restaurants()
            if "TOURS" in list_scraper:
                if ban:
                    self.debug_msg("Favor esperar 2 minutos.")
                    sleep(120)
                ban = True
                self.debug_msg("Tripadvisor - Tours")
                self.scrapper_tripadvisor_tours()
        except Exception as e:
            print(e)
            self.debug_msg("Error: Favor intentalo nuevamente %s"%e)
            return "Error: Favor intentalo nuevamente"
        # else:
        #     self.debug_msg("Finalizado")
        #     return "Scrapper Finalizado"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--city",
            help='Ciudad de la busqueda',
            default='')
    parser.add_argument("--country",
            help='Pais de busqueda',
            default='None')
    parser.add_argument("--category",
            help='Categoria del hotel',
            default='3')
    parser.add_argument("--review",
            help='Puntuacion del hotel',
            default='80')
    parser.add_argument("--precio",
            help='Puntuacion del hotel',
            default='media')
    parser.add_argument("--fecha",
            help='Fecha de permanencia',
            default='')
    parser.add_argument("--scraper",
            help='Hoteles, Restaurantes, Tours',
            default='')
    parser.add_argument("--debug",
            help='Debug',
            default='no')
    parser.add_argument("--mode",
            help='Visualizar lo que hace el scrapper',
            default='oculto')

    args = parser.parse_args()
    if args.country == '' and args.city == '':
        parser.error('Accion no permitida, use la opcion --city o --country')
    #city, country, category, review, precio, fecha, scraper, mode
    ctl = Controller(
        city=args.city, country=args.country, category=args.category, review=args.review, precio=args.precio, fecha=args.fecha, 
        scraper=args.scraper, debug=args.debug, mode=args.mode
    )
    ctl.runner()
