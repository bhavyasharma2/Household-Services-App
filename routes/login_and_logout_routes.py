from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify, send_from_directory
from app import app
import sqlite3
import os
from db_utils import execute_query, fetch_all, fetch_one
from werkzeug.utils import secure_filename
from flask import render_template
from collections import defaultdict


DATABASE = 'household_services.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE) 
        g.db.row_factory = sqlite3.Row  
        
    return g.db



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()

        if user:
            
            session['user'] = user['email']  
            session['role'] = user['role']  
            session['pincode'] = user['pin_code']  

            
            if user[3] == 'admin':
                return redirect(url_for('admin_home'))
            elif user[3].lower() == 'professional':
                return redirect(url_for('professional_home'))
            elif user[3] == 'customer':
                return redirect(url_for('customer_home'))
        else:
            flash('Invalid email or password. Try Again.', 'danger')
            return redirect(url_for('login'))

    else:
        return render_template('login.html')
    



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))