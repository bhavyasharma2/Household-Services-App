from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify, send_from_directory
from app import app
import sqlite3
import os
from db_utils import execute_query, fetch_all, fetch_one
from werkzeug.utils import secure_filename
from flask import render_template
from collections import defaultdict
import re


DATABASE = 'household_services.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE) 
        g.db.row_factory = sqlite3.Row  
        
    return g.db



UPLOAD_FOLDER = 'static/uploads/documents'  
ALLOWED_EXTENSIONS = {'pdf'}


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/register_professional', methods=['GET', 'POST'])
def register_professional():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        service_id = request.form['service_id']
        service_type_id = request.form['service_type']  
        experience = request.form['experience']
        address = request.form['address']
        pin_code = request.form['pin_code']
        mobile_number = request.form['mobile_number']
        
        
        db = get_db()
        cursor = db.cursor()

        
        documents_path = request.files.get('documents_path')
        file_path = None  

        if documents_path and allowed_file(documents_path.filename):
            filename = secure_filename(documents_path.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            documents_path.save(file_path)  

        
        cursor.execute('''
            INSERT INTO pending_registrations (email, password, full_name, address, pin_code, mobile_number, experience, documents_path, service_id, service_type_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (email, password, full_name, address, pin_code, mobile_number, experience, file_path, service_id, service_type_id))
        db.commit()
        
        
        flash("Registration request has been sent to the admin. Please wait until the admin accepts your registration.", "info")
        return redirect(url_for('login'))
        

    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM services')
    services = cursor.fetchall()

    return render_template('register_service_professional.html', services=services)



@app.route('/get_service_types/<int:service_id>')
def get_service_types(service_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, type_name FROM service_types WHERE service_id = ?', (service_id,))
    types = cursor.fetchall()
    return jsonify({'types': [{'id': t[0], 'type_name': t[1]} for t in types]})



@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        address = request.form['address']
        pin_code = request.form['pin_code']
        mobile_number = request.form['mobile_number']

        if not (8 <= len(password) and re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and re.search(r"[!@#$%^&*({[?/<>\|})]", password)):
            flash("Password should have atleast one uppercase, one lowercase, one special character. Please change your password.", "danger")
            return redirect(url_for('login'))
        
        else:

         db = get_db()
         cursor = db.cursor()

         try:
            
             cursor.execute('''
                 INSERT INTO users (email, password, role, full_name, address, pin_code, mobile_number, rating, documents_path, is_blocked) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
             ''', (email, password, 'customer', full_name, address, pin_code, mobile_number, 0, None, 0))
             db.commit()

            
             return redirect(url_for('customer_home'))
         except sqlite3.IntegrityError:
             flash('Email ID already registered. Please use a different email.', 'danger')
             return redirect(url_for('register_customer'))
    

    return render_template('register_customer.html')