from datetime import datetime, timedelta

import flask
from flask import Flask, render_template, request, jsonify
import sqlite3
from sqlite3 import Error
import json
app = Flask(__name__)

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
        response = flask.jsonify(get_all_entries(create_connection(r"C:\sqlite\db\tempsensor.db")))
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response


aaa
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
