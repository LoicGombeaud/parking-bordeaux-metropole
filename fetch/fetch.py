import argparse
import json
import mariadb
import os
import requests


# Parse input arguments
parser = argparse.ArgumentParser()
parser.add_argument('--db-host',
                    default=os.getenv('DB_HOST',
                                      default='parking-saint-jean-mariadb'))
parser.add_argument('--db-name',
                    default=os.getenv('DB_NAME',
                                      default='parking-saint-jean'))
parser.add_argument('--db-user',
                    default=os.getenv('DB_USER'))
parser.add_argument('--db-password',
                    default=os.getenv('DB_PASSWORD'))
parser.add_argument('--opendata_key',
                    default=os.getenv('OPENDATA_KEY'))
args = parser.parse_args()

# Open database connection
connection = mariadb.connect(host=args.db_host,
                             database=args.db_name,
                             user=args.db_user,
                             password=args.db_password,
                             autocommit=True)
cursor = connection.cursor()

# Define URL from which to retrieve parking data
url = 'https://data.bordeaux-metropole.fr/geojson?key=%s&typename=st_park_p' % args.opendata_key

# Retrieve Saint-Jean parkings
saint_jean_parking_ids = []
cursor.execute('SELECT id FROM parking')
for saint_jean_parking in cursor.fetchall():
    saint_jean_parking_ids.append(saint_jean_parking[0])

# Load free spots data into the database
print('Downloading measurement data...')
r = requests.get(url)
with open('parking.json', 'w') as parking_file:
    parking_file.write(r.content.decode('utf-8'))
print('Done')

print('Loading measurement data into the DB...')
with open('parking.json', 'r') as parking_file:
    parkings = json.load(parking_file)['features']
    saint_jean_parkings = filter(lambda p: p['properties']['ident'] in saint_jean_parking_ids,
                                 parkings)
    for parking in saint_jean_parkings:
        print(parking['properties']['ident'])
        print(parking['properties']['nom'])
        print(parking['properties']['mdate'])
        print(parking['properties']['libres'])
        print()
        parking_id = parking['properties']['ident']
        mdate = parking['properties']['mdate'].split('+')[0]
        free_spots = parking['properties']['libres']
        cursor.execute('INSERT IGNORE INTO parking_data (parking_id, mdate, free_spots) VALUES (?, ?, ?)',
                       (parking_id,
                        mdate,
                        free_spots))
connection.commit()

# Close connection to the database
cursor.close()
connection.close()
