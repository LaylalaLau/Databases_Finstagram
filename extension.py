#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors

import hashlib
#Initialize the app from Flask
from functools import wraps
app = Flask(__name__)
import time
SALT = 'cs3083'


#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec

#Define a route to hello function
@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return render_template("index.html")


#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    hashedPassword = hashlib.sha256(password.encode("utf-8")).hexdigest()
    

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    hashedPassword = hashlib.sha256(password.encode("utf-8")).hexdigest()
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    bio = request.form['bio']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, password, firstName, lastName,bio))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    query =  'SELECT photoID, photoPoster \
             FROM Photo \
             WHERE (allFollowers = True AND photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s AND followstatus = 1)) OR \
                   (allFollowers = False AND photoID IN (SELECT photoID FROM SharedWith WHERE (groupName,groupOwner) IN \
                                                        (SELECT groupName,owner_username FROM BelongTo WHERE member_username = %s))) OR \
             photoPoster = %s \
             ORDER BY postingdate DESC'
    query_friendGroups = 'SELECT groupName FROM Friendgroup WHERE groupOwner = %s'
    cursor.execute(query, (user,user,user))
    photos = cursor.fetchall()
    cursor.execute(query_friendGroups, (user))
    friendGroups = cursor.fetchall()
    
    query = 'CREATE OR REPLACE VIEW visiblePhotos AS  \
                                    SELECT photoID, photoPoster \
                                    FROM Photo \
                                    WHERE (allFollowers = True AND photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s)) OR \
                                          (photoID IN (SELECT photoID FROM SharedWith WHERE (groupName,groupOwner) IN \
                                                                               (SELECT groupName,owner_username FROM BelongTo WHERE member_username = %s))) \
                                    ORDER BY postingdate DESC'
    cursor.execute(query, (user,user))
    query = 'SELECT C.username AS username,C.commenttime AS commenttime,C.text AS text\
             FROM visiblePhotos vP JOIN Comments C USING(photoID)'
    cursor.execute(query)
    cursor.close()
    data2 = cursor.fetchall()
    
    cursor.close()
    return render_template('home.html', username=user, photos=photos,friendGroups = friendGroups,comments=data2)

        
@app.route('/post', methods=["GET", "POST"])
def post():
    username = session['username']
    cursor = conn.cursor();
    filepath = request.form['filepath']
#    photoFile = request.files['photoFile']
#    filepath = photoFile.filename
    visibleTo = request.form['visibleTo']
    allFollowers = 1 if visibleTo == "All Followers" else 0
    caption = request.form['caption']
    query_photo = 'INSERT INTO Photo (photoPoster, filepath, allFollowers,caption) VALUES(%s, %s, %s, %s)'
    cursor.execute(query_photo, (username, filepath, allFollowers,caption))
    if visibleTo != "All Followers":
        photoID = cursor.lastrowid
        query_sharedWith = 'INSERT INTO SharedWith (groupOwner, groupName, photoID) VALUES(%s, %s, %s)'
        cursor.execute(query_sharedWith, (username, visibleTo, photoID))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/follow_search')
def follow_search():
    #check that user is logged in
    username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM Person WHERE username != %s AND username NOT IN (SELECT username_followed FROM Follow WHERE username_follower = %s)'
    cursor.execute(query,(username,username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('follow_search.html', user_list=data)

@app.route('/follow')
def follow():
    person = request.args['person']
    username = session['username']
    cursor = conn.cursor();
    query = 'INSERT INTO Follow (username_followed, username_follower, followstatus) VALUES (%s, %s, %s)'
    cursor.execute(query, (person,username,False))
    conn.commit()
    cursor.close()
    return render_template('request_sent.html')

@app.route('/check_requests')
def check_requests():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT DISTINCT username_follower FROM Follow WHERE username_followed = %s AND followstatus = 0'
    cursor.execute(query,username)
    data = cursor.fetchall()
    cursor.close()
    return render_template('check_requests.html', user_list=data)

@app.route('/handle_request')
def handle_request():
    username = session['username'] 
    decision = request.args['decisions']
    peopleList = request.args.getlist('person')
    
    cursor = conn.cursor()
    if decision == 'Accept':
        query = 'UPDATE Follow SET followstatus = 1 WHERE username_followed = %s AND username_follower = %s'
    else:
        query = 'DELETE FROM Follow WHERE username_followed = %s AND username_follower = %s'
    for person in peopleList:
        cursor.execute(query,(username,person))
    conn.commit()
    cursor.close()
#    check_requests()
    return redirect(url_for('check_requests'))

@app.route('/select_photo')
@login_required
def select_photo():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    user = session['username']
    cursor = conn.cursor();
    query = 'CREATE OR REPLACE VIEW visiblePhotos AS  \
                                    SELECT photoID, photoPoster \
                                    FROM Photo \
                                    WHERE (allFollowers = True AND photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s)) OR \
                                          (photoID IN (SELECT photoID FROM SharedWith WHERE (groupName,groupOwner) IN \
                                                                               (SELECT groupName,owner_username FROM BelongTo WHERE member_username = %s))) \
                                    ORDER BY postingdate DESC'
    cursor.execute(query, (user,user))
    query = 'SELECT *  FROM visiblePhotos'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_photos.html', photo_list=data)
  
@app.route('/comment_photo',methods=['POST'])
@login_required
def comment_photo():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    user = session['username']
    comment = request.form['comment']
    photoID = request.form["photoID"]
    cursor = conn.cursor();
    query = 'INSERT INTO Comments (username,photoID,commenttime,text) VALUES(%s,%s,%s,%s)'
    try:
        cursor.execute(query, (user,photoID,time.strftime('%Y-%m-%d %H:%M:%S'),comment))
        #data = cursor.fetchall()
        cursor.close()
        return ('', 204)
    except:
        error = "Invalid comment or you already commented on the picture."
        return render_template("error.html", error=error)

@app.route('/like_photo',methods=['POST'])
@login_required
def like_photo():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    user = session['username']
    rating = request.form['rating']
    photoID = request.form["photoID"]
    cursor = conn.cursor();
    query = 'INSERT INTO Likes (username,photoID,liketime,rating) VALUES(%s,%s,%s,%s)'
    try:
        cursor.execute(query, (user,photoID,time.strftime('%Y-%m-%d %H:%M:%S'),rating))
        cursor.close()
        return ('', 204)
    except:
        error = "Invalid rating or you already rated the picture."
        return render_template("error.html", error=error)
      
@app.route('/show_photos', methods=["GET", "POST"])
@login_required
def show_photos():
    photo = request.args['photo']
    cursor = conn.cursor();
    query = 'SELECT Ph.photoID,Ph.filepath,Ph.photoPoster,Pe.firstName, Pe.lastName, Ph.postingdate \
             FROM Photo Ph JOIN Person Pe ON Ph.photoPoster = Pe.username \
             WHERE photoID = %s'
    cursor.execute(query, photo)
    data1 = cursor.fetchall()
    query = 'SELECT username, rating FROM Likes WHERE photoID = %s'
    cursor.execute(query, photo)
    data2 = cursor.fetchall()
    cursor.close()
    return render_template('show_photos.html', photos=data1,likes=data2)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)

