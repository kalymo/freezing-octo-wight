import os
import uuid
import psycopg2
import psycopg2.extras
from flask import Flask, session
from flask.ext.socketio import SocketIO, emit

#login
#store messages in database
#load previous messages
#search for term

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'fnejosablgjrlbfiu'
app.debug = True
socketio = SocketIO(app)

messages = [{'text':'test', 'name':'testName'}]
users = {}

def connectToDB():
  connectionString = 'dbname=irc user=postgres password=postgres host=localhost'
  try:
    return psycopg2.connect(connectionString)
  except:
    print("Can't connect to database")


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


    

@socketio.on('message', namespace='/chat')
def new_message(message):
    #tmp = {'text':message, 'name':'testName'}
    if 'username' in session:
        #print("his name is", session['username'])  //Debug code only
        tmp = {'text':message, 'name':users[session['uuid']]['username']}
        messages.append(tmp)
        emit('message', tmp, broadcast=True)
        
        conn = connectToDB() 
        cur=conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = "INSERT INTO messages VALUES(DEFAULT, %s, %s)" 
        cur.execute(query, (message, session['id']))
        conn.commit()
        
        
@socketio.on('search', namespace='/chat')
def search(searchTerm):
    if 'username' in session:
        searchTerm = '%' + searchTerm +'%'
        conn = connectToDB()
        cur=conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = "SELECT text, username FROM messages JOIN users ON messages.user_id = users.id WHERE text LIKE %s OR username LIKE %s"
        cur.execute(query, (searchTerm, searchTerm))
        results = cur.fetchall()
        for result in results:
            result = {'text': result['text'], 'name': result['username']}
            emit('result', result)
    
@socketio.on('identify', namespace='/chat')
def on_identify(message):
    print 'identify' + message
    users[session['uuid']]={'username':message}
    updateRoster()


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
        
        getMessages = "SELECT text, username FROM messages JOIN users ON messages.user_id = users.id"
        cur.execute(getMessages)
        messages = cur.fetchall()
        
        for message in messages:
            message = {'text': message['text'], 'name': message['username']}
            emit('message', message)
        updateRoster()

@socketio.on('disconnect', namespace='/chat')
def on_disconnect():
    print 'disconnect'
    if session['uuid'] in users:
        del users[session['uuid']]
        updateRoster()

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

    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
     