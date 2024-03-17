# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
#from flaskext.mysql import MySQL
#from flask_mysql import MySQL
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, Length

from PIL import Image
from datetime import datetime
import qrcode
from flask_qrcode import QRcode as FlaskQRcode
from pyzbar.pyzbar import decode  # Added import for QR code decoding
from io import BytesIO
import os
from flask import flash
from flask import Response
import hashlib
from flask import send_file


app = Flask(__name__, template_folder = 'templates')
app.secret_key = 'your_secret_key'


# MySQL configurations
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'M@hev!$h2003:'
app.config['MYSQL_DB'] = 'python'
#app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql = MySQL()
mysql.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

# Function to check if a user with the same username or email already exists
def registration_exists(full_name, email):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM registration_form WHERE full_name = %s OR email = %s", (full_name, email))
    existing_user = cur.fetchone()
    cur.close()
    return existing_user is not None

# Helper function to create a QR code
def generate_qr_code_registration(id, full_name, email):
    qr = qrcode.QRCode(
	version=1, 
	error_correction=qrcode.constants.ERROR_CORRECT_L, 
	box_size=10, 
	border=4
    )

    # Generate QR code data with registration_id, username, email
    data = f'Registration ID:{id}\nFull Name:{full_name}\nEmail:{email}'

    qr.add_data(data)
    qr.make(fit=True)

    #Generate QR Code Image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code image to BytesIO
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    #img.save(filename)

    #Save QR code image to a file
    folder_path = 'qr_Codes'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, f'candidate_qr_code_REGISTRATION_ID_{id}.png')
    img.save(file_path)

    return img_bytes, file_path

@app.route('/cand-registration', methods=['POST'])
def cand_registration():
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        event_name = request.form.get('event_name')
        photo = request.files['Photo']  # Get the uploaded photo
        toc = request.form.get('toc', 0)  # Checkbox value (1 if checked, 0 if unchecked)

        # Check if the user with the same username or email already exists
        if registration_exists(full_name, email):
            flash("User already exists!!")
            return redirect(url_for('registration'))
        
        # Check if all required fields are present
        if full_name and phone_number and email and event_name and photo:
            # Save the uploaded photo
            if photo.filename != '':
                if photo and allowed_file(photo.filename):
                    filename = secure_filename(photo.filename)
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    photo.save(photo_path)
            else:
                flash('No selected file', 'error')
                return redirect(request.url)
            
            # Create a cursor object to execute queries
            cursor = mysql.connection.cursor()
            
            # Insert data into the database
            cursor.execute(
                "INSERT INTO registration_form (full_name, phone_number, email, photo_path, event_name, accepted_terms_and_conditions) VALUES (%s, %s, %s, %s, %s, %s)",
                    (full_name, phone_number, email, photo_path, event_name, toc))
            
            
            # Commit changes to the database
            mysql.connection.commit()

            # Fetch the registration_id
            id = cursor.lastrowid
            
            # Close cursor
            cursor.close()

            # Generate and store QR code for the user with the registration_id
            img_bytes, file_path = generate_qr_code_registration(id, full_name, email)

            #return send_file(img_bytes, mimetype='image/png', download_name=f'visitor_qr_code_REGISTRATION_ID_{id}.png')

            # Serve the QR code as a file download and also display it
            return Response(
                img_bytes.getvalue(),
                mimetype='image/png',
                headers={'Content-Disposition': f'attachment;filename=candidate_qr_code_REGISTRATION_ID_{id}.png'}
            )

        else:
            # Handle case when required fields are missing
            flash('All fields are required', 'error')
            return redirect(url_for('cand_registration'))

    # Handle case when the request method is not POST
    return redirect(url_for('registration'))

# Define route for the candidate registration form
@app.route('/candidate-registration')
def candidate_registration():
    # Render the candidate registration form template
    return render_template('registration.html')

# Define route to handle redirection from homepage to candidate registration
@app.route('/register-now')
def register_now():
    # Redirect to the candidate registration route
    return redirect(url_for('candidate_registration'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add-user')
def add_user():
    return render_template('add-user.html')

@app.route('/add-event')
def add_event():
    return render_template('add-event.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/submit-sign-in', methods=['POST'])
def submit_sign_in():
    # Get the submitted email and password from the form
    email = request.form.get('email')
    password = request.form.get('password')

    # Check if the email and password match the predefined values
    if email == 'admin@gmail.com' and password == 'admin':
        # Redirect to the dashboard page after successful login
        return redirect(url_for('dashboard'))
    else:
        # If the login credentials are incorrect, redirect back to the sign-in page with a message
        flash('Invalid email or password', 'error')
        return redirect(url_for('candidate_registration', message='Invalid email or password'))
    
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/event_index', methods=['GET', 'POST'])
def event_index():
    return render_template('event_index.html')

@app.route('/events-list')
def events_list():
    return render_template('events-list.html')

# Function to check if a user with the same username or email already exists
def fetch_person_id_from_database(phone_number, event_name):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM registration_form WHERE phone_number=%s AND event_name=%s", (phone_number, event_name))
    id = cur.fetchone()
    cur.close()
    return id[0] if id else None

@app.route('/generate-qr')
def generate_qr():
    return render_template('generate-qr.html')

@app.route('/qr-generation', methods=['POST'])
def qr_generation():
# Get phone number and event name from form submission
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        event_name = request.form.get('event_name')

        # Fetch person's details from the database based on phone number and event name
        id = fetch_person_id_from_database(phone_number, event_name)

        if id:
            # Assuming the QR code filename is the person's ID followed by '.png'
            qr_code_filename = f"candidate_qr_code_REGISTRATION_ID_{id}.png"
            qr_code_path = os.path.join('qr_Codes', qr_code_filename)

            if os.path.exists(qr_code_path):
                # If the QR code file exists, serve it directly
                return send_file(qr_code_path, mimetype='image/png')
            else:
                # Handle case where QR code file is not found
                return "QR code not found"
        else:
            # Handle case where person is not found in the database
            return "Person not found"
    else:
        return redirect(url_for('generate-qr'))

@app.route('/generate-qr@')
def generate_qr1():
    return render_template('generate-qr@.html')

@app.route('/payments-list')
def payments_list():
    return render_template('payments-list.html')

@app.route('/registration')
def registration():
    return render_template('registration.html')

@app.route('/users-list')
def users_list():
    return render_template('users-list.html')

@app.route('/success-page')
def success_page():
    return render_template('success_page.html')

# Function to check if a user with the same username or email already exists
def visitor_exists(full_name, email):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM visitors WHERE full_name = %s OR email = %s", (full_name, email))
    existing_user = cur.fetchone()
    cur.close()
    return existing_user is not None

# Helper function to create a QR code
def generate_qr_code_visitor(id, full_name, email):
    qr = qrcode.QRCode(
	version=1, 
	error_correction=qrcode.constants.ERROR_CORRECT_L, 
	box_size=10, 
	border=4
    )

    # Generate QR code data with registration_id, username, email
    data = f'Registration ID:{id}\nFull Name:{full_name}\nEmail:{email}'

    qr.add_data(data)
    qr.make(fit=True)

    #Generate QR Code Image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code image to BytesIO
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    #img.save(filename)

    #Save QR code image to a file
    folder_path = 'qr_Codes'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, f'visitor_qr_code_REGISTRATION_ID_{id}.png')
    img.save(file_path)

    return img_bytes, file_path

from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/visitor-registration', methods=['POST'])
def visitor_registration():
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        event_name = request.form.get('event_name')
        photo = request.files['Photo']  # Get the uploaded photo
        toc = request.form.get('toc', 0)  # Checkbox value (1 if checked, 0 if unchecked)

        # Check if the user with the same username or email already exists
        if visitor_exists(full_name, email):
            flash("User already exists!!")
            return redirect(url_for('visitor'))
        
        # Check if the user with the same username or email already exists in candidate_registration
        if registration_exists(full_name, email):
            flash("User already exists!!")
            return redirect(url_for('visitor'))
        
        # Check if all required fields are present
        if full_name and phone_number and email and event_name and photo:
            # Save the uploaded photo
            if photo.filename != '':
                if photo and allowed_file(photo.filename):
                    filename = secure_filename(photo.filename)
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    photo.save(photo_path)
            else:
                flash('No selected file', 'error')
                return redirect(request.url)
            
            # Create a cursor object to execute queries
            cursor = mysql.connection.cursor()
            
            # Insert data into the database
            cursor.execute(
                "INSERT INTO visitors (full_name, phone_number, email, photo_path, event_name, accepted_terms_and_conditions) VALUES (%s, %s, %s, %s, %s, %s)",
                    (full_name, phone_number, email, photo_path, event_name, toc))
            
            
            # Commit changes to the database
            mysql.connection.commit()

            # Fetch the registration_id
            id = cursor.lastrowid
            
            # Close cursor
            cursor.close()

            # Generate and store QR code for the user with the registration_id
            img_bytes, file_path = generate_qr_code_visitor(id, full_name, email)

            #return send_file(img_bytes, mimetype='image/png', download_name=f'visitor_qr_code_REGISTRATION_ID_{id}.png')

            # Serve the QR code as a file download and also display it
            return Response(
                img_bytes.getvalue(),
                mimetype='image/png',
                headers={'Content-Disposition': f'attachment;filename=visitor_qr_code_REGISTRATION_ID_{id}.png'}
            )

            """# Serve the QR code as a file download and also display it
            return send_file(
                BytesIO(img_bytes.getvalue()),
                mimetype='image/png',
                as_attachment=True,
                attachment_filename=f'visitor_qr_code_REGISTRATION_ID_{id}.png'
            )"""
            
            # Redirect to a success page or any other page as needed
            #return redirect(url_for('success_page'))
        else:
            # Handle case when required fields are missing
            flash('All fields are required', 'error')
            return redirect(url_for('visitor_registration'))

    # Handle case when the request method is not POST
    return redirect(url_for('visitor'))

@app.route('/visitor')
def visitor():
    return render_template('visitor.html')

@app.route('/visitor@')
def visitor1():
    return render_template('visitor@.html')

if __name__ == '__main__':
    #db.create_all()
    app.run(debug=True, use_reloader=False)
