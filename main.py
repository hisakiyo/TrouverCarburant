import requests
import zipfile
import io
import json, xmltodict
from geopy import distance


gas_url = 'https://donnees.roulez-eco.fr/opendata/instantane'
lat = '50.938982' # Votre latitude
long = '1.869328' # Votre longitude
max_km = 40 # Votre distance max en KM pour aller faire le plein
gas = 'Gazole' # Type de carburant (eg. Gazole, E85, E10, SP98, SP95)


def convert_xml_to_json(xml_file):
    # Convert the XML to JSON
    return json.loads(json.dumps(xmltodict.parse(xml_file)))

# Function to calc if gas station is in range
def is_in_range(station_lat, station_long):
    station_lat = float(station_lat)
    station_long = float(station_long)
    station_lat /= 100000
    station_long /= 100000
    # Calculate the distance between the station and the user
    distances = distance.distance((lat, long), (station_lat, station_long)).km
    # If the distance is less than the max_km, return True
    if distances < max_km:
        return True
    else:
        return False

# Fetches the ZIP file from the API, unzip it and parse the XML
def fetch_data(url):
    # Get the ZIP file
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    # Unzip the file
    data = z.read('PrixCarburants_instantane.xml')
    # Parse the XML
    return convert_xml_to_json(data.decode('ISO-8859-1'))

# Return all the gas stations in the range
def get_gas_stations(url):
    # Fetch the data
    data = fetch_data(url)
    # Get the list of stations
    stations = data['pdv_liste']['pdv']
    # Create a list of stations in the range
    stations_in_range = []
    # For each station
    for station in stations:
        # If it is in the range
        if is_in_range(station['@latitude'], station['@longitude']) and "prix" in station:
            # Add it to the list
            obj = {
                'adresse': station['adresse'] + ' - ' + station['@cp'] + ' ' + station['ville'],
                'latitude': float(station['@latitude']) / 100000,
                'longitude': float(station['@longitude']) / 100000
            }
            # If station['prix'] is a list, get the first element
            if isinstance(station['prix'], list):
                for gas_type in station['prix']:
                    obj[gas_type['@nom']] = {
                        'price': gas_type['@valeur'],
                        'maj': gas_type['@maj']
                    }
                stations_in_range.append(obj)
            else:
                obj[station['prix']['@nom']] = {
                    'price': station['prix']['@valeur'],
                    'maj': station['prix']['@maj']
                }
                stations_in_range.append(obj)
    
    # Return the list
    return stations_in_range

# Filter and sort the stations
def filter_and_sort(stations):
    # Create a list of stations
    stations_in_range = []
    # For each station
    for station in stations:
        # If it has the gas type
        if gas in station:
            # Add it to the list
            stations_in_range.append(station)
    # Sort the list by price by descending order
    stations_in_range.sort(key=lambda station: station[gas]['price'], reverse=True)
    # Return the list
    return stations_in_range

# Print the stations
def print_stations(stations):
    # For each station
    for station in stations:
        # Print the station
        print('\n' + station['adresse'] + ' (' + str(station['latitude']) + ', ' + str(station['longitude']) + ')')

        # If it has the gas type
        if gas in station:
            # Print the price
            print('\t', gas, ':', station[gas]['price'], '€', '(' + station[gas]['maj'] + ')')
            print('\t', '% d\'économie par rapport au plus cher', ':', round((1 - float(station[gas]['price']) / float(stations[0][gas]['price'])) * 100, 2), '%')

data = get_gas_stations(gas_url)
data = filter_and_sort(data)
print_stations(data)
