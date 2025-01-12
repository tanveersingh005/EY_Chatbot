from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required
from datetime import datetime
import requests

# Initialize the Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super-secret-key'
app.config['SECURITY_PASSWORD_SALT'] = 'super-secret-salt'

# Initialize the database
db = SQLAlchemy(app)

# Define roles and users for Flask-Security
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

# Define the data model for patient data
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    symptoms = db.Column(db.String(500))
    diagnosis = db.Column(db.String(500))
    appointment_date = db.Column(db.DateTime, nullable=True)

# Set up Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# API Keys for Infermedica
INFERMEDICA_APP_ID = 'your_infermedica_app_id'
INFERMEDICA_APP_KEY = 'your_infermedica_app_key'

# Helper function for symptom analysis
def analyze_symptoms(symptoms):
    url = "https://api.infermedica.com/v3/diagnosis"
    headers = {
        "App-Id": INFERMEDICA_APP_ID,
        "App-Key": INFERMEDICA_APP_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "age": {"value": 30},  # Example age, can be modified based on input
        "sex": "male",         # Example gender, can be modified based on input
        "evidence": [{"id": sym, "choice_id": "present"} for sym in symptoms]
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Routes
@app.route('/')
def home():
    return render_template('index.html')  # A simple frontend for user interaction

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    data = request.json
    name = data.get('name')
    age = data.get('age')
    gender = data.get('gender')
    symptoms = data.get('symptoms', [])
    # Analyze symptoms using Infermedica
    diagnosis = analyze_symptoms(symptoms)
    # Save to database
    patient = Patient(name=name, age=age, gender=gender, symptoms=", ".join(symptoms), diagnosis=str(diagnosis))
    db.session.add(patient)
    db.session.commit()
    return jsonify({"message": "Diagnosis complete", "data": diagnosis})

@app.route('/schedule', methods=['POST'])
@login_required
def schedule():
    data = request.json
    name = data.get('name')
    appointment_date = data.get('appointment_date')
    patient = Patient.query.filter_by(name=name).first()
    if patient:
        patient.appointment_date = datetime.strptime(appointment_date, "%Y-%m-%d")
        db.session.commit()
        return jsonify({"message": "Appointment scheduled successfully"})
    return jsonify({"error": "Patient not found"}), 404

@app.route('/reminder', methods=['POST'])
@login_required
def reminder():
    data = request.json
    name = data.get('name')
    medication = data.get('medication')
    time = data.get('time')
    return jsonify({"message": f"Reminder set for {name} to take {medication} at {time}"})

# Error handling
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

# Create database and roles
@app.before_first_request
def create_user_and_roles():
    db.create_all()
    if not Role.query.first():
        user_datastore.create_role(name='admin')
        user_datastore.create_role(name='user')
    if not User.query.first():
        user_datastore.create_user(email='admin@example.com', password='password', roles=['admin'])
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
