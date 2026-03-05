# WeatherRack 🦌

A Django web application that analyzes weather patterns to help deer hunters identify the best days to hunt. WeatherRack scores a 10-day forecast for any hunting location based on the key environmental factors that drive deer movement.

## Features

- **User Accounts** — Register, login, and manage your profile
- **Hunting Area Management** — Save multiple hunting locations by name, automatically geocoded to coordinates
- **10-Day Forecast** — Pulled from Open-Meteo's free weather API
- **Hunt Score** — Each day is scored 0–105 based on conditions known to affect deer movement
- **Best Day Banner** — Instantly see your top hunting day at a glance
- **Moon Data** — Moonrise and moonset calculated astronomically using ephem
- **Responsive UI** — Dark, outdoors-themed interface that works on mobile

## Scoring System

Each day is scored across five factors:

| Factor | Max Points | Logic |
|---|---|---|
| Temperature | 25 | Days below the 10-day average score higher |
| Barometric Pressure | 25 | Rapid drops (pre-front) and rises (post-front) score highest |
| Wind Speed | 15 | Ideal range is 5–15 mph |
| Wind Direction | 15 | N/NW post-front winds score highest, S/SE winds score lowest |
| Precipitation | 10 | Lower chance of rain scores higher |
| Moon Timing | 15 | Moonrise/moonset close to sunrise/sunset scores higher |

**Ratings:**
- 🟢 **Excellent** — 70+ points
- 🟡 **Good** — 52–69 points  
- 🟠 **Fair** — 35–51 points
- 🔴 **Poor** — Under 35 points

## Tech Stack

- **Backend** — Django 6
- **Weather API** — [Open-Meteo](https://open-meteo.com/) (free, no key required)
- **Geocoding** — [Nominatim / OpenStreetMap](https://nominatim.org/) (free, no key required)
- **Moon Calculations** — [ephem](https://rhodesmill.org/ephem/) (local astronomical calculations)
- **Timezone Detection** — timezonefinder + pytz
- **Database** — PostgreSQL (production) / SQLite (development)
- **Deployment** — Railway
- **Package Manager** — uv

## Local Development

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

### Setup
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/weather-rack.git
cd weather-rack

# Create virtual environment
uv venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# Install dependencies
uv pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to view the app.

## Environment Variables

Create a `.env` file in the root directory:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

In production set:
```
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=your-postgres-url
```

## Project Structure
```
weather_rack/
├── hunt/                   # Main app
│   ├── templates/hunt/     # HTML templates
│   ├── models.py           # HuntingArea model
│   ├── views.py            # View logic
│   ├── urls.py             # URL routing
│   ├── forms.py            # Django forms
│   └── utils.py            # Weather, moon, and scoring logic
├── weather_rack/           # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── Procfile                # Railway/Gunicorn config
├── runtime.txt             # Python version
└── manage.py
```

## Roadmap

- [ ] Wind direction stand-preference (per hunting area)
- [ ] Whitetail rut phase overlay by region
- [ ] Email alerts for excellent forecast days
- [ ] Historical score tracking
- [ ] Mobile PWA support

## License

MIT License — free to use and modify.

## Acknowledgements

- Weather data provided by [Open-Meteo](https://open-meteo.com/)
- Geocoding by [Nominatim](https://nominatim.org/) © OpenStreetMap contributors
- Astronomical calculations by [ephem](https://rhodesmill.org/ephem/)