from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
import os # Import the os module

# Initialize Flask and extensions
app = Flask(__name__)

# --- Database Configuration ---
# Get the absolute path for the directory where this file is located
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
# --- FIX: Added cors_allowed_origins to solve the browser security error ---
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Database Models ---
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    route_id = db.Column(db.String(80))
    locations = db.relationship('Location', backref='vehicle', lazy=True)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# --- API Endpoint ---
@app.route('/api/v1/location_update', methods=['POST'])
def location_update():
    data = request.json
    vehicle_id = data.get('vehicle_id')
    lat = data.get('latitude')
    lng = data.get('longitude')
    
    if not all([vehicle_id, lat, lng]):
        return jsonify({'error': 'Missing data'}), 400

    vehicle = db.session.get(Vehicle, vehicle_id)
    if not vehicle:
        return jsonify({'error': f'Vehicle with id {vehicle_id} not found'}), 404

    new_location = Location(
        vehicle_id=vehicle_id,
        latitude=lat,
        longitude=lng
    )
    db.session.add(new_location)
    db.session.commit()

    socketio.emit('location_update', {
        'vehicle_id': vehicle_id,
        'latitude': lat,
        'longitude': lng,
        'timestamp': new_location.timestamp.isoformat()
    })
    
    return jsonify({'message': 'Location updated successfully'}), 200

# --- NEW API Endpoint for vehicle list ---
@app.route('/api/v1/vehicles', methods=['GET'])
def get_vehicles():
    """Returns a list of all vehicles."""
    vehicles = Vehicle.query.all()
    vehicle_list = [
        {'id': v.id, 'name': v.name, 'route_id': v.route_id}
        for v in vehicles
    ]
    return jsonify(vehicle_list)

# --- NEW API Endpoint for historical data ---
@app.route('/api/v1/history', methods=['GET'])
def get_history():
    """Returns the location history for a vehicle on a specific date."""
    vehicle_id = request.args.get('vehicle_id')
    date_str = request.args.get('date')

    if not all([vehicle_id, date_str]):
        return jsonify({'error': 'Missing vehicle_id or date parameter'}), 400

    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_of_day = datetime.combine(query_date, time.min)
        end_of_day = datetime.combine(query_date, time.max)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    locations = Location.query.filter(
        Location.vehicle_id == vehicle_id,
        Location.timestamp.between(start_of_day, end_of_day)
    ).order_by(Location.timestamp.asc()).all()

    history_data = [
        {
            'latitude': loc.latitude,
            'longitude': loc.longitude,
            'timestamp': loc.timestamp.isoformat()
        }
        for loc in locations
    ]
    return jsonify(history_data)

# --- Frontend Route ---
@app.route('/')
def index():
    """Serves the main tracking page."""
    return render_template('index.html')

# --- Function to automatically create DB and seed data ---
def init_database():
    """Creates the database tables and populates them if they don't exist."""
    with app.app_context():
        db.create_all()
        if not Vehicle.query.first():
            print("Database is empty. Seeding initial vehicles...")
            vehicle1 = Vehicle(name='Bus 101', route_id='Route A')
            vehicle2 = Vehicle(name='Bus 102', route_id='Route B')
            db.session.add(vehicle1)
            db.session.add(vehicle2)
            db.session.commit()
            print("Database seeded successfully.")
        else:
            print("Database already exists.")

# --- Main execution block ---
if __name__ == '__main__':
    init_database()
    socketio.run(app, host='0.0.0.0', debug=True, port=5001)

