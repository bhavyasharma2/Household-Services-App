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



@app.route('/admin_home')
def admin_home():
    return render_template('admin_dashboard.html')



@app.route('/new_registration_requests')
def new_registration_requests():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
    SELECT id AS request_id, full_name, email, service_id, service_type_id, pin_code, documents_path
    FROM pending_registrations
    ''')
    registration_requests = cursor.fetchall()
    print(registration_requests)  

    db.close()

    return render_template('admin_registration_requests.html', registration_requests=registration_requests)



@app.route('/approve_registration/<int:request_id>', methods=['POST'])
def approve_registration(request_id):
    db = get_db()
    cursor = db.cursor()

    
    cursor.execute('SELECT * FROM pending_registrations WHERE id = ?', (request_id,))
    registration = cursor.fetchone()

    if registration:
        
        cursor.execute('''
            INSERT INTO users (email, password, role, full_name, address, pin_code, mobile_number, experience, documents_path, service_id, service_type_id, is_blocked)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (registration['email'], registration['password'], 'professional', registration['full_name'],
              registration['address'], registration['pin_code'], registration['mobile_number'],
              registration['experience'], registration['documents_path'], registration['service_id'],
              registration['service_type_id'], 0))
        db.commit()

        
        cursor.execute('DELETE FROM pending_registrations WHERE id = ?', (request_id,))
        db.commit()

        flash("Registration approved successfully.", "success")
    return redirect(url_for('new_registration_requests'))


@app.route('/reject_registration/<int:request_id>', methods=['POST'])
def reject_registration(request_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM pending_registrations WHERE id = ?', (request_id,))
    db.commit()
    flash("Registration request rejected.", "danger")
    return redirect(url_for('new_registration_requests'))




@app.route('/view_document/<path:document_path>')
def view_document(document_path):
    
    full_path = os.path.join(app.root_path, document_path)
    if os.path.exists(full_path):
        return render_template('view_document.html', document_url=url_for('static', filename=document_path[len('static/'):]))
    else:
        flash("Document not found.", "danger")
        return redirect(url_for('professional_details'))
    


@app.route('/admin/professionals/search')
def search_professional_by_name():
    query = request.args.get('query')
    cur = get_db().cursor()
    
    
    sql_query = """
        SELECT u.id, u.email, u.full_name, u.experience, s.name AS service_name,
               st.type_name AS service_type_name, u.address, u.pin_code, 
               u.documents_path, COALESCE(COUNT(sr.id), 0) AS service_request_count, 
               u.rating, u.is_blocked
        FROM users u
        LEFT JOIN services s ON u.service_id = s.id
        LEFT JOIN service_types st ON u.service_type_id = st.id
        LEFT JOIN service_requests sr ON u.id = sr.professional_id
        WHERE u.role = 'professional'
    """
    
    
    if query:
        sql_query += " AND LOWER(u.full_name) LIKE ?"
        parameters = ('%' + query.lower() + '%',)
    else:
        parameters = ()

    
    sql_query += " GROUP BY u.id, s.name, st.type_name"

    
    cur.execute(sql_query, parameters)
    professionals = cur.fetchall()

    return render_template('service_professional_details.html', professionals=professionals)




@app.route('/customer_details')
def customer_details():
    
    customers = fetch_all('''
        SELECT u.id, u.email, u.full_name, u.address, u.pin_code, COUNT(sr.id) AS service_request_count,
            u.is_blocked
        FROM users u
        LEFT JOIN service_requests sr ON u.id = sr.customer_id
        WHERE u.role = 'customer'
        GROUP BY u.id
    ''')
    
    return render_template('customer_details.html', customers=customers)




@app.route('/block_customer/<int:user_id>')
def block_customer(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET is_blocked = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("Customer has been blocked.")
    return redirect(url_for('customer_details'))

@app.route('/unblock_customer/<int:user_id>')
def unblock_customer(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET is_blocked = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("Customer has been unblocked.")
    return redirect(url_for('customer_details'))



@app.route('/professional_details')
def professional_details():
    db = get_db()
    cursor = db.cursor()

    
    cursor.execute('''
    SELECT u.id, u.email, u.full_name, u.experience, s.name AS service_name, 
           st.type_name AS service_type_name, u.address, u.pin_code, u.documents_path, 
           COALESCE(COUNT(sr.id), 0) AS service_request_count, u.rating, u.is_blocked
    FROM users u
    LEFT JOIN services s ON u.service_id = s.id
    LEFT JOIN service_types st ON u.service_type_id = st.id
    LEFT JOIN service_requests sr ON u.id = sr.professional_id
    WHERE u.role = 'professional'
    GROUP BY u.id
''')
    professionals = cursor.fetchall()

    
    professionals = [
        {
            'id': row[0],
            'email': row[1],
            'full_name': row[2],
            'experience': row[3],
            'service_name': row[4],
            'service_type_name': row[5],
            'address': row[6],
            'pin_code': row[7],
            'documents_path': row[8],
            'service_request_count': row[9],
            'rating': row[10],
            'is_blocked': row[11]
        }
        for row in professionals
    ]

    return render_template('service_professional_details.html', professionals=professionals)



@app.route('/block_professional/<int:user_id>')
def block_professional(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET is_blocked = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("Professional has been blocked.")
    return redirect(url_for('professional_details'))

@app.route('/unblock_professional/<int:user_id>')
def unblock_professional(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET is_blocked = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("Professional has been unblocked.")
    return redirect(url_for('professional_details'))




@app.route('/service_details')
def service_details():
    db = get_db()
    cursor = db.cursor()

    
    cursor.execute('''
        SELECT s.id, s.name, s.time_required, s.price, s.description,
               (SELECT GROUP_CONCAT(st.type_name, ', ') 
                FROM (SELECT DISTINCT type_name 
                      FROM service_types 
                      WHERE service_id = s.id) st
               ) AS service_types
        FROM services s
        GROUP BY s.id
    ''')
    services = cursor.fetchall()

    
    services = [
        {
            'id': row[0],
            'name': row[1],
            'time_required': row[2],
            'price': row[3],
            'description': row[4],
            'service_types': row[5] if row[5] else 'No types available'
        }
        for row in services
    ]

    return render_template('services_details.html', services=services)



@app.route('/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    db = get_db()
    
    if request.method == 'POST':
        
        service_name = request.form['service_name']
        time_required = request.form['time_required']
        price = request.form['price']
        description = request.form['description']
        new_service_type = request.form.get('new_service_type')  

        
        db.execute("""
            UPDATE services
            SET name = ?, time_required = ?, price = ?, description = ?
            WHERE id = ?
        """, (service_name, time_required, price, description, service_id))
        db.commit()

        
        if new_service_type:
            service_types = new_service_type.split(",")  
            for service_type in service_types:
                
                service_type = service_type.strip()
                
                
                existing_service_type = db.execute("""
                    SELECT id FROM service_types WHERE type_name = ?
                """, (service_type,)).fetchone()
                
                if not existing_service_type:
                    
                    db.execute("""
                        INSERT INTO service_types (type_name, service_id)
                        VALUES (?, ?)
                    """, (service_type, service_id))
                    db.commit()

        flash("Service updated successfully", "success")
        return redirect(url_for('service_details'))
    
    
    service = db.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    service_types = db.execute("""
        SELECT type_name FROM service_types WHERE service_id = ?
    """, (service_id,)).fetchall()
    
    
    existing_service_types = [type_tuple[0] for type_tuple in service_types]

    return render_template('edit_service.html', service=service, existing_service_types=existing_service_types)



@app.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    db = get_db()
    db.execute("DELETE FROM services WHERE id = ?", (service_id,))
    db.commit()
    flash("Service deleted successfully", "danger")
    return redirect(url_for('service_details'))



@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    db = get_db()
    if request.method == 'POST':
        
        service_name = request.form['service_name']
        time_required = request.form['time_required']
        price = request.form['price']
        description = request.form['description']
        service_types = request.form['service_types']  

        
        db.execute("""
            INSERT INTO services (name, time_required, price, description)
            VALUES (?, ?, ?, ?)
        """, (service_name, time_required, price, description))
        db.commit()

        
        service_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        
        if service_types:
            service_type_list = service_types.split(",")  
            
            service_type_list = list(set([service_type.strip() for service_type in service_type_list]))
            for service_type in service_type_list:
                if service_type:  
                    db.execute("""
                        INSERT INTO service_types (service_id, type_name)
                        VALUES (?, ?)
                    """, (service_id, service_type))
                    db.commit()

        flash("New service added successfully", "success")
        return redirect(url_for('service_details'))

    return render_template('add_service.html')




@app.route('/admin/service_requests')
def admin_service_requests():
    db = get_db()
    
    
    cursor = db.execute("""
        SELECT sr.id, sr.customer_id, sr.professional_id, s.name AS service_name, st.type_name AS service_type, 
        u.pin_code, sr.status, sr.requested_date, sr.completion_date
        FROM service_requests sr
        JOIN services s ON sr.service_id = s.id
        JOIN users u ON sr.customer_id = u.id
        JOIN service_types st ON sr.service_type_id = st.id
    """)
    
    
    service_requests = cursor.fetchall()
    cursor.close()
    
    return render_template('admin_service_requests.html', service_requests=service_requests)



@app.route('/admin_edit_profile', methods=['GET', 'POST'])
def admin_edit_profile():
    
    email = session.get('user')
    
    db = get_db()
    cursor = db.execute("SELECT id, email FROM users WHERE email = ?", (email,))
    admin = cursor.fetchone()
    
    if request.method == 'POST':
        
        new_password = request.form.get('new_password')
        
        if new_password:
            
            db.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, admin['id']))
            db.commit()
            flash("Password updated successfully!")
            return redirect(url_for('admin_home'))
        else:
            flash("Please enter a new password.")

    return render_template('admin_edit_profile.html', admin=admin)




@app.route('/admin_statistics')
def admin_statistics():
    db = get_db()
    cursor = db.cursor()

    
    cursor.execute('''
        SELECT 
            CASE 
                WHEN rating >= 4 THEN '4 and above'
                WHEN rating >= 2 AND rating < 4 THEN 'Between 4 and 2'
                ELSE 'Below 2'
            END AS rating_group,
            COUNT(*) AS count
        FROM users
        WHERE role = 'professional'
        GROUP BY rating_group
    ''')
    
    professional_ratings = [
        {'rating_group': row[0], 'count': row[1]} for row in cursor.fetchall()
    ]

    
    cursor.execute('''
        SELECT s.name, COUNT(sr.id) AS request_count
        FROM service_requests sr
        JOIN services s ON sr.service_id = s.id
        GROUP BY s.name
    ''')
    service_requests_by_name = [
    {'service_name': row[0], 'request_count': row[1]} for row in cursor.fetchall()
    ]

    
    cursor.execute('''
        SELECT pin_code, COUNT(id) AS customer_count
        FROM users
        WHERE role = 'customer'
        GROUP BY pin_code
    ''')
    customers_by_pincode = [
    {'pincode': row[0], 'customer_count': row[1]} for row in cursor.fetchall()
    ]


    
    cursor.execute('''
        SELECT status, COUNT(id) AS request_count
        FROM service_requests
        GROUP BY status
    ''')
    service_requests_by_status = [
    {'status': row[0], 'request_count': row[1]} for row in cursor.fetchall()
    ]

    return render_template(
        'admin_statistics.html', 
        professional_ratings=professional_ratings,
        service_requests_by_name=service_requests_by_name,
        customers_by_pincode=customers_by_pincode,
        service_requests_by_status=service_requests_by_status
    )