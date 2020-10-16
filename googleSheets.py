import gspread
import argparse
import requests
import simplejson
import pandas as pd
from time import sleep
from pprint import pprint
from datetime import datetime
from urllib.parse import quote_plus, unquote
from oauth2client.service_account import ServiceAccountCredentials

class Googlesheet(object):
    cont_hotels = 0
    hotel_to_insert = []
    cont_restaurants = 0
    restaurants_to_insert = []
    cont_tours = 0
    tours_to_insert = []
    df = []

    def __init__(self):
        self.scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
        self.sheet = None
        self.worksheet_hotels = None
        self.worksheet_restaurants = None
        self.worksheet_tours = None
        self.auth_google_sheet()

    def auth_google_sheet(self):
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials_google.json", self.scope)
        client = gspread.authorize(creds)
        self.sheet = client.open("BD Acuerdos") # Open the spreadhseet
        self.worksheet_hotels = self.sheet.worksheet("Hospedajes")
        self.worksheet_restaurants = self.sheet.worksheet("Restaurantes")
        self.worksheet_tours = self.sheet.worksheet("Tours")

    def get_all_values(self, sheet):
        wks = self.sheet.worksheet(sheet)
        data = wks.get_all_values()
        headers = data.pop(0)
        self.df = pd.DataFrame(data, columns=headers)

    def find_hotels(self, hotels):
        for hotel in hotels:
            if not (self.df["Nombre"] == hotel).any():
                l = [r for r in self.hotel_to_insert if r == hotel ]
                if len(l) == 0:
                    self.hotel_to_insert.append(hotel)
                    self.cont_hotels+=1
                
                if self.cont_hotels == 70:
                    break

    def find_restaurants(self, restaurants):
        for restaurant in restaurants:
            name = restaurant["name"]
            if not (self.df["Nombre"] == name).any():
                l = [r for r in self.restaurants_to_insert if r["name"] == name ]
                if len(l) == 0:
                    self.restaurants_to_insert.append(restaurant)
                    self.cont_restaurants+=1
                
            if self.cont_restaurants == 70:
                break

    def find_tours(self, tours):
        for tour in tours:
            name = tour["name"]
            if not (self.df["Nombre"] == name).any():
                l = [t for t in self.tours_to_insert if t["name"] == name ]
                if len(l) == 0:
                    self.tours_to_insert.append(tour)
                    self.cont_tours+=1

            if self.cont_tours == 70:
                break

    def save_tours(self, tours, fecha, city):
        cont = 0
        for tour in tours:
            name = tour.get("name", "")
            tel = tour.get("telephone", "")
            email = tour.get("email", "")
            if email != "":
                cont+=1
                self.worksheet_tours.append_row([email, name, "~ |", city, fecha, tel])

            if cont == 50:
                break
        return "Tripadvisor - Tours Finalizado"

    def save_restaurants(self, restaurants, fecha, city):
        cont = 0
        for restaurant in restaurants:
            name = restaurant.get("name","")
            tel = restaurant.get("telephone","")
            email = restaurant.get("email","")
            if email != "":
                cont+=1
                self.worksheet_restaurants.append_row([email, name, "~ |", city, fecha, tel])
            if cont == 50:
                break
        return "Tripadvisor - Restaurantes Finalizado"

    def save_hotels(self, hotels, fecha, city):
        cont = 0
        for hotel in hotels:
            name = hotel.get('name', '')
            tel = hotel.get('telephone', '')
            email = hotel.get('email', '')
            if email != "":
                cont+=1
                self.worksheet_hotels.append_row([email, name, "~ |", city, fecha, tel])
            if cont == 50:
                break
        return "Booking Finalizado"