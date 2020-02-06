from flask import Flask, redirect, url_for ,g , jsonify
import sqlite3 , requests
# from flask_mysqldb import MySQL
app = Flask(__name__)

DATABASE = './potholedb.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = make_dicts  # make dictionary of rows
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


@app.route('/')
def home():
    return redirect(url_for('getcomplaints'))


@app.route('/post-complaints', methods=['POST'])
def postcomplaints():
    #token = request.form['userid']
    # if(token is not none):

    # duplication checking <..TODO >
    
    #values from app_interface
    data = request.get_json()  # get json from them
    category = data['category']
    latitude = data['latitude']
    longitude = data['longitude']
    image_name = data['image_name']
    address = data['address']
    landmark = data['landmark'] 
    #getting traffic level of complaint point

    api_key="jqaiP21S534IESqdD667p0Aiheea7gpt"
    # Just testing out

    URL="https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point="+str(latitude)+"%2C"+str(longitude)+"&key="+api_key
    r=requests.get(url=URL)

    traffic_data=r.json()

    free_flow_speed=traffic_data['flowSegmentData']['freeFlowSpeed']   
    current_speed=traffic_data['flowSegmentData']['currentSpeed']
    free_flow_travel_time=traffic_data['flowSegmentData']['freeFlowTravelTime']
    current_travel_time=traffic_data['flowSegmentData']['currentTravelTime']

    traffic_value=free_flow_speed - current_speed  + (free_flow_travel_time - current_travel_time)/free_flow_travel_time


    cur = get_db().cursor()
    cur.execute('''INSERT into complaints (complaint_id,complaint_category,
				complaint_latitude,complaint_longitude,image_name) VALUES
				(:id,:cat,:lat,:long,:img)''', {"id": 1, "cat": category, "lat": latitude, "long": longitude, "img": image_name})

    return 'asd'


@app.route('/get-complaints', methods=['GET', 'POST'])
def getcomplaints():
    #token = request.form['userid']
    # if(token is not none):
    # get from db
    cur = get_db().cursor()
    cur.execute("select * from complaints")
    rows = cur.fetchall()
    if rows is not None:
        rows.insert(0, {'status': 1})
        response = jsonify(rows)
    return response


if __name__ == '__main__':
    app.run(debug=True)