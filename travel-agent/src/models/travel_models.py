# Data models for Travel AI Agent
class TravelRequest:
    def __init__(self, destination, start_date, end_date, number_of_travelers):
        self.destination = destination
        self.start_date = start_date
        self.end_date = end_date
        self.number_of_travelers = number_of_travelers

class FlightDetails:
    def __init__(self, airline, flight_number, departure_time, arrival_time, price):
        self.airline = airline
        self.flight_number = flight_number
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.price = price

class AccommodationDetails:
    def __init__(self, hotel_name, check_in_date, check_out_date, price_per_night, total_price):
        self.hotel_name = hotel_name
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.price_per_night = price_per_night
        self.total_price = total_price
