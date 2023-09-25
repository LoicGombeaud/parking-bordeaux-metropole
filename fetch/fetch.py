import argparse
import json
import mariadb
import os
import requests


# Parse input arguments
parser = argparse.ArgumentParser()
parser.add_argument('--db-host',
                    default=os.getenv('DB_HOST',
                                      default='parking-bordeaux-metropole-mariadb'))
parser.add_argument('--db-name',
                    default=os.getenv('DB_NAME',
                                      default='parking-bordeaux-metropole'))
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

# Load free spots data into the database
print('Downloading measurement data...')
r = requests.get(url)
with open('parking.json', 'w') as parking_file:
    parking_file.write(r.content.decode('utf-8'))
print('Done')

print('Loading measurement data into the DB...')
with open('parking.json', 'r') as parking_file:
    parkings = json.load(parking_file)['features']
    for parking in parkings:
        parking_id = parking['properties']['ident']
        name = parking['properties']['nom']
        coordinates = parking['geometry']['coordinates']
        mdate = parking['properties']['mdate'].split('+')[0]
        total_spots = parking['properties']['total']
        free_spots = parking['properties']['libres']
        print(f'{parking_id=}')
        print(f'{name=}')
        print(f'{coordinates=}')
        print(f'{mdate=}')
        print(f'{total_spots=}')
        print(f'{free_spots=}')
        print()
        if free_spots is not None:
            # Save parking info
            cursor.execute('INSERT IGNORE INTO parking VALUES (?, ?, POINT(?, ?), ?)',
                           (parking_id,
                            name,
                            coordinates[0],
                            coordinates[1],
                            total_spots
                            ))
            cursor.execute('INSERT IGNORE INTO parking_data (parking_id, mdate, free_spots) VALUES (?, ?, ?)',
                           (parking_id,
                            mdate,
                            free_spots))

# Close connection to the database
cursor.close()
connection.close()
