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

# Setup static files - only run locally, not in Vercel
if not os.environ.get('VERCEL'):
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