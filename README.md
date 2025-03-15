# Night Sky Planet Viewer

A Starlette application that shows which planets are visible in the night sky tonight.

## Features

- Displays planets visible to the naked eye
- Shows planet icons, altitude information, and compass directions
- Uses real-time astronomy data
- Clean, night-sky themed UI

## Setup

1. Clone this repository
2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
3. Update the `.env` file with your API credentials:
   ```
   ASTRONOMY_API_APP_ID=your_app_id_here
   ASTRONOMY_API_APP_SECRET=your_app_secret_here
   # Or alternatively use the direct authorization token:
   ASTRONOMY_API_AUTH_TOKEN=your_auth_token_here
   LATITUDE=51.758375  # Default coordinates (update with your location)
   LONGITUDE=-1.034740
   ```

   Get your API credentials by signing up at [Astronomy API](https://astronomyapi.com/).

4. Run the application:
   ```
   python app.py
   ```
5. Open your browser to `http://localhost:8000`

## How It Works

The application queries the Astronomy API to get the positions of Mercury, Venus, Mars, Jupiter, and Saturn. It then checks if each planet is above the horizon at a visible altitude (above 5 degrees) and displays the results.

The application shows both the altitude of each planet and its compass direction (N, NE, E, SE, S, SW, W, NW), calculated from the azimuth value provided by the API.

The UI is built with Starlette, Jinja2 templates, and HTMX for dynamic content loading without complex JavaScript frameworks.

## Customizing

- To change your location, update the `LATITUDE` and `LONGITUDE` values in the `.env` file
- The application checks for planet visibility at 10:00 PM local time by default

## Deployment

This application is ready to deploy to Vercel through GitHub:

1. Push this repository to GitHub
2. Connect your Vercel account to your GitHub repository
3. Configure environment variables in Vercel (ASTRONOMY_API_AUTH_TOKEN, LATITUDE, LONGITUDE)
4. Deploy!

For detailed deployment instructions, see the [DEPLOY.md](DEPLOY.md) file. 