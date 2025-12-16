from flask import Flask, render_template
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from views.UserView import init_user_routes
from views.AppointmentView import init_appointment_routes
from views.AdminView import init_admin_routes

app = Flask(__name__)

@app.route('/home')
def home():
    return render_template('home.html')

def create_app():

    app.config.from_pyfile('config.py')
    db = MySQL(app)
    bcrypt = Bcrypt(app)

    init_user_routes(app, db, bcrypt)
    init_appointment_routes(app, db)
    init_admin_routes(app, db)

    return app, db

if __name__ == '__main__':
    app, db = create_app()

    app.run(debug=True)
