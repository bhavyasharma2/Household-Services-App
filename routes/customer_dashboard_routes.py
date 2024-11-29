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



@app.route('/customer_home')
def customer_home():
    if 'user' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))
    is_blocked = fetch_one("SELECT is_blocked FROM users WHERE email = ?", (session['user'],))[0]
    return render_template('customer_dashboard.html', is_blocked=is_blocked)




@app.route('/customer_edit_profile', methods=['GET', 'POST'])
def customer_edit_profile():
    email = session.get('user')  

    db = get_db()
    if request.method == 'POST':
        
        new_email = request.form['email']
        new_password = request.form['password']
        new_name = request.form['name']
        new_address = request.form['address']
        new_pin_code = request.form['pin_code']
        new_mobile_number = request.form['mobile_number']

        
        db.execute("""
            UPDATE users
            SET email = ?, password = ?, full_name = ?, address = ?, pin_code = ?, mobile_number = ?
            WHERE email = ?
        """, (new_email, new_password, new_name, new_address, new_pin_code, new_mobile_number, email))
        
        db.commit()
        flash("Profile updated successfully.")
        
        session['user'] = new_email
        return redirect(url_for('customer_home'))

    
    cursor = db.execute("SELECT email, password, full_name, address, pin_code, mobile_number FROM users WHERE email = ?", (email,))
    customer_details = cursor.fetchone()
    cursor.close()

    
    return render_template('customer_edit_profile.html', customer=customer_details)



@app.route('/available_services')
def available_services():
    services = fetch_all("SELECT id, name, description, price, time_required FROM services")
    
    
    service_types = fetch_all("SELECT service_id, id, type_name FROM service_types")

    
    for i, service in enumerate(services):
        service_dict = dict(service)
        
        related_types = [st for st in service_types if st['service_id'] == service['id']]
        service_dict['types'] = related_types
        services[i] = service_dict
    
    return render_template('cust_service_page.html', services=services)



@app.route('/available_professionals/<int:service_id>', methods=['GET'])
def available_professionals(service_id):
    if session['role'] == 'customer':
        
        customer_pincode = session.get('pincode')

        
        service = fetch_one("SELECT id, name FROM services WHERE id = ?", (service_id,))

        
        service_type_id = request.args.get('service_type_id')

        
        print(f"Service ID: {service_id}, Customer Pincode: {customer_pincode}, Service Type ID: {service_type_id}")

        
        if service_type_id:
            
            professionals = fetch_all("""
                SELECT id, full_name, mobile_number, experience, rating 
                FROM users 
                WHERE role = 'professional' 
                AND service_id = ? 
                AND pin_code = ? 
                AND service_type_id = ?
            """, (service_id, customer_pincode, service_type_id))
        else:
            
            professionals = []
        
        
        print(f"Fetched professionals: {professionals}")

        
        no_professionals = len(professionals) == 0

        return render_template('available_professionals.html', professionals=professionals, no_professionals=no_professionals, service=service)
    return render_template('available_professionals.html')




@app.route('/book_service/<int:professional_id>/<int:service_id>', methods=['GET', 'POST'])
def book_service(professional_id, service_id):
    print(f"Professional ID: {professional_id}, Service ID: {service_id}")  

    
    cursor = get_db().execute("""
        SELECT st.id AS service_type_id
        FROM service_types st
        WHERE st.service_id = ? 
    """, (service_id,))
    service_type = cursor.fetchone()

    if not service_type:
        flash("Service type not found.")
        return redirect(url_for('customer_home'))  

    service_type_id = service_type['service_type_id']

    if request.method == 'POST':
        email = session.get('user')
        if not email:
            flash("You need to log in to book a service.")
            return redirect(url_for('login'))  

        cursor = get_db().execute("SELECT id FROM users WHERE email = ?", (email,))
        customer = cursor.fetchone()

        if not customer:
            flash("Customer not found.")
            return redirect(url_for('customer_home'))

        customer_id = customer['id']
        requested_date = request.form.get('date')

        if requested_date:
            cursor = get_db().execute("""
                INSERT INTO service_requests (customer_id, service_id, professional_id, service_type_id, requested_date)
                VALUES (?, ?, ?, ?, ?)
            """, (customer_id, service_id, professional_id, service_type_id, requested_date))
            get_db().commit()
            cursor.close()

            flash("Service booking confirmed!")
            return redirect(url_for('customer_home'))  
        else:
            flash("Please select a date for the service.")
            return redirect(url_for('book_service', professional_id=professional_id, service_id=service_id))

    return render_template('service_request_form.html', professional_id=professional_id, service_id=service_id, service_type_id=service_type_id)



@app.route('/service_request_history')
def service_request_history():
    
    email = session.get('user')  
    cursor1 = get_db().execute("SELECT id FROM users WHERE email = ?", (email,))
    cust_id = cursor1.fetchone()  
    customer_id = int(cust_id['id'])
    db = get_db()
    cursor = db.execute("""
        SELECT sr.id, sr.service_id, u.full_name AS professional_name, 
               s.name AS service_name, st.type_name AS service_type, 
               u.mobile_number, sr.status, sr.requested_date 
        FROM service_requests sr
        JOIN users u ON sr.professional_id = u.id
        JOIN services s ON sr.service_id = s.id
        JOIN service_types st ON sr.service_type_id = st.id  -- Ensure `service_types` and `type_name` exist
        WHERE sr.customer_id = ?
        """, (customer_id,))

    service_requests = cursor.fetchall()
    cursor.close()  
    
    
    return render_template('service_request_history.html', service_requests=service_requests) 



@app.route('/edit_service_request/<int:request_id>', methods=['GET', 'POST'])
def edit_service_request(request_id):
    if request.method == 'POST':
        new_requested_date = request.form['requested_date']
        cursor = get_db()
        cursor.execute("""
            UPDATE service_requests
            SET requested_date = ?
            WHERE id = ?
        """, (new_requested_date, request_id))
        cursor.commit()
        flash("Service request updated successfully.")
        return redirect(url_for('service_request_history'))

    db = get_db()
    cursor= db.execute("""
        SELECT sr.requested_date
        FROM service_requests sr
        WHERE sr.id = ?
    """, (request_id,))
    service_request = cursor.fetchone()

    return render_template('edit_service_request.html', service_request=service_request)



@app.route('/close_service/<int:request_id>', methods=['POST'])
def close_service(request_id):
    
    email = session.get('user')
    if not email:
        return redirect(url_for('login'))

    db = get_db()
    
    
    db.execute('UPDATE service_requests SET status = ?, completion_date = CURRENT_DATE WHERE id = ?', ('Completed', request_id))
    db.commit()
    
    
    return redirect(url_for('service_review_form', request_id=request_id))



@app.route('/service_review_form/<int:request_id>', methods=['GET'])
def service_review_form(request_id):
    db = get_db()
    
    
    service_request = db.execute('''
        SELECT sr.id AS service_request_id,
            s.name AS service_name,
            st.type_name AS service_type_name,
            sr.requested_date,
            sr.completion_date,
            sr.professional_id,
            u.full_name AS professional_name,
            u.mobile_number AS professional_contact
        FROM service_requests sr
        JOIN services s ON sr.service_id = s.id
        LEFT JOIN service_types st ON sr.service_type_id = st.id
        JOIN users u ON sr.professional_id = u.id
        WHERE sr.id = ?
    ''', (request_id,)).fetchone()
    
    return render_template('service_review_form.html', service_request=service_request)



@app.route('/submit_review/<int:request_id>', methods=['POST'])
def submit_review(request_id):
    db = get_db()
    
    
    new_rating = int(request.form['service_rating'])
    
    
    professional = db.execute('SELECT u.id, u.rating FROM users u JOIN service_requests sr ON u.id = sr.professional_id WHERE sr.id = ?', 
                              (request_id,)).fetchone()
    professional_id, current_rating = professional['id'], professional['rating']
    
    
    if current_rating is None:
        average_rating = new_rating
    else:
        average_rating = (current_rating + new_rating) / 2

    
    db.execute('UPDATE users SET rating = ? WHERE id = ?', (average_rating, professional_id))
    db.execute('UPDATE service_requests SET status = ?, completion_date = CURRENT_DATE WHERE id = ?', ('Completed', request_id))
    db.commit()
    
    return redirect(url_for('service_request_history'))



@app.route('/search_results', methods=['GET'])
def search_results():
    query = request.args.get('query', '').strip()
    db = get_db()
    
    
    cursor = db.execute("""
        SELECT s.name AS service_name, st.type_name AS service_type, u.full_name AS professional_name, u.pin_code, u.rating
        FROM services s
        JOIN service_types st ON s.id = st.service_id
        JOIN users u ON u.service_type_id = st.id
        WHERE s.name LIKE ? OR st.type_name LIKE ? OR u.pin_code LIKE ?
    """, (f"%{query}%", f"%{query}%", f"%{query}%"))
    
    results = cursor.fetchall()
    cursor.close()
    
    return render_template('search_results.html', query=query, results=results)




@app.route('/customer_statistics')
def customer_statistics():
    
    email = session.get('user')
    if not email:
        return redirect(url_for('login'))

    db = get_db()

    
    cursor = db.execute('''
        SELECT s.name AS service_name, COUNT(sr.id) AS request_count
        FROM service_requests sr
        JOIN services s ON sr.service_id = s.id
        WHERE sr.customer_id = (SELECT id FROM users WHERE email = ?)
        GROUP BY s.name
    ''', (email,))
    service_requests_by_name = [
        {'service_name': row[0], 'request_count': row[1]} for row in cursor.fetchall()
    ]

    
    cursor = db.execute('''
        SELECT status, COUNT(id) AS status_count
        FROM service_requests
        WHERE customer_id = (SELECT id FROM users WHERE email = ?)
        GROUP BY status
    ''', (email,))
    service_requests_by_status = [
        {'status': row[0], 'status_count': row[1]} for row in cursor.fetchall()
    ]

    return render_template(
        'customer_statistics.html',
        service_requests_by_name=service_requests_by_name,
        service_requests_by_status=service_requests_by_status
    )