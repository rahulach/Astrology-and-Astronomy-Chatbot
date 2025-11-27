import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    NASA_API_KEY = os.environ.get('NASA_API_KEY') or "DEMO_KEY"
    PIXABAY_API_KEY = os.environ.get('PIXABAY_API_KEY') or "49653562-e59db92f385286c1ce93025e9"
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or "AIzaSyApQBcBBToCVhwCekgRoPFL6lB5CJrwJTI"
    # Add missing API keys
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY') or "your_openweathermap_api_key"
    ASTRONOMY_API_KEY = os.environ.get('ASTRONOMY_API_KEY') or "your_astronomy_api_key"

    def __init__(self):
        self.RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY_HERE"  # Get from RapidAPI.com
        self.HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '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')

    # API Endpoints
    NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
    NASA_IMAGE_SEARCH_URL = "https://images-api.nasa.gov/search"
    PIXABAY_API_URL = "https://pixabay.com/api/"
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
