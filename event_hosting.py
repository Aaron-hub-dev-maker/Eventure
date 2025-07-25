from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Setup MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['events']  # Database
collection = db['parties']  # Collection for events

@app.route('/host', methods=['POST'])
def host_event():
    try:
        # Retrieve form data
        name = request.form.get('name')
        category = request.form.get('category')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        place = request.form.get('place')
        landmark = request.form.get('landmark')
        distance_str = request.form.get('distance')  # Get distance as a string

        # Validate required fields
        if not all([name, category, date_str, time_str, place, landmark, distance_str]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400

        # Validate and parse distance
        try:
            distance = float(distance_str)
        except ValueError:
            return jsonify({'success': False, 'error': 'Distance must be a valid number'}), 400

        # Validate and parse date and time
        try:
            event_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date or time format'}), 400

        # Create event data dictionary
        event_data = {
            'Name': name,
            'DateTime': event_datetime,
            'Place': place,
            'Distance': distance,
            'Category': category,
            'Checkpoint': landmark
        }

        # Insert into MongoDB
        result = collection.insert_one(event_data)

        # Return success response with inserted ID
        return jsonify({'success': True, 'inserted_id': str(result.inserted_id)})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/')
def index():
    try:
        # Fetch all events from the database
        events = list(collection.find())
        return render_template('index.html', events=events)
    except Exception as e:
        print(f"Error fetching events: {e}")
        return jsonify({'success': False, 'error': 'Error fetching events'}), 500

if __name__ == '__main__':
    app.run(debug=True)
