from datetime import datetime, timedelta

import flask
from flask import Flask, render_template, request, jsonify
import sqlite3
from sqlite3 import Error
import json

app = Flask(__name__)


# TO UTILIZE THIS PROJECT, IN THE TERMINAL TYPE 'flask run --host=0.0.0.0'
# IN THE REACT APP CHANGE THE GET RESPONSE URL TO WHATEVER THIS APPLICATION PRODUCES FOR EXAMPLE:
# MINE WAS http://192.168.2.201:5000 WHEN RUNNING THE APP ON MY WIFI
# SO THE REACT APP WILL TALK TO http://192.168.2.201:5000/api/temperature AND RECIEVE A JSON RESPONSE
# OF TEMP, HUMIDITY, and TIMESTAMP
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def create_entry(conn, project):
    sql = ''' INSERT INTO data_entry(temp,humidity,timestamp)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, project)
    conn.commit()
    return cur.lastrowid


def get_all_entries(conn):
    try:
        sql = '''SELECT * FROM data_entry'''
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        column_names = [desc[0] for desc in cur.description]

        entries = [dict(zip(column_names, row)) for row in rows]

        json_entries = json.dumps(entries)
        return json_entries
    except Exception as e:
        print(f"Error in get_all_entries: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route('/temperature')
def showTables():
    # Initialize an empty list to store the extracted data
    data = []
    labels = []  # Initialize an empty list for labels

    # Open the file for reading
    with open('dht_data.txt', 'r') as file:
        lines = file.readlines()
        if not lines:
            print("File is empty.")
        else:
            latest_time = datetime.strptime(lines[-1].strip().split(' | ')[1], '%H-%M')

        for line in lines:
            # Split the line by commas and extract the values
            values = line.strip().split(', ')
            if len(values) >= 3:
                value1 = float(values[0])
                value2 = float(values[1][:-1])  # Remove the '%' character and convert to float
                timestamp_str = values[2]

                # Extract the day and time parts of the timestamp and parse them
                day, time_str = timestamp_str.split(' | ')
                timestamp = datetime.strptime(time_str, '%H-%M')

                # Calculate the time difference in seconds
                time_difference = (latest_time - timestamp).total_seconds()

                # Convert time difference to intervals of 5 minutes (300 seconds)
                time_difference_in_minutes = int(time_difference / 300)

                data.append((value1, value2, time_difference))

                # Format the labels with the day and time in the desired format "Day | Hour : Minute"
                label = f"{day} | {timestamp.strftime('%H')} : {timestamp.strftime('%M')}"
                labels.append(label)

    # Now the 'data' list contains the extracted values with time differences, and 'labels' contain formatted labels in the "Day | Hour : Minute" format
    print(data)
    print(labels)

    header = "Line Graph"
    description = "This is the first line graph"
    return flask.render_template('line_graph_example.html', data=data, labels=labels, header=header)


@app.route('/')
def index():
    return flask.render_template("index.html")


import json

def parse_data_line(line):
    # Split the line into temperature, humidity, and timestamp using commas and "|"
    temperature, humidity, timestamp = line.strip().split(', ')

    try:
        # Convert temperature and humidity to float values
        temperature = float(temperature)
        humidity = float(humidity)

        # Create a dictionary for the data
        data = {
            'temp': temperature,
            'humidity': humidity,
            'timestamp': timestamp
        }

        # Return the JSON object
        return json.dumps(data)
    except ValueError as e:
        print(f"Warning: Skipping line '{line.strip()}'. Error: {e}")
        return None



def read_dht_data(file_path):
    # Initialize an empty list to store JSON objects
    data_objects = []

    # Open the file and read each line
    with open(file_path, 'r') as file:
        for line in file:
            # Parse the data and create a JSON object
            data_object = parse_data_line(line)

            # Append the JSON object to the list
            data_objects.append(data_object)

    # Return the list of JSON objects
    return data_objects


@app.route('/api/temperature', methods=['POST', 'GET'])
def addData():
    if request.method == 'POST':
        try:
            # Receive the JSON data from the request
            data = request.get_json()
            print("Data received")
            print(str(data))

            # Ensure that the JSON data contains three values
            if 'temperature' in data and 'humidity' in data and 'timestamp' in data:
                temperature = data['temperature']
            humidity = data['humidity']
            timestamp = data['timestamp']

            # Append the data to a data file
            with open('dht_data.txt', 'a') as file:
                file.write(f"{str(temperature)}, {str(humidity)}, {timestamp}\n")

            # Insert the data into the database
            conn = sqlite3.connect('C:\sqlite\db\\tempsensor.db')
            cur = conn.cursor()
            cur.execute("INSERT INTO data_entry (temp, humidity, timestamp) VALUES (?, ?, ?)",
                        (temperature, humidity, timestamp))
            conn.commit()
            conn.close()

            return jsonify({"message": "Data inserted successfully."}), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'GET':
        print("Get request called")
        # response = flask.jsonify(get_all_entries(create_connection(r"C:\sqlite\db\tempsensor.db")))
        response = jsonify(read_dht_data("dht_data.txt"))
        print(response)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response


database = r"C:\sqlite\db\tempsensor.db"
connection = create_connection(r"C:\sqlite\db\tempsensor.db")

sql_create_dataentry_table = """ CREATE TABLE IF NOT EXISTS data_entry (
                                                id integer PRIMARY KEY,
                                                temp double NOT NULL,
                                                humidity double,
                                                timestamp text
                                            ); """

conn = create_connection(database)
create_table(connection, sql_create_dataentry_table)

# create tables
if conn is not None:
    # create projects table
    create_table(conn, sql_create_dataentry_table)
else:
    print("Error! cannot create the database connection.")
print("Table Created")

if __name__ == '__main__':
    app.run()
