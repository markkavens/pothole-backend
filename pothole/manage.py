
from flask import *
import sqlite3 , requests, hashlib

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

@app.route('/admin-interface')
def adminInterface():
    return 'Hto'

@app.route('/post-complaints',methods=['POST'])
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
				(:id,:cat,:lat,:long,:img)''',{"id":1,"cat":category,"lat":latitude,"long":longitude,"img":image_name})
    for row in cur.execute('SELECT * FROM complaints'):
        print(row)
    get_db().commit()
    return "sone"



@app.route('/get-complaints',methods=['GET','POST'])
def getcomplaints():

    #token = request.form['userid']
    # if(token is not none):
    # get from db
    cur = get_db().cursor()
    cur.execute("select * from complaints")
    rows = cur.fetchall()
    if len(rows)>0 :
        rows.insert(0, {'status': 1})
        response = jsonify(rows)
    return response

########################################################################login###############################################
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST' :
        username=request.form['username']
        password=request.form['password']
        h=hashlib.md5(password.encode())
        cur=get_db().cursor()
        cur.execute("SELECT * FROM employees WHERE mobile_no="+username)
        rows=cur.fetchall()
        print(rows)
        if len(rows)>0 :
            if(rows[0]['password'] == h.hexdigest()):
                session['username']=rows[0]['name']
                session['officer_id']=rows[0]['officer_id']
                session['office_id']=rows[0]['office_id']
                session['points']=rows[0]['points']
                session['leaderboar_rank']=rows[0]['leaderboard_rank']    
                return   redirect('/pending')
            else:
                return render_template('login.html', login_status=0)
        else:
            return render_template('login.html', login_status=2)
    else:
        return render_template('login.html')



@app.route('/pending',methods=['GET','POST'])
def pending():
	#session checking
	office_id = 2 # to be set
	cur = get_db().cursor()
	cur.execute("select complaint_id,nearest5 from complaints WHERE owner_id is NULL")
	rows = cur.fetchall()
	if rows is not None:
		complaint_list = []
		for row in rows:
			nearest = row['nearest5']
			ids = nearest.split(",")
			print(ids)
			if str(office_id) in ids:
				complaint_list.append(row['complaint_id'])

		print(complaint_list)
		cur.execute("select * from complaints where complaint_id in "+str((tuple(complaint_list))))
		rows_p = cur.fetchall()
		return jsonify(rows_p)

	return "NO COMPLAINTS" ## to do render_template



if __name__ =='__main__':  
    app.run(debug = True)  

