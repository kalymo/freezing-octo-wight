import os
import uuid
import psycopg2
import psycopg2.extras
from flask import Flask, session
from flask.ext.socketio import join_room, leave_room
from flask.ext.socketio import SocketIO, emit

#create a room
#store room info in database
#load previous messages from specific room
#search for term in a specific room

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'fnejosablgjrlbfiu'
app.debug = True
socketio = SocketIO(app)

messages = [{'text':'test', 'name':'testName'}]
users = {}
rooms = []

def connectToDB():
  connectionString = 'dbname=irc user=postgres password=postgres host=localhost'
  try:
    return psycopg2.connect(connectionString)
  except:
    print("Can't connect to database")


# fetch rooms from the database once :)
con = connectToDB()
cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
room_query = "SELECT id, name FROM rooms"
cur.execute(room_query)
results = cur.fetchall()
for result in results:
    result = {'name': result['name'], 'id': result['id']}
    rooms.append(result)
    print(result)


def updateRoster():
    names = []
    for user_id in  users:
        print users[user_id]['username']
        if len(users[user_id]['username'])==0:
            names.append('Anonymous')
        else:
            names.append(users[user_id]['username'])
    print 'broadcasting names'
    emit('roster', names, broadcast=True)
    

@socketio.on('connect', namespace='/chat')
def test_connect():
    session['uuid']=uuid.uuid1()
    #session['username']='starter name' //comment out to stop non-users from posting
    print 'connected'
    
    users[session['uuid']]={'username':'New User'}
    updateRoster()

def updateRooms():
    emit('rooms', rooms)



@socketio.on('join', namespace="/chat")
def on_join(data):
    username = data['username']
    room = data['room']['id']
    print("joining: " , room)
    join_room(str(room))
    con = connectToDB()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
    messages_query = "SELECT username, text FROM messages JOIN users on messages.user_id = users.id WHERE room_id = %s order by messages.id "
    cur.execute(messages_query, (room,))
    results = cur.fetchall()
    for result in results:
        result = {'name' : result['username'], 'text' : result['text'], 'room' : data['room']['name']}
        emit('message', result)
    print(username + ' has entered the room.')

@socketio.on('leave', namespace="/chat")
def on_leave(data):
    username = data['username']
    room = data['room']['id']
    print("leaving: " , room)
    leave_room(str(room))
    print(username + ' has left the room.')    


@socketio.on('message', namespace='/chat')
def new_message(message):
    #tmp = {'text':message, 'name':'testName'}
    if 'username' in session:
        #print("his name is", session['username'])  //Debug code only
        tmp = {'text':message['text'], 'room':message['room']['name'],  'name':users[session['uuid']]['username']}
        messages.append(tmp)
        emit('message', tmp, room=str(message['room']['id']))
        
        conn = connectToDB() 
        print('message-text: ' , message['text'])
        print('session-id: ' , session['id'])
        cur=conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = "INSERT INTO messages VALUES(DEFAULT, %s, %s, %s)" 
        cur.execute(query, (message['text'], session['id'], message['room']['id']))
        conn.commit()
        
        
@socketio.on('search', namespace='/chat')
def search(searchTerm):
    if 'username' in session:
        room_id = searchTerm['room']['id']
        searchTerm = '%' + searchTerm['searchTerm'] +'%'
        conn = connectToDB()
        cur=conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = "SELECT text, username FROM messages JOIN users ON messages.user_id = users.id WHERE (text LIKE %s OR username LIKE %s) AND room_id = %s"
        cur.execute(query, (searchTerm, searchTerm, room_id))
        results = cur.fetchall()
        for result in results:
            result = {'text': result['text'], 'name': result['username']}
            emit('result', result)
    
@socketio.on('identify', namespace='/chat')
def on_identify(message):
    if 'uuid' in session:
        users[session['uuid']]={'username':message}
        updateRoster()
    else:
        print 'sending information'
        session['uuid']=uuid.uuid1()
        session['username']='starter name'
  
        updateRoster()
        updateRooms()

        for message in messages:
            emit('message', message)


@socketio.on('login', namespace='/chat')
def on_login(datainfo):
    print 'login '
    username = datainfo['username']
    password = datainfo['password']
    conn = connectToDB()
    cur=conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "select * from users WHERE username = %s AND password = %s" 
    cur.execute(query, (username, password))
    result = cur.fetchone()
    if result:
        users[session['uuid']]={'username': datainfo['username']}
        session['username']=datainfo['username']
        session['id']=result['id']
        updateRooms()
        # getMessages = "SELECT text, username, rooms.name FROM messages JOIN users ON messages.user_id = users.id JOIN rooms ON room_id = rooms.id WHERE room_id = 1"
        # cur.execute(getMessages)
        # messages = cur.fetchall()
        
        # for message in messages:
        #     message = {'text': message['text'], 'name': message['username'], 'room': message['name']}
        #     emit('message', message)
        # updateRoster()

@socketio.on('disconnect', namespace='/chat')
def on_disconnect():
    print 'disconnect'
    if session['uuid'] in users:
        del users[session['uuid']]
        updateRoster()
        
# @app.route('/new_room', methods=['POST'])
@socketio.on('new_room', namespace='/chat')
def new_room(data):
    
    con = connectToDB()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
    add_room_query = "INSERT INTO rooms VALUES (default, %s) RETURNING id"
    cur.execute(add_room_query, (data['name'],))
    the_id = cur.fetchone()['id']
    con.commit()
    
    rooms.append({'name':data['name'], 'id':the_id})
    print 'updating rooms'
    updateRooms()
    print 'back'

    # return jsonify(success= "ok")

@app.route('/')
def hello_world():
    print 'in hello world'
    return app.send_static_file('index.html')
    return 'Hello World!'

@app.route('/js/<path:path>')
def static_proxy_js(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('js', path))
    
@app.route('/css/<path:path>')
def static_proxy_css(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('css', path))
    
@app.route('/img/<path:path>')
def static_proxy_img(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('img', path))
    
if __name__ == '__main__':
    print "A"
    # when we start the program, we should load all the rooms from the database ONCE
   
    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
     