# Use Starlette directly to avoid the FastHTML import errors
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
import uvicorn
import logging
import base64

import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("night_sky")

# Load environment variables
load_dotenv()

# Create templates directory
import os
os.makedirs("templates", exist_ok=True)

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# API constants and authentication
API_URL = "https://api.astronomyapi.com/api/v2/bodies/positions"

# Get the full auth token directly - this is the approach from the example
AUTH_TOKEN = os.getenv('ASTRONOMY_API_AUTH_TOKEN')

# Log auth status (safely)
if AUTH_TOKEN:
    logger.info(f"Using full AUTH_TOKEN from .env file (starts with: {AUTH_TOKEN[:8]}...)")
else:
    logger.warning("AUTH_TOKEN not found in .env, trying APP_ID/APP_SECRET instead")
    APP_ID = os.getenv('ASTRONOMY_API_APP_ID')
    APP_SECRET = os.getenv('ASTRONOMY_API_APP_SECRET')
    if APP_ID and APP_SECRET:
        logger.info(f"API Credentials loaded - APP_ID: {APP_ID[:4]}... and APP_SECRET")
    else:
        logger.error("No valid API credentials found in .env file!")

# Check if the symbol images exist in root directory and copy them to static folder if needed
def setup_static_files():
    for planet in ["mercury", "venus", "mars", "jupiter", "saturn"]:
        src_file = f"symbol_{planet}.png"
        dest_dir = "static"
        dest_file = os.path.join(dest_dir, src_file)
        
        # If file exists in root but not in static folder, copy it
        if os.path.exists(src_file) and not os.path.exists(dest_file):
            logger.info(f"Copying {src_file} to static folder")
            import shutil
            shutil.copy(src_file, dest_file)

# Setup static files
setup_static_files()

# Planet data with icon URLs - now using local files
PLANETS = [
    {"name": "mercury", "icon": "/static/symbol_mercury.png"},
    {"name": "venus", "icon": "/static/symbol_venus.png"},
    {"name": "mars", "icon": "/static/symbol_mars.png"},
    {"name": "jupiter", "icon": "/static/symbol_jupiter.png"},
    {"name": "saturn", "icon": "/static/symbol_saturn.png"}
]

# Set up templates
templates = Jinja2Templates(directory="templates")

# Create base template
with open("templates/base.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Night Sky Planets{% endblock %}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <script src="https://unpkg.com/htmx.org@1.9.2"></script>
    <style>
        :root {
            --background-color: #1a1b26;
            --text-color: #c0caf5;
            --card-bg: #f5f5f7;
            --card-text: #2e3440;
            --card-shadow: rgba(0, 0, 0, 0.1);
            --header-bg: #2f3546;
            --header-text: #c0caf5;
            --accent-color: #7aa2f7;
            --border-radius: 12px;
        }
        
        body {
            background-color: var(--background-color);
            color: var(--text-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, sans-serif;
            line-height: 1.5;
        }
        
        .header {
            background-color: var(--header-bg);
            border-radius: var(--border-radius);
            padding: 2rem;
            margin-bottom: 2rem;
            text-align: center;
            color: var(--header-text);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .header h1 {
            margin-top: 0;
            margin-bottom: 0.75rem;
            font-weight: 700;
            color: white;
        }
        
        .header p {
            margin-bottom: 0.5rem;
            opacity: 0.9;
        }
        
        .header .date {
            color: white;
            font-size: 1.1rem;
            font-weight: 500;
        }
        
        .planet-card {
            background-color: var(--card-bg);
            color: var(--card-text);
            border-radius: var(--border-radius);
            padding: 1.25rem 1.5rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 2px 8px var(--card-shadow);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            border-left: 4px solid var(--accent-color);
        }
        
        .planet-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 12px var(--card-shadow);
        }
        
        .planet-icon {
            width: 28px;
            height: 28px;
            vertical-align: middle;
            margin-right: 0.75rem;
        }
        
        .planet-info {
            display: flex;
            align-items: center;
        }
        
        .planet-name {
            font-weight: 600;
            font-size: 1.15rem;
        }
        
        .planet-details {
            margin-left: auto;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }
        
        .planet-altitude {
            font-weight: 700;
            color: var(--accent-color);
            font-size: 1.25rem;
            letter-spacing: -0.5px;
        }
        
        .planet-direction {
            color: #666;
            font-size: 0.9rem;
            margin-top: 0.2rem;
        }

        .loading {
            text-align: center;
            margin: 2.5rem;
            color: var(--text-color);
            font-size: 1.1rem;
        }
        
        .container {
            max-width: 680px;
            padding: 2.5rem 1.5rem;
        }
        
        .no-planets {
            background-color: var(--card-bg);
            color: var(--card-text);
            border-radius: var(--border-radius);
            padding: 1.75rem;
            text-align: center;
            box-shadow: 0 2px 8px var(--card-shadow);
            font-size: 1.1rem;
        }
    </style>
</head>
<body>
    <main class="container">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
    """)

# Create home template
with open("templates/index.html", "w") as f:
    f.write("""
{% extends "base.html" %}

{% block title %}Night Sky Planets{% endblock %}

{% block content %}
<div>
    <div class="header">
        <h1>Tonight's Visible Planets</h1>
        <p class="date">{{ today }}</p>
    </div>
    
    <div id="planets-container" hx-get="/planets" hx-trigger="load" hx-swap="innerHTML">
        <div class="loading">
            <p>Scanning the night sky...</p>
        </div>
    </div>
</div>
{% endblock %}
    """)

# Create planets template
with open("templates/planets.html", "w") as f:
    f.write("""
{% if planets %}
    {% for planet in planets %}
    <div class="planet-card">
        <div class="planet-info">
            <img src="{{ planet.icon }}" class="planet-icon" alt="{{ planet.name }} icon">
            <span class="planet-name">{{ planet.name }}</span>
            <div class="planet-details">
                <span class="planet-altitude">{{ planet.altitude|round(1) }}°</span>
                <span class="planet-direction">{{ planet.direction }}</span>
            </div>
        </div>
    </div>
    {% endfor %}
{% else %}
    <div class="no-planets">
        <p>No planets clearly visible tonight.</p>
    </div>
{% endif %}
    """)

def get_compass_direction(azimuth):
    """Convert azimuth in degrees to compass direction (N, NE, E, etc.)"""
    # Define direction ranges (each direction covers 45 degrees)
    directions = [
        {'name': 'N', 'min': 337.5, 'max': 22.5},  # North wraps around 0°
        {'name': 'NE', 'min': 22.5, 'max': 67.5},
        {'name': 'E', 'min': 67.5, 'max': 112.5},
        {'name': 'SE', 'min': 112.5, 'max': 157.5},
        {'name': 'S', 'min': 157.5, 'max': 202.5},
        {'name': 'SW', 'min': 202.5, 'max': 247.5},
        {'name': 'W', 'min': 247.5, 'max': 292.5},
        {'name': 'NW', 'min': 292.5, 'max': 337.5}
    ]
    
    # Handle the special case for North (which wraps around 0°)
    if azimuth >= 337.5 or azimuth < 22.5:
        return 'N'
    
    # Check each direction range
    for direction in directions:
        if direction['min'] <= azimuth < direction['max']:
            return direction['name']
    
    # Fallback (should never happen with valid azimuth)
    return '?'

def get_visible_planets(lat, lon, date, time="22:00:00"):
    """Get planets that are visible from the given location and time"""
    logger.info(f"Fetching planet data for location ({lat}, {lon}) on {date} at {time}")
    
    # Construct params for single API request
    params = {
        "latitude": lat,
        "longitude": lon,
        "from_date": date,
        "to_date": date,
        "elevation": 0,
        "time": time
    }

    visible_planets = []
    all_planets_data = []
    planet_names = ["mercury", "venus", "mars", "jupiter", "saturn"]
    
    try:
        # Use the AUTH_TOKEN directly from .env - exactly as shown in the example
        if AUTH_TOKEN:
            headers = {
                'Authorization': AUTH_TOKEN,
                'Content-Type': 'application/json'
            }
            logger.info("Using direct Authorization token from .env file")
        else:
            logger.info("No AUTH_TOKEN found, constructing from APP_ID/APP_SECRET")
            APP_ID = os.getenv('ASTRONOMY_API_APP_ID')
            APP_SECRET = os.getenv('ASTRONOMY_API_APP_SECRET')
            auth_string = f"{APP_ID}:{APP_SECRET}"
            encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
            headers = {
                'Authorization': f'Basic {encoded_auth}',
                'Content-Type': 'application/json'
            }
        
        # Make API request
        logger.info(f"Making request to {API_URL} with params: {params}")
        logger.info(f"Authorization header starts with: {headers['Authorization'][:15]}...")
        
        response = requests.get(API_URL, params=params, headers=headers)
        
        # Log the full response for debugging
        logger.info(f"API Response Status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"API Error: {response.text}")
            return []
        
        # Parse data
        data = response.json()
        logger.info("API response parsed successfully")
        
        # Extract relevant data for each planet we're interested in
        rows = data['data']['table']['rows']
        
        # Log all planet IDs from the API for debugging
        logger.info("Planet IDs from API:")
        for row in rows:
            entry_id = row.get('entry', {}).get('id', '')
            entry_name = row.get('entry', {}).get('name', '')
            logger.info(f"ID: {entry_id}, Name: {entry_name}")
        
        # Process each planet in the response
        for row in rows:
            planet_id = row.get('entry', {}).get('id', '').lower()
            
            if planet_id in planet_names:
                planet_name = row['entry']['name']
                cells = row.get('cells', [])
                
                if cells and len(cells) > 0:
                    # Get altitude from the first (and only) cell
                    altitude = cells[0]['position']['horizontal']['altitude']['degrees']
                    
                    # Get azimuth for compass direction
                    azimuth = float(cells[0]['position']['horizontal']['azimuth']['degrees'])
                    compass_direction = get_compass_direction(azimuth)
                    
                    # Convert to float
                    try:
                        altitude = float(altitude)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert altitude to float: {altitude}")
                        continue
                    
                    # Log all planet data
                    planet_info = {
                        'name': planet_name,
                        'altitude': altitude,
                        'azimuth': azimuth,
                        'direction': compass_direction
                    }
                    all_planets_data.append(planet_info)
                    
                    # Add to visible planets if above horizon threshold
                    if altitude > 5:
                        # Find matching icon from our PLANETS list using lowercase comparison
                        icon = next((p['icon'] for p in PLANETS if p['name'].lower() == planet_id.lower()), None)
                        
                        # Debug log the icon matching
                        logger.info(f"Looking for icon for {planet_id} (name: {planet_name}) - Found: {icon is not None}")
                        
                        visible_planets.append({
                            'name': planet_name,
                            'icon': icon,
                            'altitude': altitude,
                            'azimuth': azimuth,
                            'direction': compass_direction
                        })
    
    except Exception as e:
        logger.error(f"Error in API call: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
    # Log planet visibility data
    logger.info("------- PLANET ALTITUDES AND DIRECTIONS -------")
    for planet in all_planets_data:
        visible_status = "VISIBLE" if planet['altitude'] > 5 else "Not visible"
        logger.info(f"{planet['name']}: {planet['altitude']:.1f}° - {planet['direction']} - {visible_status}")
    logger.info("-------------------------------")

    return visible_planets

async def homepage(request):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    latitude = os.getenv('LATITUDE', '51.758375')
    longitude = os.getenv('LONGITUDE', '-1.034740')
    
    logger.info(f"Homepage requested from {request.client.host}")
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "today": today,
        "latitude": latitude,
        "longitude": longitude
    })

async def planets(request):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    latitude = os.getenv('LATITUDE', '51.758375')
    longitude = os.getenv('LONGITUDE', '-1.034740')
    
    logger.info(f"Planet data requested from {request.client.host}")
    
    visible_planets = get_visible_planets(latitude, longitude, today)
    
    if visible_planets:
        logger.info(f"Returning {len(visible_planets)} visible planets")
    else:
        logger.info("No planets visible tonight")
    
    return templates.TemplateResponse("planets.html", {
        "request": request,
        "planets": visible_planets
    })

# Create Starlette app with routes
app = Starlette(
    debug=True,
    routes=[
        Route('/', homepage),
        Route('/planets', planets),
        Mount('/static', StaticFiles(directory="static"), name="static")
    ]
)

if __name__ == "__main__":
    logger.info("Starting Night Sky Planet Viewer")
    # Use environment variables for port if available (for Vercel compatibility)
    port = int(os.environ.get("PORT", 8000))
    # Run with hot reload in development, but bind to 0.0.0.0 for compatibility
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True) 