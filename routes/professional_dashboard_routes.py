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




@app.route('/professional_home')
def professional_home():
    is_blocked = fetch_one("SELECT is_blocked FROM users WHERE email = ?", (session['user'],))[0]
    return render_template('professional_dashboard.html', is_blocked=is_blocked)




@app.route('/prof_search', methods=['GET'])
def prof_search():
    
    email = session.get('user')
    if not email or session.get('role') != 'professional':
        return redirect(url_for('login'))

    
    query = request.args.get('query')
    db = get_db()

    
    cursor = db.cursor()
    cursor.execute('''
        SELECT sr.id, u.full_name AS customer_name, sr.requested_date, sr.status
        FROM service_requests sr
        JOIN users u ON sr.customer_id = u.id
        WHERE sr.professional_id = (
            SELECT id FROM users WHERE email = ?
        )
        AND (u.full_name LIKE ? OR sr.requested_date LIKE ? OR u.pin_code LIKE ?)
    ''', (email, f'%{query}%', f'%{query}%', f'%{query}%'))
    search_results = cursor.fetchall()

    return render_template('prof_search_results.html', results=search_results)




@app.route('/prof_edit_profile', methods=['GET', 'POST'])
def prof_edit_profile():
    email = session.get('user')  
    db = get_db()
    
    
    cursor = db.execute('SELECT * FROM users WHERE email = ?', (email,))
    professional = cursor.fetchone()

    if request.method == 'POST':
        
        full_name = request.form['full_name']
        password = request.form['password']
        experience = request.form['experience']
        address = request.form['address']
        pin_code = request.form['pin_code']
        mobile_number = request.form['mobile_number']
        documents = request.files['documents']  

        
        if documents:
            
            documents_path = f"uploads/{documents.filename}"
            documents.save(documents_path)
        else:
            
            documents_path = professional['documents_path']

        
        db.execute("""
            UPDATE users
            SET full_name = ?, password = ?, experience = ?, address = ?, pin_code = ?, mobile_number = ?, documents_path = ?
            WHERE email = ?
        """, (full_name, password, experience, address, pin_code, mobile_number, documents_path, email))
        
        db.commit()

        
        return redirect(url_for('professional_home'))  

    return render_template('prof_edit_profile.html', professional=professional)




@app.route('/prof_service_requests')
def prof_service_requests():
    email = session.get('user')  
    db = get_db()
    
    
    prof_id_tuple = fetch_one('SELECT id FROM users WHERE email = ?', (email,))
    is_blocked = fetch_one("SELECT is_blocked FROM users WHERE email = ?", (session['user'],))[0]
    
    
    if prof_id_tuple is None:
        return redirect(url_for('login'))  
    
    
    prof_id = prof_id_tuple[0]
    
    
    pending_requests = db.execute('''SELECT sr.id, u.full_name, u.mobile_number, u.address, u.pin_code, sr.requested_date 
                                  FROM service_requests sr
                                  JOIN users u ON sr.customer_id = u.id
                                  WHERE sr.professional_id = ? AND sr.status = 'Pending' ''', 
                                  (prof_id,)).fetchall()
    
    
    assigned_rejected_requests = db.execute('''SELECT sr.id, u.full_name, u.mobile_number, u.address, u.pin_code, sr.requested_date,  sr.status
                                            FROM service_requests sr
                                            JOIN users u ON sr.customer_id = u.id
                                            WHERE sr.professional_id = ? AND sr.status IN ('Assigned', 'Rejected')''', 
                                            (prof_id,)).fetchall()

    
    closed_requests = db.execute('''SELECT sr.id, u.full_name, u.mobile_number, u.address, u.pin_code, sr.requested_date, sr.status, sr.completion_date
                                FROM service_requests sr
                                    JOIN users u ON sr.customer_id = u.id
                                    WHERE sr.professional_id = ? AND sr.status = 'Completed' ''', 
                                    (prof_id,)).fetchall()

    return render_template('prof_service_requests.html', 
                           pending_requests=pending_requests, 
                           assigned_rejected_requests=assigned_rejected_requests,
                           closed_requests=closed_requests,
                           is_blocked=is_blocked)




@app.route('/accept_request/<int:request_id>', methods=['GET'])
def accept_request(request_id):
    email = session.get('user')  
    db = get_db()
    
    
    prof_id_tuple = fetch_one('SELECT id FROM users WHERE email = ?', (email,))
    
    
    if prof_id_tuple is None:
        return redirect(url_for('login'))  
    
    
    prof_id = prof_id_tuple[0]

    db.execute('''UPDATE service_requests
                  SET status = 'Assigned'
                  WHERE id = ? AND professional_id = ?''', 
               (request_id, prof_id))
    
    
    db.commit()

    return redirect(url_for('prof_service_requests'))



@app.route('/reject_request/<int:request_id>', methods=['GET'])
def reject_request(request_id):
    email = session.get('user')  
    db = get_db()
    
    
    prof_id_tuple = fetch_one('SELECT id FROM users WHERE email = ?', (email,))
    
    
    if prof_id_tuple is None:
        return redirect(url_for('login'))  
    
    
    prof_id = prof_id_tuple[0]

    db.execute('''UPDATE service_requests
                  SET status = 'Rejected'
                  WHERE id = ? AND professional_id = ?''', 
               (request_id, prof_id))
    
    db.commit()

    return redirect(url_for('prof_service_requests'))




@app.route('/professional_statistics')
def professional_statistics():
    email = session.get('user')
    conn = get_db()
    cursor = conn.cursor()

    
    cursor.execute('''
        SELECT rating 
        FROM users
        WHERE email = ? AND role = 'professional'
    ''', (email,))
    
    
    rating_result = cursor.fetchone()
    professional_rating = rating_result['rating'] if rating_result else 'No rating available'

    
    cursor.execute('''
        SELECT status, COUNT(*) AS count
        FROM service_requests
        WHERE professional_id = (
            SELECT id FROM users WHERE email = ? AND role = 'professional'
        )
        GROUP BY status
    ''', (email,))
    
    
    service_requests_by_status = [
        {'status': row[0], 'count': row[1]} for row in cursor.fetchall()
    ]

    return render_template(
        'professional_statistics.html',
        professional_rating=professional_rating,
        service_requests_by_status=service_requests_by_status
    )
