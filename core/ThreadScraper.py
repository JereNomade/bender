import threading

class ThreadScraperBooking(threading.Thread):
   process_result = []

   def __init__(self, session, city, country, category, review, offset, parsing_data):
      threading.Thread.__init__(self)
      self.session = session
      self.city = city
      self.country = country
      self.category = category
      self.review = review
      self.offset = offset
      self.parsing_data = parsing_data

   def run(self):
      self.process_result.extend(self.parsing_data(self.session, self.city, self.country, self.category, self.review, self.offset))
