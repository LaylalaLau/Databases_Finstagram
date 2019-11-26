#Import Flask Library
from flask import Flask, render_template, request, session, redirect, url_for, send_file
import os
import uuid
import hashlib
import pymysql.cursors
from functools import wraps
import time
SALT = 'cs3083'

#Initialize the app from Flask
app = Flask(__name__)
IMAGES_DIR = os.path.join(os.getcwd(), "images")

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='root',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor,
                       autocommit=True)

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
    #if "username" in session:
        #return redirect(url_for("home"))
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
    #hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()
    
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
    #hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()
    #firstName = request.form["fname"]
    #lastName = request.form["lname"]

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
        ins = 'INSERT INTO Person(username,password) VALUES(%s, %s)'
        cursor.execute(ins, (username, password))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
@login_required
def home():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT photoID, photoPoster \
             FROM Photo \
             WHERE (allFollowers = True AND photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s)) OR \
                   (allFollowers = False AND photoID IN (SELECT photoID FROM SharedWith WHERE (groupName,groupOwner) IN \
                                                        (SELECT groupName,owner_username FROM BelongTo WHERE member_username = %s))) \
             ORDER BY postingdate DESC'
    cursor.execute(query, (user,user))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, photos=data)

        
@app.route('/post', methods=['POST'])
@login_required
def post():
    image_file = request.files.get("photo", "")
    image_name = image_file.filename
    filepath = os.path.join(IMAGES_DIR, image_name)
    image_file.save(filepath)
    username = session['username']
    cursor = conn.cursor();
    # photo = request.form['photo']
    query = 'INSERT INTO Photo (photoID, photoPoster, postingDate) VALUES(%s, %s, datetime.datetime.now())'
    cursor.execute(query, (photo, username))
    query = "INSERT INTO photo (timestamp, filePath) VALUES (%s, %s)"
    cursor.execute(query, (time.strftime('%Y-%m-%d %H:%M:%S'), image_name))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

"""
@app.route("/uploadImage", methods=["POST"])
@login_required
def upload_image():
    if request.files:
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename
        filepath = os.path.join(IMAGES_DIR, image_name)
        image_file.save(filepath)
        query = "INSERT INTO photo (timestamp, filePath) VALUES (%s, %s)"
        with connection.cursor() as cursor:
            cursor.execute(query, (time.strftime('%Y-%m-%d %H:%M:%S'), image_name))
        message = "Image has been successfully uploaded."
        return render_template("upload.html", message=message)
    else:
        message = "Failed to upload image."
        return render_template("upload.html", message=message)
"""

@app.route('/select_photo')
@login_required
def select_photo():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT photoID FROM blog'
    # Fix this later!!!
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_photo.html', photo_list=data)

@app.route('/select_Friendgroup')
@login_required
def select_Friendgroup():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT photoID FROM blog'
    # Fix this later!!!
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', Friendgroup=data)

@app.route('/show_photos', methods=["GET", "POST"])
@login_required
def show_photos():
    photo = request.args['photo']
    cursor = conn.cursor();
    query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    # Fix query!!!
    cursor.execute(query, photo)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_photos.html', photos=data)

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
