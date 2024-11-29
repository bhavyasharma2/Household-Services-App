# EaseWork 
### A Household Services Application

A comprehensive web-based platform designed to seamlessly connect customers with skilled service professionals for various household needs. The application features role-specific functionalities tailored for Admins, Service Professionals, and Customers, enabling efficient management of service requests, assignments, and reviews while ensuring a user-friendly experience for all participants.

---

## Functionalities

### Admin
- Approves or rejects service professional registration requests.
- Blocks/unblocks users (customers or professionals) based on activity or reviews.
- Monitors all users and service requests.
- Creates and manages services with a base price.
- Can view system statistics

### Service Professional
- Registers and uploads documents for admin approval.
- Views and accepts/rejects service requests from customers.
- Can view closed service requests and customer reviews.

### Customer
- Registers and logs in to book household services.
- Searches services available on the platform.
- Tracks the status of service requests (Requested, Assigned, Completed).
- Closes services and submits reviews with ratings for professionals.

---

## Technologies Used
### Backend
- **Flask**: A lightweight Python web framework for building and handling server-side logic.
- **SQLite**: A simple, serverless database for data storage.

### Frontend
- **Jinja2**: A templating engine for rendering dynamic HTML pages.
- **Bootstrap**: A CSS framework for responsive design and UI components.

### Development Tools
- **Python**: Primary programming language.
- **WSL (Windows Subsystem for Linux)**: Ubuntu environment for development on Windows.

---

## Installation and Setup

Follow these steps to set up and run the project on your system:

### 1. Clone the Repository
```bash
git clone https://github.com/bhavyasharma2/Household-Services-App.git
cd Household-Services-App
 ```

### 2. Install Requirements
```bash
pip install -r requirements.txt
sudo apt install sqlite3
 ```

### 3. Run Application
```bash
python3 app.py
 ```
