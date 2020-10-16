from bs4 import BeautifulSoup
import re
import ast
import base64

def get_hotel_name(hotel):
    if hotel.select_one("span.sr-hotel__name") is None:
        return ''
    else:
        return hotel.select_one("span.sr-hotel__name").text.strip()

def get_tel_facebook(hotel):
    elements = hotel.find_all("div",attrs={'class':'_50f4'},text=re.compile(r'Llamar'))
    if len(elements) == 0:
        return ''
    else:
        return elements[0].text.split("Llamar ")[1].strip()

def get_category_facebook(hotel):
    elements = hotel.find_all('a',href=re.compile(r'/pages/category/.*o*t*l?'))
    if len(elements) == 0:
        return False
    else:
        return True

def get_title_facebook(hotel):
    title = hotel.find('title')
    if title is None:
        return ''
    else:
        return title.text.split(" - ")[0].replace("  "," ").strip().lower()

def get_tel_facebook_pages(response):
    pos_init = response.find('+54 294 443-0644')
    if pos_init == -1:
        return ''
    else:
        pos_end = response[pos_init:].find("<")
        tel = response[pos_init:pos_init+pos_end]
        return tel.replace("'","")

def get_mail_facebook(hotel):
    #mail = hotel.find('a', href = re.compile(r'mailto:'))
    mail = hotel.findChildren('a', href = re.compile(r'mailto:'))
    if len(mail) == 0:
        return ''
    return mail[0].text.strip()

def get_property_type_hotel(hotel):
    if hotel.select_one("span.bh-property-type") is None:
        return 'No tiene'
    else:
        return hotel.select_one("span.bh-property-type").text.strip()

def get_restaurant_name_list(restaurant):
    name = restaurant.select_one("._15_ydu6b")
    if name is None:
        return ''
    return name.text.split(". ")[-1]

def get_restaurant_name(restaurant):
    name = restaurant.select_one("._3a1XQ88S")
    if name is None:
        return ''
    return name.text.strip()

def get_restaurant_tel(restaurant):
    telephone = restaurant.find('a', href = re.compile(r'tel:+'))
    if telephone is None:
        return ''
    return telephone.text.strip()

def get_restaurant_mail(restaurant):
    mail = restaurant.find('a', href = re.compile(r'mailto:'))
    if mail is None:
        return ''
    return mail.attrs['href'].split(":")[1].split("?subject")[0].strip()

def get_restaurant_website(restaurant):
    regex = re.compile(r'\"website\":\"http.*?"')
    script = restaurant.find('script', text = regex)
    if script is None:
        return ''
    link = regex.findall(str(script))
    website = link[0][11:-1]
    return website

def get_tour_name_list(restaurant):
    name = restaurant.select_one("._1QKQOve4")
    if name is None:
        return ''
    return name.text

def get_tour_name(tour):
    name = tour.select_one("#HEADING")
    if name is None:
        return ''
    return name.text.strip()

def decode_link(code):
    decoded = base64.b64decode(code)
    return decoded.decode().split("_")[1]

def get_tour_tel(tour):
    regex = re.compile(r'\"phone\":\".*?"')
    script = tour.find('script', text = regex)
    if script is None:
        return ''
    link = regex.findall(str(script))
    telephone = link[0][9:-1]
    return telephone

def get_tour_mail(tour):
    regex = re.compile(r'\"email\":\".*?"')
    script = tour.find('script', text = regex)
    if script is None:
        return ''
    link = regex.findall(str(script))
    email = link[0][9:-1]
    try:
        email = decode_link(email)
    except:
        return email
    else:
        email = email.replace("mailto:","")
        return email

def get_tour_website(tour):
    regex = re.compile(r'\"website\":\".*?"')
    script = tour.find('script', text = regex)
    if script is None:
        return ''
    link = regex.findall(str(script))
    website = link[0][11:-1]
    try:
        website = decode_link(website)
    except:
        return website
    else:
        return website
