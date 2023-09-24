import argparse
import mariadb
import os
from datetime import date
from datetime import timedelta


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
parser.add_argument('--day-to-compute',
                    default=(date.today() - timedelta(days=1)).isoformat())
args = parser.parse_args()

# Open database connection
connection = mariadb.connect(host=args.db_host,
                             database=args.db_name,
                             user=args.db_user,
                             password=args.db_password,
                             autocommit=True)
cursor = connection.cursor()

# Retrieve Saint-Jean parkings
saint_jean_parking_ids = []
cursor.execute('SELECT id FROM parking')
for saint_jean_parking in cursor.fetchall():
    saint_jean_parking_ids.append(saint_jean_parking[0])


# Compute hourly and daily minima for each parking
day_to_compute = args.day_to_compute
print('Computing daily and hourly minima for %s' % day_to_compute)
print()
minima_hourly = {}
minima_daily = {}
for parking_id in saint_jean_parking_ids:
    print('Parking ID: %s' % parking_id)
    minima_hourly[parking_id] = {}
    for hour_to_compute in range(0, 24):
        cursor.execute('SELECT MIN(free_spots) FROM parking_data WHERE parking_id = ? AND DATE(mdate) = ? AND HOUR(mdate) = ?',
                       (parking_id,
                        args.day_to_compute,
                        hour_to_compute))
        result = cursor.fetchone()
        if result[0] is not None: # do nothing if NULL / None
            minima_hourly[parking_id][hour_to_compute] = result[0]
    print(f'{minima_hourly[parking_id]=}')
    print()
    minima_daily[parking_id] = min(minima_hourly[parking_id].values())

print(f'{minima_daily=}')
print()

# Write minima to database
print('Writing minima to database...')
for parking_id in saint_jean_parking_ids:
    for hour in minima_hourly[parking_id]:
        cursor.execute('INSERT INTO minima_hourly VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE free_spots=?',
                       (parking_id,
                        day_to_compute,
                        hour,
                        minima_hourly[parking_id][hour],
                        minima_hourly[parking_id][hour]))
    cursor.execute('INSERT INTO minima_daily VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE free_spots=?',
                   (parking_id,
                    day_to_compute,
                    minima_daily[parking_id],
                    minima_daily[parking_id]))
print('Success!')

# Close connection to the database
cursor.close()
connection.close()
