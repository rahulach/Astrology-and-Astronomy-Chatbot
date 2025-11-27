from flask import Flask, render_template, request, jsonify
import requests
from config import Config
import json
import urllib.parse
import sqlite3
from datetime import datetime
import os
import base64

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
             "https://apod.nasa.gov/apod/image/1708/PartialSolarEclipse_Horalek_1500.jpg"),
            # Add 5 new events here with appropriate online images
            (6, "Supermoon", "2025-10-15", "Lunar Phase",
             "The Moon appears bigger and brighter than usual as it reaches perigee - its closest point to Earth.",
             "https://images.unsplash.com/photo-1496429862132-5ab36b6ae330?q=80&w=1000&auto=format&fit=crop"),
            (7, "Neowise Comet Approach", "2025-11-03", "Comet",
             "Comet Neowise makes its closest approach to Earth, visible with the naked eye in the northern hemisphere.",
             "https://images.unsplash.com/photo-1595508064774-5ff825ff0f81?q=80&w=1000&auto=format&fit=crop"),
            (8, "Venus-Jupiter Conjunction", "2025-11-23", "Planetary Event",
             "The two brightest planets appear to meet in the night sky, coming within 0.3 degrees of each other.",
             "https://images.unsplash.com/photo-1543722530-d2c3201371e7?q=80&w=1000&auto=format&fit=crop"),
            (9, "Northern Lights Outburst", "2025-12-21", "Auroral Display",
             "A predicted geomagnetic storm will cause spectacular aurora displays visible at unusually low latitudes.",
             "https://images.unsplash.com/photo-1483347756197-71ef80e95f73?q=80&w=1000&auto=format&fit=crop"),
            (10, "Geminid Meteor Storm", "2025-12-14", "Meteor Storm",
             "An unusually intense meteor shower with up to 150 meteors per hour at its peak.",
             "https://images.unsplash.com/photo-1607437817193-3b3d1b2c7ced?q=80&w=1000&auto=format&fit=crop")
        ]
        cursor.executemany('INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)', sample_events)
        conn.commit()
    else:
        # Check if we need to add the new events
        cursor.execute('SELECT id FROM events WHERE id = 10')
        if not cursor.fetchone():
            # Add the new events
            new_events = [
                (6, "Supermoon", "2025-10-15", "Lunar Phase",
                 "The Moon appears bigger and brighter than usual as it reaches perigee - its closest point to Earth.",
                 "https://images.unsplash.com/photo-1496429862132-5ab36b6ae330?q=80&w=1000&auto=format&fit=crop"),
                (7, "Neowise Comet Approach", "2025-11-03", "Comet",
                 "Comet Neowise makes its closest approach to Earth, visible with the naked eye in the northern hemisphere.",
                 "https://images.unsplash.com/photo-1595508064774-5ff825ff0f81?q=80&w=1000&auto=format&fit=crop"),
                (8, "Venus-Jupiter Conjunction", "2025-11-23", "Planetary Event",
                 "The two brightest planets appear to meet in the night sky, coming within 0.3 degrees of each other.",
                 "https://images.unsplash.com/photo-1543722530-d2c3201371e7?q=80&w=1000&auto=format&fit=crop"),
                (9, "Northern Lights Outburst", "2025-12-21", "Auroral Display",
                 "A predicted geomagnetic storm will cause spectacular aurora displays visible at unusually low latitudes.",
                 "https://images.unsplash.com/photo-1483347756197-71ef80e95f73?q=80&w=1000&auto=format&fit=crop"),
                (10, "Geminid Meteor Storm", "2025-12-14", "Meteor Storm",
                 "An unusually intense meteor shower with up to 150 meteors per hour at its peak.",
                 "https://images.unsplash.com/photo-1607437817193-3b3d1b2c7ced?q=80&w=1000&auto=format&fit=crop")
            ]
            cursor.executemany('INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)', new_events)
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
    # Get unique event types with assigned colors
    event_types = get_event_types_with_colors()
    
    # Add display_class to each event based on its type
    for event in events:
        event['tag_color'] = event_types.get(event['type'])
        # Create a CSS class name from the type (lowercase, no spaces)
        event['display_class'] = 'event-' + event['type'].lower().replace(' ', '-')
    
    return render_template('calendar.html', events=events, event_types=event_types)

@app.route('/api/quiz/question', methods=['GET'])
def get_quiz_question():
    try:
        # Load quiz data from JSON file
        quiz_file_path = os.path.join(app.root_path, 'static', 'data', 'astronomy_quiz.json')
        
        with open(quiz_file_path, 'r') as f:
            quiz_data = json.load(f)
            
        # Get a random question
        question_id = request.args.get('id')
        
        if question_id:
            # Try to get a specific question by ID
            try:
                question_index = int(question_id) % len(quiz_data)
                return jsonify(quiz_data[question_index])
            except (ValueError, IndexError):
                # If ID is invalid, fall back to random
                import random
                return jsonify(random.choice(quiz_data))
        else:
            # Return a random question
            import random
            return jsonify(random.choice(quiz_data))
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/astrology')
def astrology():
    zodiac_emojis = {
        "Aries": "♈",
        "Taurus": "♉",
        "Gemini": "♊",
        "Cancer": "♋",
        "Leo": "♌",
        "Virgo": "♍",
        "Libra": "♎",
        "Scorpio": "♏",
        "Sagittarius": "♐",
        "Capricorn": "♑",
        "Aquarius": "♒",
        "Pisces": "♓"
    }
    return render_template('astrology.html', zodiac_emojis=zodiac_emojis)

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
    
    # Standard redirect message for non-astronomy queries
    astronomy_redirect = "I can only answer questions about astronomy and space topics. Please ask me about planets, stars, galaxies, or other cosmic phenomena instead."
    
    # Step 1: Pre-filtering - Check if query is astronomy-related
    if not is_astronomy_related_query(query):
        return jsonify({"response": astronomy_redirect})
    
    # Step 2: Check for astronomy-adjacent terms that might be valid queries
    if has_astronomy_context(query):
        # Proceed with the query even if it's not strictly astronomy but has context
        pass
    
    # Ensure the chat stays focused on astronomy
    prompt = f"""
    You are CosmicAssistant, an expert in astronomy and space science. Your purpose is to provide accurate, educational information about astronomy, space, planets, stars, galaxies, celestial events, or space exploration.

    MOST CRITICAL RULE: 
    * You MUST respond to astronomy and space-related questions with helpful, educational information.
    * For questions about upcoming space events, NASA missions, astronomical observations, or space news, provide informative responses.
    * For ANY query completely unrelated to astronomy or space science, respond ONLY with exactly:
      "I can only answer questions about astronomy and space topics. Please ask me about planets, stars, galaxies, or other cosmic phenomena instead."
    * Space exploration, astronomy history, and current space missions are all valid topics.
    
    User question: {query}
    
    Remember: If the question isn't about astronomy or space, provide ONLY the standard redirection response.
    """
    
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
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024
        }
    }
    
    # Updated to use Gemini 2.0 Flash model
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={config.GEMINI_API_KEY}",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        response_data = response.json()
        try:
            # Extract the AI's response from the Gemini response structure
            ai_response = response_data['candidates'][0]['content']['parts'][0]['text']
            
            # Double-check if response is still astronomy focused
            if not is_astronomy_related_response(ai_response):
                return jsonify({"response": astronomy_redirect})
                
            return jsonify({"response": ai_response})
        except (KeyError, IndexError):
            return jsonify({"error": "Invalid AI response format"})
    
    return jsonify({"error": "Failed to get AI response"})

def has_astronomy_context(message):
    """Check for astronomy-adjacent terms that might not be in our main keyword list but are valid questions"""
    astronomy_context_terms = [
        'upcoming', 'launch', 'mission', 'event', 'news', 'discovery', 
        'observation', 'tonight', 'visible', 'sky', 'watch',
        'when can i see', 'next', 'future', 'planned', 'schedule',
        'space program', 'nasa', 'esa', 'spacex', 'isro', 'jaxa'
    ]
    
    message_lower = message.lower()
    
    # Check for combinations of context terms
    for term in astronomy_context_terms:
        if term in message_lower:
            # If we find a contextual term, it's likely astronomy-related
            return True
            
    return False

def is_astronomy_related_query(message):
    """Check if a query is related to astronomy"""
    astronomy_keywords = [
        'planet', 'moon', 'star', 'sun', 'galaxy', 'asteroid', 'comet', 'meteor', 
        'constellation', 'nebula', 'black hole', 'supernova', 'pulsar', 'quasar',
        'solar system', 'exoplanet', 'satellite', 'orbit', 'celestial', 
        'nasa', 'esa', 'spacex', 'space mission', 'astronaut', 'spacecraft', 'telescope',
        'hubble', 'james webb', 'voyager', 'rover', 'rocket', 'launch', 'station',
        'space', 'astronomy', 'universe', 'cosmos', 'cosmic', 'astronomical',
        'light year', 'parsec', 'gravity', 'big bang', 'eclipse', 'orbit',
        'mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 
        'neptune', 'pluto', 'eclipse', 'meteor shower', 'northern lights', 'aurora', 'gravity',
        'solstice', 'equinox', 'transit', 'conjunction', 'redshift'
    ]
    
    message_lower = message.lower()
    
    # First check for explicit non-astronomy terms
    non_astronomy_topics = [
        'weather', 'sports', 'politics', 'music', 'movie', 'film', 
        'celebrity', 'actor', 'actress', 'singer', 'artist',
        'recipe', 'food', 'cook', 'restaurant', 'diet',
        'stock', 'market', 'finance', 'money', 'investment',
        'dating', 'relationship', 'breakup', 'marriage',
        'medical', 'disease', 'symptom', 'health', 'doctor',
        'attorney', 'lawyer', 'legal', 'lawsuit',
        'birthday', 'gift', 'present', 'shopping'
    ]
    
    for topic in non_astronomy_topics:
        if topic in message_lower:
            return False
    
    # Then check for astronomy terms
    for keyword in astronomy_keywords:
        if keyword in message_lower:
            return True
            
    # Additional space-related patterns
    space_patterns = [
        'why is the sky', 'what is in space', 'how far', 'light from', 
        'how old is the', 'what causes', 'why do stars', 'when can i see', 
        'how to observe', 'stargazing', 'night sky'
    ]
    
    for pattern in space_patterns:
        if pattern in message_lower:
            return True
    
    # If no astronomy terms found, assume it's not astronomy-related
    return False

def is_astronomy_related_response(response):
    """Check if AI response is astronomy-related"""
    # If it's the standard redirect, it's valid
    if "I can only answer questions about astronomy and space topics" in response:
        return True
    
    # Count astronomy terms in the response
    astronomy_keywords = [
        'planet', 'moon', 'star', 'sun', 'galaxy', 'asteroid', 'comet', 
        'constellation', 'nebula', 'black hole', 'supernova', 
        'solar system', 'exoplanet', 'orbit', 'celestial', 
        'nasa', 'telescope', 'space', 'astronomy', 'universe', 'cosmos', 
        'astronomical', 'light year', 'gravity', 'earth', 'mars', 'jupiter'
    ]
    
    response_lower = response.lower()
    
    astronomy_term_count = sum(1 for keyword in astronomy_keywords if keyword in response_lower)
    
    # If the response contains at least 2 astronomy terms, consider it valid
    return astronomy_term_count >= 2

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
                      "description": "Aries is the first sign of the zodiac, symbolizing new beginnings. People born under this sign are often characterized by their boldness and pioneering spirit.",
                      "emoji": "♈"},
            "Taurus": {"start": (4, 20), "end": (5, 20), "element": "Earth", 
                      "traits": "Patient, reliable, practical", 
                      "description": "Taurus is known for stability and persistence. Those born under this sign value security and comfort, and are often very reliable.",
                      "emoji": "♉"},
            "Gemini": {"start": (5, 21), "end": (6, 20), "element": "Air", 
                      "traits": "Adaptable, communicative, curious", 
                      "description": "Gemini is represented by the twins, symbolizing duality. People with this sign are often versatile, inquisitive, and excellent communicators.",
                      "emoji": "♊"},
            "Cancer": {"start": (6, 21), "end": (7, 22), "element": "Water", 
                      "traits": "Intuitive, emotional, protective", 
                      "description": "Cancer is deeply connected to home and family. Those born under this sign are often nurturing, empathetic, and protective of loved ones.",
                      "emoji": "♋"},
            "Leo": {"start": (7, 23), "end": (8, 22), "element": "Fire", 
                      "traits": "Confident, generous, loyal", 
                      "description": "Leo is represented by the lion, symbolizing courage and leadership. People with this sign often have a natural flair for drama and creativity.",
                      "emoji": "♌"},
            "Virgo": {"start": (8, 23), "end": (9, 22), "element": "Earth", 
                      "traits": "Analytical, precise, helpful", 
                      "description": "Virgo is associated with meticulousness and service. Those born under this sign are often detail-oriented, practical, and devoted to self-improvement.",
                      "emoji": "♍"},
            "Libra": {"start": (9, 23), "end": (10, 22), "element": "Air", 
                      "traits": "Balanced, diplomatic, social", 
                      "description": "Libra is symbolized by the scales, representing balance and harmony. People with this sign often have a strong sense of justice and value relationships.",
                      "emoji": "♎"},
            "Scorpio": {"start": (10, 23), "end": (11, 21), "element": "Water", 
                      "traits": "Passionate, resourceful, brave", 
                      "description": "Scorpio is associated with intensity and transformation. Those born under this sign are often determined, passionate, and perceptive.",
                      "emoji": "♏"},
            "Sagittarius": {"start": (11, 22), "end": (12, 21), "element": "Fire", 
                      "traits": "Optimistic, adventurous, independent", 
                      "description": "Sagittarius is represented by the archer, symbolizing aspiration and exploration. People with this sign often love travel, learning, and philosophical discussions.",
                      "emoji": "♐"},
            "Capricorn": {"start": (12, 22), "end": (1, 19), "element": "Earth", 
                      "traits": "Disciplined, responsible, self-controlled", 
                      "description": "Capricorn is associated with ambition and discipline. Those born under this sign are often hardworking, patient, and practical.",
                      "emoji": "♑"},
            "Aquarius": {"start": (1, 20), "end": (2, 18), "element": "Air", 
                      "traits": "Progressive, original, independent", 
                      "description": "Aquarius is known for innovation and humanitarianism. People with this sign are often forward-thinking, unconventional, and value intellectual stimulation.",
                      "emoji": "♒"},
            "Pisces": {"start": (2, 19), "end": (3, 20), "element": "Water", 
                      "traits": "Compassionate, artistic, intuitive", 
                      "description": "Pisces is symbolized by the fish, representing connection to the spiritual realm. Those born under this sign are often creative, empathetic, and dreamy.",
                      "emoji": "♓"}
        }
        
        # Find the zodiac sign
        for sign, info in zodiac_signs.items():
            start_month, start_day = info["start"]
            end_month, end_day = info["end"]
            
            # Handle cases that span year boundary (like Capricorn)
            if start_month > end_month:
                if (month == start_month and day >= start_day) or (month == end_month and day <= end_day) or (month > start_month) or (month < end_month):
                    result = {"sign": sign, "element": info["element"], "traits": info["traits"], 
                             "description": info["description"], "emoji": info["emoji"]}
                    break
            else:
                if (month == start_month and day >= start_day) or (month == end_month and day <= end_day) or (start_month < month < end_month):
                    result = {"sign": sign, "element": info["element"], "traits": info["traits"], 
                             "description": info["description"], "emoji": info["emoji"]}
                    break
        else:
            return jsonify({"error": "Could not determine zodiac sign"})
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/horoscope', methods=['GET'])
def get_horoscope():
    sign = request.args.get('sign', '').lower()
    day = request.args.get('day', 'today')
    
    # Validate sign
    valid_signs = ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo', 
                  'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces']
    
    if (sign not in valid_signs):
        return jsonify({"error": "Invalid zodiac sign"}), 400
    
    # Validate day
    valid_days = ['yesterday', 'today', 'tomorrow']
    if day not in valid_days:
        return jsonify({"error": "Day must be yesterday, today, or tomorrow"}), 400
    
    # Log detailed diagnostic info for debugging
    print(f"Trying to fetch horoscope for {sign} ({day})...")
    
    try:
        # First, try with the Aztro API which is known to be reliable
        aztro_url = "https://aztro.sameerkumar.website/"
        aztro_params = {"sign": sign, "day": day}
        print(f"Making request to Aztro API: {aztro_url}")
        response = requests.post(aztro_url, params=aztro_params)
        
        if response.status_code == 200:
            print("Aztro API request successful")
            response_data = response.json()
            
            # Add Vedic astrology information
            vedic_info = get_vedic_astrology_info(sign)
            response_data.update({
                "vedic_astrology": vedic_info
            })
            
            return jsonify(response_data)
        else:
            print(f"Aztro API returned status code: {response.status_code}")
            
            # Try generated response as a backup
            current_date = datetime.now().strftime("%B %d, %Y")
            sign_data = get_sign_data(sign)
            
            # Generate a fallback horoscope response
            fallback_data = {
                "description": f"Today is a good day to embrace your {sign_data['element']} element. Focus on your {sign_data['traits'].split(', ')[0].lower()} nature.",
                "compatibility": sign_data.get("compatibility", get_compatible_sign(sign)),
                "mood": "Reflective",
                "lucky_number": str(((datetime.now().day + ord(sign[0])) % 9) + 1),
                "lucky_time": f"{(datetime.now().hour % 12) + 1}:{datetime.now().minute:02d} {('AM' if datetime.now().hour < 12 else 'PM')}",
                "current_date": current_date,
                "vedic_astrology": get_vedic_astrology_info(sign)
            }
            
            return jsonify(fallback_data)
            
    except Exception as e:
        print(f"Error fetching horoscope: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Helper function for Vedic astrology information
def get_vedic_astrology_info(western_sign):
    # Mapping from Western to Vedic zodiac signs (approximately)
    vedic_mapping = {
        "aries": "Pisces",  # or early Aries
        "taurus": "Aries",
        "gemini": "Taurus",
        "cancer": "Gemini",
        "leo": "Cancer",
        "virgo": "Leo",
        "libra": "Virgo",
        "scorpio": "Libra",
        "sagittarius": "Scorpio",
        "capricorn": "Sagittarius",
        "aquarius": "Capricorn",
        "pisces": "Aquarius"
    }
    
    # Sanskrit names for Vedic zodiac signs:
    sanskrit_names = {
        "Aries": "Mesha",
        "Taurus": "Vrishabha",
        "Gemini": "Mithuna",
        "Cancer": "Karka",
        "Leo": "Simha",
        "Virgo": "Kanya",
        "Libra": "Tula",
        "Scorpio": "Vrishchika",
        "Sagittarius": "Dhanu",
        "Capricorn": "Makara",
        "Aquarius": "Kumbha",
        "Pisces": "Meena"
    }
    
    # Get corresponding Vedic sign
    vedic_sign = vedic_mapping.get(western_sign.lower(), "Unknown")
    sanskrit_name = sanskrit_names.get(vedic_sign, "Unknown")
    
    # Nakshatra information (simplified - in real calculations this depends on exact birth time)
    nakshatras = {
        "Aries": ["Ashwini", "Bharani", "Krittika"],
        "Taurus": ["Krittika", "Rohini", "Mrigashira"],
        "Gemini": ["Mrigashira", "Ardra", "Punarvasu"],
        "Cancer": ["Punarvasu", "Pushya", "Ashlesha"],
        "Leo": ["Magha", "Purva Phalguni", "Uttara Phalguni"],
        "Virgo": ["Uttara Phalguni", "Hasta", "Chitra"],
        "Libra": ["Chitra", "Swati", "Vishakha"],
        "Scorpio": ["Vishakha", "Anuradha", "Jyeshtha"],
        "Sagittarius": ["Mula", "Purva Ashadha", "Uttara Ashadha"],
        "Capricorn": ["Uttara Ashadha", "Shravana", "Dhanishta"],
        "Aquarius": ["Dhanishta", "Shatabhisha", "Purva Bhadrapada"],
        "Pisces": ["Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
    }
    
    # Get possible nakshatras for this sign
    possible_nakshatras = nakshatras.get(vedic_sign, ["Unknown"])
    
    # Calculate today's ruling planet based on weekday
    weekday = datetime.now().weekday()
    ruling_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    today_planet = ruling_planets[weekday]
    
    # Determine auspicious direction based on ruling planet
    auspicious_directions = {
        "Sun": "East",
        "Moon": "Northwest",
        "Mars": "South",
        "Mercury": "North",
        "Jupiter": "Northeast",
        "Venus": "Southeast",
        "Saturn": "West"
    }
    
    auspicious_direction = auspicious_directions.get(today_planet, "Unknown")
    
    # Collect Vedic astrology information
    vedic_info = {
        "vedic_sign": vedic_sign,
        "sanskrit_name": sanskrit_name,
        "possible_nakshatras": possible_nakshatras,
        "ruling_planet": get_vedic_ruling_planet(vedic_sign),
        "todays_planet": today_planet,
        "auspicious_direction": auspicious_direction,
        "vedic_element": get_vedic_element(vedic_sign),
        "vedic_quality": get_vedic_quality(vedic_sign)
    }
    
    return vedic_info

def get_vedic_ruling_planet(vedic_sign):
    ruling_planets = {
        "Aries": "Mars",
        "Taurus": "Venus",
        "Gemini": "Mercury",
        "Cancer": "Moon",
        "Leo": "Sun",
        "Virgo": "Mercury",
        "Libra": "Venus",
        "Scorpio": "Mars (traditionally) / Pluto (modern)",
        "Sagittarius": "Jupiter",
        "Capricorn": "Saturn",
        "Aquarius": "Saturn (traditionally) / Uranus (modern)",
        "Pisces": "Jupiter (traditionally) / Neptune (modern)"
    }
    return ruling_planets.get(vedic_sign, "Unknown")

def get_vedic_element(vedic_sign):
    elements = {
        "Aries": "Fire (Agni)",
        "Taurus": "Earth (Prithvi)",
        "Gemini": "Air (Vayu)",
        "Cancer": "Water (Jala)",
        "Leo": "Fire (Agni)",
        "Virgo": "Earth (Prithvi)",
        "Libra": "Air (Vayu)",
        "Scorpio": "Water (Jala)",
        "Sagittarius": "Fire (Agni)",
        "Capricorn": "Earth (Prithvi)",
        "Aquarius": "Air (Vayu)",
        "Pisces": "Water (Jala)"
    }
    return elements.get(vedic_sign, "Unknown")

def get_vedic_quality(vedic_sign):
    qualities = {
        "Aries": "Movable (Chara)",
        "Taurus": "Fixed (Sthira)",
        "Gemini": "Dual (Dvisvabhava)",
        "Cancer": "Movable (Chara)",
        "Leo": "Fixed (Sthira)",
        "Virgo": "Dual (Dvisvabhava)",
        "Libra": "Movable (Chara)",
        "Scorpio": "Fixed (Sthira)",
        "Sagittarius": "Dual (Dvisvabhava)",
        "Capricorn": "Movable (Chara)",
        "Aquarius": "Fixed (Sthira)",
        "Pisces": "Dual (Dvisvabhava)"
    }
    return qualities.get(vedic_sign, "Unknown")

# Helper functions for fallback horoscope generation
def get_sign_data(sign):
    zodiac_data = {
        "aries": {"element": "Fire", "traits": "Independent, assertive, energetic"},
        "taurus": {"element": "Earth", "traits": "Patient, reliable, practical"},
        "gemini": {"element": "Air", "traits": "Adaptable, communicative, curious"},
        "cancer": {"element": "Water", "traits": "Intuitive, emotional, protective"},
        "leo": {"element": "Fire", "traits": "Confident, generous, loyal"},
        "virgo": {"element": "Earth", "traits": "Analytical, precise, helpful"},
        "libra": {"element": "Air", "traits": "Balanced, diplomatic, social"},
        "scorpio": {"element": "Water", "traits": "Passionate, resourceful, brave"},
        "sagittarius": {"element": "Fire", "traits": "Optimistic, adventurous, independent"},
        "capricorn": {"element": "Earth", "traits": "Disciplined, responsible, self-controlled"},
        "aquarius": {"element": "Air", "traits": "Progressive, original, independent"},
        "pisces": {"element": "Water", "traits": "Compassionate, artistic, intuitive"}
    }
    return zodiac_data.get(sign.lower(), {"element": "Unknown", "traits": "Mysterious"})

def get_compatible_sign(sign):
    compatibility = {
        "aries": "Libra",
        "taurus": "Scorpio",
        "gemini": "Sagittarius",
        "cancer": "Capricorn",
        "leo": "Aquarius",
        "virgo": "Pisces",
        "libra": "Aries",
        "scorpio": "Taurus",
        "sagittarius": "Gemini",
        "capricorn": "Cancer",
        "aquarius": "Leo",
        "pisces": "Virgo"
    }
    return compatibility.get(sign.lower(), "Gemini")

@app.route('/api/huggingface/generate', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
        
    try:
        # Call Hugging Face API for image generation
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"}
        
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt}
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to generate image"}), response.status_code
            
        # The response will be the binary image data
        image_bytes = response.content
        
        # Convert to base64 for sending to frontend
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        return jsonify({
            "image": f"data:image/jpeg;base64,{image_base64}"
        })
        
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/huggingface/test', methods=['GET'])
def test_huggingface_api():
    try:
        # Simple test prompt
        test_prompt = "a small test image of a star"
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"}
        
        # Make a test request
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": test_prompt}
        )
        
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "message": "API key is valid and working"
            })
        elif response.status_code == 401:
            return jsonify({
                "status": "error",
                "message": "Invalid API key"
            }), 401
        else:
            return jsonify({
                "status": "error",
                "message": f"API test failed with status code: {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Error testing API key",
            "error": str(e)
        }), 500

# Helper function to get unique event types and assign colors
def get_event_types_with_colors():
    db_path = os.path.join(app.root_path, 'astronomy.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT type FROM events')
    types = [row['type'] for row in cursor.fetchall()]
    conn.close()
    
    # Assign consistent colors to event types
    colors = ["#FF5733", "#33A8FF", "#33FF57", "#FF33A8", "#A833FF", "#FFD700", "#4682B4", "#FF6347", "#2E8B57", "#9932CC"]
    return {event_type: colors[i % len(colors)] for i, event_type in enumerate(types)}

if __name__ == '__main__':
    app.run(debug=True)
