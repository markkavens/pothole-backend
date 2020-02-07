from flask import *
import sqlite3
import requests
import hashlib
import math
import datetime, time
from operator import itemgetter 

import base64

import os
app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = '/home/siram/Downloads/pothole-backend/pothole/potholedb.db'

def session_checking():
    if(session == {}):
        return False
    else:
        return True
    
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = make_dicts  # make dictionary of rows
    return db

### to be checked..
def distance(lat1, lat2, lon1, lon2):
    r = 6378100
    print(type(lat1))
    lat1=lat1*(math.pi/180)
    lat2=lat2*(math.pi/180)
    lon1=lon1*(math.pi/180)
    lon2=lon2*(math.pi/180)
    val=math.sqrt((math.sin((lat2-lat1)/2) )**2 + math.cos(lat1)*math.cos(lat2)*(math.sin((lon2-lon1)/2) )**2 )
    d=2*r*math.asin(val)
    
    return d


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
    return redirect('/login')


#@app.route('/register')
# def registerUser():
#     cur = get_db().cursor()
#     cur.execute('''INSERT into complaints (complaint_category,complaint_latitude,
#                     complaint_longitude,image_name) VALUES
# 				    (:cat,:lat,:long,:img)''',
#                 {"cat": '', "lat": latitude,
#                     "long": longitude, "img": image_name
#                  }
#                 )


@app.route('/admin-interface')
def adminInterface():
    print(session)
    return render_template('admin.html', username = "NIKHIL" ) #session['username'] should be changed to this

@app.route("/api-test",methods=["POST","GET"])
def apitest():
    if request.method == "POST":
        print(request.get_json())
        return 'Hello'

@app.route('/post-complaints', methods=['POST'])
def postcomplaints():
    #token = request.form['userid']
    # if(token is not none):
    # values from app_interface
    data = request.get_json()  # get json from them
    category = data['category']
    latitude = float(data['latitude'])
    longitude = float(data['longitude'])
    reg_time =  datetime.datetime.now()
    image_name = str(reg_time).replace(" ","")
    
    imgdata = base64.b64decode(data['base64img'])
    filename = "./static/uploaded/"+ image_name + '.jpeg'  
    # filename = "uploaded/hiya"
    image_name+='.jpeg'
    #f = open(filename, "wb")
    #f.close()
    
    with open(filename, 'wb+') as f:
        f.write(imgdata)
    f.close()
    print(latitude, longitude)
    
    
    # if 'image' in request.files:
    # # print("Files are: " , len(request.files))
    #     img = request.files['image']
    #     img.save("uploaded/pothole.jpeg")

    #address = data['address']
    #landmark = data['landmark']
    # duplication checking
    cur = get_db().cursor()
    '''
    cur.execute("select complaint_id,complaint_latitude,complaint_longitude from complaints")
    rows = cur.fetchall()
    limit = 5
    if rows is not []:
        for row in rows:
            lat2 = row['complaint_latitude']
            lon2 = row['complaint_longitude']
            print(lat2, lon2)
            d = distance(latitude, lat2, longitude, lon2)
            print(d)
            if d <= limit:
                cur.execute("UPDATE complaints SET upvotes=upvotes+1 where complaint_id="+ str(row['complaint_id']))
                get_db().commit()
                return "status duplicate"
    '''
    # nearest 5 findings
    nearest = {}
    nearestlist = []
    cur.execute("select * from offices")
    rows_offices = cur.fetchall()
    for row_office in rows_offices:
        lat_o = row_office['office_latitude']
        lon_o = row_office['office_longitude']
        d = distance(latitude, lat_o, longitude, lon_o)
        nearest[row_office['office_id']] = d
    sorted_d = sorted((value, key) for (key, value) in nearest.items())
    print(sorted_d)
    i = 0
    while i < len(sorted_d) and i < 5:
        nearestlist.append(str(sorted_d[i][1]))
        i+=1
    nearest5 = ",".join(nearestlist)
    print(nearest5)

    # getting traffic level of complaint point
    api_key = "jqaiP21S534IESqdD667p0Aiheea7gpt"
    # Just testing out
    URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point=" + \
        str(latitude)+"%2C"+str(longitude)+"&key="+api_key
    r = requests.get(url=URL)
    traffic_data = r.json()
    if traffic_data is not {} and 'httpStatusCode' not in traffic_data:
        free_flow_speed = traffic_data['flowSegmentData']['freeFlowSpeed']
        current_speed = traffic_data['flowSegmentData']['currentSpeed']
        free_flow_travel_time = traffic_data['flowSegmentData']['freeFlowTravelTime']
        current_travel_time = traffic_data['flowSegmentData']['currentTravelTime']
        traffic_value = free_flow_speed-current_speed+(free_flow_travel_time-current_travel_time)/free_flow_travel_time 
        print(traffic_value)
    else:
        traffic_value = 0
    
    # database posting
    cur.execute('''INSERT into complaints (complaint_category,complaint_latitude,complaint_longitude,
                    image_name,traffic_value,registration_time,nearest5) VALUES(:cat,:lat,:long,:img,:tv,:rtime,:near)''',
                    {"cat": category, "lat": latitude, "long": longitude, "img": image_name,"tv":traffic_value,"rtime":reg_time,"near":nearest5})
    get_db().commit()
    for row in cur.execute('SELECT * FROM complaints'):
        print(row)
    
    return jsonify({"status":1})


@app.route('/get-complaints', methods=['GET', 'POST'])
def getcomplaints():
    #token = request.args['userid']
    # if(token is not none):
    # get from db
    cur = get_db().cursor()
    cur.execute("select * from complaints")
    rows = cur.fetchall()
    if len(rows) > 0:
        for row in rows:
            if row['image_name'] is not None:
                row['img_url'] = request.url_root + "uploaded/"+row['image_name']
        rows.insert(0, {'status': 1})
        response = jsonify(rows)
    else:
        response = { "status":0 }
    return response


########################### office side #################################

@app.route('/login', methods=['GET', 'POST'])
def login():
    if(session is not {}):
        redirect(url_for('pending'))
    if request.method == 'POST':
        username = request.form['username']
        print(username)
        password = request.form['password']
        h = hashlib.md5(password.encode())
        cur = get_db().cursor()
        cur.execute("SELECT * FROM employees WHERE mobile_no="+str(username))
        rows = cur.fetchall()
        print(rows)
        if len(rows) > 0:
            if(rows[0]['password'] == h.hexdigest()):
                session['username'] = rows[0]['officer_name']
                session['officer_id'] = rows[0]['officer_id']
                session['office_id'] = rows[0]['office_id']
                session['points'] = rows[0]['points']
                session['leaderboar_rank'] = rows[0]['leaderboard_rank']
                return redirect('/pending')
            else:
                return render_template('login.html', login_status=0)
        else:
            return render_template('login.html', login_status=2)
    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    for i in range(len(session)):
        session.pop()

    return redirect('/')



@app.route('/pending', methods=['GET', 'POST'])
def pending():
    #session checking ..commented for test
    '''if session  == {}:
        return redirect(url_for('login'))
    office_id = session['office_id'] '''
    office_id = 1 ## just for testing
    cur = get_db().cursor()
    cur.execute(
        "select complaint_id,nearest5 from complaints WHERE office_assigned is NULL")
    rows = cur.fetchall()
    if len(rows) > 0:
        complaint_list = []
        for row in rows:
            if row['nearest5'] is None:
                continue
            nearest = row['nearest5']
            ids = nearest.split(",")
            print(ids)
            if str(office_id) in ids:
                complaint_list.append(row['complaint_id'])

        print("complaint_list",complaint_list)
        if(len(complaint_list)>1):
            cur.execute("select * from complaints where complaint_id in "+ str(tuple(complaint_list))     )
        else:
            cur.execute("select * from complaints where complaint_id= "+ str(complaint_list[0])    )
        rows_p = cur.fetchall()
        return render_template('admin.html',isPending = True,data=rows_p)

    return "NO COMPLAINTS"  # to do render_template



@app.route('/owned', methods=['GET', 'POST'])
def owned():
        # session checking
    # if(len(session) == 0):
    #     return redirect(url_for('login'))
    # office_id = session['office_id']
    # print(office_id)
    office_id = 1
    cur = get_db().cursor()
    cur.execute("select * from complaints WHERE office_assigned = "+str(office_id) + " AND is_solved is NULL order by traffic_value desc,upvotes desc" ) 
    rows = cur.fetchall()
    if(len(rows) > 0):
        return render_template("admin.html", isPending=False , data = rows)

    return "NO COMPLAINTS" ## to do render_template

###################################################### accept #########################################

@app.route('/accept/<complaint_id>')
def accept(complaint_id):
    
    office_assigned=1   #session['office_id'] todo: change it back
    office_assigned=1
    accept_time = datetime.datetime.now()
    # expected_time=10000 to be calculated
    cur=get_db().cursor()
    cur.execute('''UPDATE complaints SET office_assigned = :office_assigned ,accept_time = :accept_time
                                      WHERE complaint_id = :complaint_id ''',
                    {"office_assigned": office_assigned, "accept_time": accept_time,"complaint_id":complaint_id})
    
    get_db().commit()
    
    return redirect(url_for('pending'))

@app.route('/reject/<complaint_id>')
def reject(complaint_id):
    office_id=1    #session['office_id']   todo: change it back
    cur=get_db().cursor()
    cur.execute("SELECT nearest5 FROM complaints WHERE complaint_id= ?", complaint_id)
    rows=cur.fetchall()
    if(len(rows)>0):
        nearest5=rows[0]['nearest5']
        nearest5=nearest5.split(',')
        print("office_id: ",str(office_id))
        if( str(office_id) in nearest5 ):
            nearest5.remove(str(office_id))
        print(nearest5)
        nearest5 = ",".join(nearest5)
    
    cur.execute('UPDATE complaints SET nearest5= :nearest5 WHERE complaint_id= :complaint_id',
                {"nearest5":nearest5,"complaint_id":complaint_id})
    get_db().commit()
    
    return redirect(url_for('pending'))

@app.route('/resolve/<complaint_id>')
def resolve(complaint_id):
    
    solver_id= 1 #session['officer_id'] todo: change it back
    solved_time=datetime.datetime.now()
    is_solved=1
    
    cur=get_db().cursor()
    
    cur.execute('UPDATE complaints  SET solver_id= :solver_id,solved_time= :solved_time,is_solved= :is_solved WHERE complaint_id= :complaint_id'
                ,{'solver_id':solver_id,'solved_time':solved_time,'is_solved':is_solved,'complaint_id':complaint_id})
    
    get_db().commit()
    
    return redirect(url_for('owned'))  

################################################################ statistics ####################################################

@app.route('/get_stats')  
def get_stats():
    office_id=1 #session['office_id'] todo: to change this
    
    cur=get_db().cursor()
    cur.execute('SELECT * FROM complaints WHERE office_assigned= 1 and is_solved is NULL')
    rows_unsolved=cur.fetchall()
    unsolved_complaints=len(rows_unsolved)
    cur.execute('SELECT * FROM complaints WHERE office_assigned= 1 and is_solved is 1')
    rows_solved=cur.fetchall()
    total_complaints=len(rows_solved)+len(rows_unsolved)
    solved_complaints=len(rows_solved)
    unsolved_complaints=len(rows_unsolved)
    rows_solved=sorted(rows_solved,key=itemgetter('complaint_id'))
    #todo: ETS
    # ETS=0
    # nof_comp_for_ets=5
    # for i in  range(nof_comp_for_ets):
    #     ETS+=rows[i]['solved_time']-rows[i]['registration_time']
    # ETS/=nof_comp_for_ets
    # if(total_complaints>0):
            
    employee_solved={}
    for i in range(len(rows_solved)):
        if(rows_solved[i]['solver_id'] in employee_solved.keys()):
            employee_solved[rows_solved[i]['solver_id']]+=1 
        else:
            employee_solved[rows_solved[i]['solver_id']]=1
    final_stats={}
    final_stats['total_complaints']=total_complaints
    final_stats['solved_complaints']=solved_complaints
    final_stats['unsolved_complaints']=unsolved_complaints
    final_stats['employee_solved']=employee_solved
    print("final",final_stats)  
                
    return jsonify(final_stats)

@app.route('/stats')
def stats():
    # if(session_checking()):
        return render_template('statistics.html')
     
    
    
    
        
        
if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port = 5500)
