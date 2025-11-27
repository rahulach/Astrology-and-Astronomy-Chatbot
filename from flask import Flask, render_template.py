from flask import Flask, render_template, request, jsonify
import requests
from config import Config
import json
import urllib.parse
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
config = Config()

# Database setup function
def init_db():
    db_path = os.path.join(app.root_path, 'astronomy.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create events table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        description TEXT,
        image TEXT
    )
    ''')
    
    # Check if we have any events already
    cursor.execute('SELECT COUNT(*) FROM events')
    if cursor.fetchone()[0] == 0:
        # Insert sample data if the table is empty
        sample_events = [
            (1, "Perseid Meteor Shower", "2025-08-12", "Meteor Shower",
             "One of the brightest meteor showers, peaking at 50-75 meteors per hour.",
             "https://apod.nasa.gov/apod/image/2008/Perseids_ESO_1080.jpg"),
            (2, "Total Lunar Eclipse", "2025-05-26", "Eclipse",
             "A total lunar eclipse visible from parts of Asia, Australia, and the Americas.",
             "https://apod.nasa.gov/apod/image/1801/TotalLunarEclipse_Fairbairn_3000.jpg"),
            (3, "Jupiter at Opposition", "2025-07-15", "Planetary Event",
             "Jupiter will be at its closest approach to Earth, fully illuminated by the Sun.",
             "https://apod.nasa.gov/apod/image/2108/Jupiter_Close_Approach_Sankar_3000.jpg"),
            (4, "Full Moon (Strawberry Moon)", "2025-06-13", "Lunar Phase",
             "The June full moon, traditionally called the Strawberry Moon.",
             "https://apod.nasa.gov/apod/image/2006/StrawberryMoon_Horalek_1500.jpg"),
            (5, "Partial Solar Eclipse", "2025-09-30", "Eclipse",
             "A partial solar eclipse visible from parts of North America and Europe.",
             "https://apod.nasa.gov/apod/image/1708/PartialSolarEclipse_Horalek_1500.jpg")
        ]
        cursor.executemany('INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)', sample_events)
        conn.commit()
    conn.close()

# Function to get events from database
def get_db_events():
    db_path = os.path.join(app.root_path, 'astronomy.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM events ORDER BY date')
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return events

# Initialize database on startup
with app.app_context():
    init_db()

# Routes
@app.route('/')
def index():
    events = get_db_events()
    featured_events = events[:3]
    return render_template('index.html', featured_events=featured_events)

@app.route('/calendar')
def calendar():
    events = get_db_events()
    return render_template('calendar.html', events=events)

@app.route('/astrology')
def astrology():
    return render_template('astrology.html')

@app.route('/chat')
def chat():
    # Get NASA APOD for the chat page
    params = {'api_key': config.NASA_API_KEY}
    response = requests.get(config.NASA_APOD_URL, params=params)
    apod_data = response.json() if response.status_code == 200 else None
    return render_template('chat.html', apod=apod_data)

@app.route('/explore')
def explore():
    return render_template('explore.html')

@app.route('/starmap')
def starmap():
    # New route for interactive star map
    return render_template('starmap.html')

# API Endpoints
@app.route('/api/nasa/apod', methods=['GET'])
def get_nasa_apod():
    params = {'api_key': config.NASA_API_KEY}
    response = requests.get(config.NASA_APOD_URL, params=params)
    return jsonify(response.json() if response.status_code == 200 else {"error": "Failed to fetch APOD"})

@app.route('/api/nasa/search', methods=['GET'])
def search_nasa_images():
    query = request.args.get('q', 'stars')
    params = {'q': query}
    response = requests.get(config.NASA_IMAGE_SEARCH_URL, params=params)
    return jsonify(response.json() if response.status_code == 200 else {"error": "Failed to search NASA images"})

@app.route('/api/pixabay/search', methods=['GET'])
def search_pixabay_images():
    query = request.args.get('q', 'space')
    params = {
        'key': config.PIXABAY_API_KEY,
        'q': query,
        'image_type': 'photo'
    }
    response = requests.get(config.PIXABAY_API_URL, params=params)
    return jsonify(response.json() if response.status_code == 200 else {"error": "Failed to search Pixabay images"})

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    query = request.json.get('query', '')
    
    # Ensure the chat stays focused on astronomy
    prompt = f"Answer the following astronomy question: {query}. Keep your response focused on astronomy topics only."
    
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': config.GEMINI_API_KEY
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    response = requests.post(
        f"{config.GEMINI_API_URL}?key={config.GEMINI_API_KEY}",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        response_data = response.json()
        try:
            # Extract the AI's response from the Gemini response structure
            ai_response = response_data['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"response": ai_response})
        except (KeyError, IndexError):
            return jsonify({"error": "Invalid AI response format"})
    
    return jsonify({"error": "Failed to get AI response"})

@app.route('/api/events', methods=['GET'])
def get_events():
    events = get_db_events()
    return jsonify(events)

@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    db_path = os.path.join(app.root_path, 'astronomy.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
    event = cursor.fetchone()
    conn.close()
    
    if event:
        return jsonify(dict(event))
    return jsonify({"error": "Event not found"}), 404

@app.route('/api/weather/observing', methods=['GET'])
def get_observing_conditions():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude are required"}), 400
    
    # Weather API call (using OpenWeatherMap as an example)
    params = {
        'lat': lat,
        'lon': lon,
        'appid': config.WEATHER_API_KEY,
        'units': 'metric'
    }
    
    try:
        response = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params)
        if response.status_code == 200:
            weather_data = response.json()
            
            # Calculate observing conditions quality
            clouds = weather_data.get('clouds', {}).get('all', 0)
            visibility = weather_data.get('visibility', 0)
            wind_speed = weather_data.get('wind', {}).get('speed', 0)
            
            # Determine if conditions are good for stargazing
            is_clear = clouds < 20
            is_calm = wind_speed < 15
            is_good_visibility = visibility > 8000
            
            observing_quality = "Good" if (is_clear and is_calm and is_good_visibility) else "Fair" if (clouds < 40 and is_calm) else "Poor"
            
            return jsonify({
                "observing_quality": observing_quality,
                "cloud_cover_percent": clouds,
                "wind_speed": wind_speed,
                "visibility": visibility,
                "current_weather": weather_data['weather'][0]['description'],
                "temperature": weather_data['main']['temp']
            })
        else:
            return jsonify({"error": "Failed to fetch weather data"}), response.status_code
    except Exception as e:
        return jsonify({"error": f"Weather API error: {str(e)}"}), 500

@app.route('/api/starmap/data', methods=['GET'])
def get_starmap_data():
    lat = request.args.get('lat', '0')
    lon = request.args.get('lon', '0')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        # Using Astronomy API (example - you'll need to sign up for an appropriate service)
        params = {
            'latitude': lat,
            'longitude': lon,
            'date': date,
            'apiKey': config.ASTRONOMY_API_KEY
        }
        
        response = requests.get('https://api.astronomyapi.com/api/v2/bodies/positions', params=params)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to fetch star map data"}), response.status_code
    except Exception as e:
        return jsonify({"error": f"Star map API error: {str(e)}"}), 500

@app.route('/api/zodiac', methods=['POST'])
def calculate_zodiac():
    birth_date = request.json.get('birth_date', '')
    try:
        # Parse month and day from birth_date (format: YYYY-MM-DD)
        month, day = int(birth_date.split('-')[1]), int(birth_date.split('-')[2])
        
        # Dictionary of zodiac signs with their date ranges and details
        zodiac_signs = {
            "Aries": {"start": (3, 21), "end": (4, 19), "element": "Fire", 
                      "traits": "Independent, assertive, energetic", 
                      "description": "Aries is the first sign of the zodiac, symbolizing new beginnings. People born under this sign are often characterized by their boldness and pioneering spirit."},
            "Taurus": {"start": (4, 20), "end": (5, 20), "element": "Earth", 
                      "traits": "Patient, reliable, practical", 
                      "description": "Taurus is known for stability and persistence. Those born under this sign value security and comfort, and are often very reliable."},
            "Gemini": {"start": (5, 21), "end": (6, 20), "element": "Air", 
                      "traits": "Adaptable, communicative, curious", 
                      "description": "Gemini is represented by the twins, symbolizing duality. People with this sign are often versatile, inquisitive, and excellent communicators."},
            "Cancer": {"start": (6, 21), "end": (7, 22), "element": "Water", 
                      "traits": "Intuitive, emotional, protective", 
                      "description": "Cancer is deeply connected to home and family. Those born under this sign are often nurturing, empathetic, and protective of loved ones."},
            "Leo": {"start": (7, 23), "end": (8, 22), "element": "Fire", 
                      "traits": "Confident, generous, loyal", 
                      "description": "Leo is represented by the lion, symbolizing courage and leadership. People with this sign often have a natural flair for drama and creativity."},
            "Virgo": {"start": (8, 23), "end": (9, 22), "element": "Earth", 
                      "traits": "Analytical, precise, helpful", 
                      "description": "Virgo is associated with meticulousness and service. Those born under this sign are often detail-oriented, practical, and devoted to self-improvement."},
            "Libra": {"start": (9, 23), "end": (10, 22), "element": "Air", 
                      "traits": "Balanced, diplomatic, social", 
                      "description": "Libra is symbolized by the scales, representing balance and harmony. People with this sign often have a strong sense of justice and value relationships."},
            "Scorpio": {"start": (10, 23), "end": (11, 21), "element": "Water", 
                      "traits": "Passionate, resourceful, brave", 
                      "description": "Scorpio is associated with intensity and transformation. Those born under this sign are often determined, passionate, and perceptive."},
            "Sagittarius": {"start": (11, 22), "end": (12, 21), "element": "Fire", 
                      "traits": "Optimistic, adventurous, independent", 
                      "description": "Sagittarius is represented by the archer, symbolizing aspiration and exploration. People with this sign often love travel, learning, and philosophical discussions."},
            "Capricorn": {"start": (12, 22), "end": (1, 19), "element": "Earth", 
                      "traits": "Disciplined, responsible, self-controlled", 
                      "description": "Capricorn is associated with ambition and discipline. Those born under this sign are often hardworking, patient, and practical."},
            "Aquarius": {"start": (1, 20), "end": (2, 18), "element": "Air", 
                      "traits": "Progressive, original, independent", 
                      "description": "Aquarius is known for innovation and humanitarianism. People with this sign are often forward-thinking, unconventional, and value intellectual stimulation."},
            "Pisces": {"start": (2, 19), "end": (3, 20), "element": "Water", 
                      "traits": "Compassionate, artistic, intuitive", 
                      "description": "Pisces is symbolized by the fish, representing connection to the spiritual realm. Those born under this sign are often creative, empathetic, and dreamy."}
        }
        
        # Find the zodiac sign
        for sign, info in zodiac_signs.items():
            start_month, start_day = info["start"]
            end_month, end_day = info["end"]
            
            # Handle cases that span year boundary (like Capricorn)
            if start_month > end_month:
                if (month == start_month and day >= start_day) or (month == end_month and day <= end_day) or (month > start_month) or (month < end_month):
                    result = {"sign": sign, "element": info["element"], "traits": info["traits"], "description": info["description"]}
                    break
            else:
                if (month == start_month and day >= start_day) or (month == end_month and day <= end_day) or (start_month < month < end_month):
                    result = {"sign": sign, "element": info["element"], "traits": info["traits"], "description": info["description"]}
                    break
        else:
            return jsonify({"error": "Could not determine zodiac sign"})
            
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)