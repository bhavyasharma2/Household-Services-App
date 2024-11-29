import sqlite3


conn = sqlite3.connect('household_services.db')
cursor = conn.cursor()


cursor.execute('DROP TABLE IF EXISTS users')
cursor.execute('DROP TABLE IF EXISTS service_types')
cursor.execute('DROP TABLE IF EXISTS service_requests')


cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        full_name TEXT,
        address TEXT,
        pin_code INTEGER,
        mobile_number TEXT,
        experience INTEGER,
        rating FLOAT DEFAULT 0,       
        documents_path TEXT,  
        service_id INTEGER,  
        service_type_id INTEGER,       
        is_blocked INTEGER DEFAULT 0,
        FOREIGN KEY (service_id) REFERENCES services(id),  
        FOREIGN KEY (service_type_id) REFERENCES service_types(id)       
    )
''')


cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,       
        name TEXT NOT NULL,       
        price REAL NOT NULL,
        time_required INTEGER NOT NULL,
        description TEXT NOT NULL        
    )
''')


cursor.execute('''
    CREATE TABLE IF NOT EXISTS service_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,  
        type_name TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services(id)
    )
''')



cursor.execute('''
    CREATE TABLE IF NOT EXISTS service_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    service_type_id INTEGER,           
    professional_id INTEGER NOT NULL,
    requested_date TEXT NOT NULL,
    completion_date TEXT,
    status TEXT NOT NULL DEFAULT 'Pending',
    FOREIGN KEY (customer_id) REFERENCES users(id),
    FOREIGN KEY (service_id) REFERENCES services(id),
    FOREIGN KEY (professional_id) REFERENCES users(id),
    FOREIGN KEY (service_type_id) REFERENCES service_types(id)            
    )
''')


cursor.execute('''
    CREATE TABLE IF NOT EXISTS pending_registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        service_id INTEGER NOT NULL,
        service_type_id INTEGER NOT NULL,
        experience INTEGER NOT NULL,
        address TEXT NOT NULL,
        pin_code TEXT NOT NULL,
        mobile_number TEXT NOT NULL,
        documents_path TEXT,
        FOREIGN KEY (service_id) REFERENCES services(id),
        FOREIGN KEY (service_type_id) REFERENCES service_types(id)
    )
''')


services = [
    (1, 'Cleaning Services', 1000, 2, 'Professional cleaning and maintenance.'),
    (2, 'Plumbing', 500, 1, 'Plumbing repair and maintenance.'),
    (3, 'Electrical Work', 600, 1, 'Installation and repair of electrical systems.')
]
for service in services:
    cursor.execute('INSERT OR IGNORE INTO services (id, name, price, time_required, description) VALUES (?, ?, ?, ?, ?)', service)


cursor.execute('''
    INSERT OR IGNORE INTO users (email, password, role) VALUES 
    ('admin@example.com', 'admin123', 'admin')
''')


customers = [
    ('customer1@example.com', 'customer1', 'customer', 'Alia Sharma', '123 Main St, City', 12345, '9876543210'),
    ('customer2@example.com', 'customer2', 'customer', 'Krishna Pareek', '456 Elm St, City', 54321, '9876543211')
]

for customer in customers:
    cursor.execute('''
        INSERT INTO users (email, password, role, full_name, address, pin_code, mobile_number)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', customer)


professionals = [
    ('professional1@example.com', 'professional1', 'professional', 'Bhanu Pratap', '789 Oak St, City', 12345, '9876543212', 5, 4, 1, 1),
    ('professional2@example.com', 'professional2', 'professional', 'Raghu Tank', '101 Pine St, City', 54321, '9876543213', 3, 5, 2, 4)
]

for professional in professionals:
    cursor.execute('''
        INSERT INTO users (email, password, role, full_name, address, pin_code, mobile_number, experience, rating, service_id, service_type_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', professional)


service_types = [
    (1, 'Carpet Cleaning'),
    (1, 'Kitchen Cleaning'),
    (2, 'Leak Repair'),
    (2, 'Pipe Installation'),
    (3, 'Fixture Installation'),
    (3, 'Wiring Repair')
]

for service_type in service_types:
    cursor.execute('INSERT OR IGNORE INTO service_types (service_id, type_name) VALUES (?, ?)', service_type)


conn.commit()
conn.close()

print("Database setup complete with one admin, two customers, and two professionals.")


