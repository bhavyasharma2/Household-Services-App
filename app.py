from flask import Flask
import os

app = Flask(__name__)

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'defaultsecretkey')


@app.route('/')
def index():
    return redirect(url_for('login'))  


from routes.login_and_logout_routes import *
from routes.admin_dashboard_routes import *
from routes.professional_dashboard_routes import *
from routes.customer_dashboard_routes import *
from routes.register_routes import *

if __name__ == '__main__':
    app.run(debug=True)

