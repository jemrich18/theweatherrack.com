import requests
import ephem
from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder
import pytz


def geocode_location(location_string):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': location_string,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'WeatherRack/1.0'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        if data:
            return {
                'latitude': float(data[0]['lat']),
                'longitude': float(data[0]['lon']),
                'display_name': data[0]['display_name']
            }
        return None
    except Exception:
        return None


def get_weather_data(latitude, longitude):
    url = 'https://api.open-meteo.com/v1/forecast'
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'daily': [
            'temperature_2m_max',
            'temperature_2m_min',
            'precipitation_probability_max',
            'windspeed_10m_max',
            'windgusts_10m_max',
        ],
        'hourly': [
            'surface_pressure',
            'temperature_2m',
        ],
        'temperature_unit': 'fahrenheit',
        'windspeed_unit': 'mph',
        'forecast_days': 10,
        'timezone': 'auto'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data
    except Exception:
        return None


import ephem
from datetime import datetime, date

def get_moon_data(latitude, longitude, date_str):
    try:
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=latitude, lng=longitude)
        tz = pytz.timezone(tz_name)
        utc_now = datetime.strptime(date_str, '%Y-%m-%d')
        offset = tz.utcoffset(utc_now)

        observer = ephem.Observer()
        observer.lat = str(latitude)
        observer.lon = str(longitude)
        observer.date = date_str

        moon = ephem.Moon()
        sun = ephem.Sun()

        try:
            moonrise = (observer.next_rising(moon).datetime() + offset).strftime('%H:%M')
        except ephem.NeverUpError:
            moonrise = 'Never rises'
        except ephem.AlwaysUpError:
            moonrise = 'Always up'

        try:
            moonset = (observer.next_setting(moon).datetime() + offset).strftime('%H:%M')
        except ephem.NeverUpError:
            moonset = 'Never sets'
        except ephem.AlwaysUpError:
            moonset = 'Always up'

        try:
            sunrise = (observer.next_rising(sun).datetime() + offset).strftime('%H:%M')
        except Exception:
            sunrise = 'N/A'

        try:
            sunset = (observer.next_setting(sun).datetime() + offset).strftime('%H:%M')
        except Exception:
            sunset = 'N/A'

        return {
            'sunrise': sunrise,
            'sunset': sunset,
            'moonrise': moonrise,
            'moonset': moonset,
        }

    except Exception:
        return None


def parse_time(time_str):
    if not time_str or time_str in ('Never rises', 'Never sets', 'Always up', 'N/A'):
        return None
    try:
        t = datetime.strptime(time_str, '%H:%M')
        return t.hour * 60 + t.minute
    except Exception:
        return None


def score_moon(sunrise, sunset, moonrise, moonset):
    score = 0
    reasons = []

    sunrise_mins = parse_time(sunrise)
    sunset_mins = parse_time(sunset)
    moonrise_mins = parse_time(moonrise)
    moonset_mins = parse_time(moonset)

    if sunrise_mins and moonrise_mins:
        gap = abs(sunrise_mins - moonrise_mins)
        if gap <= 60:
            score += 8
            reasons.append(f'Moonrise near sunrise ({gap} min gap)')
        elif gap <= 120:
            score += 4
            reasons.append(f'Moonrise within 2hrs of sunrise')

    if sunset_mins and moonset_mins:
        gap = abs(sunset_mins - moonset_mins)
        if gap <= 60:
            score += 7
            reasons.append(f'Moonset near sunset ({gap} min gap)')
        elif gap <= 120:
            score += 3
            reasons.append(f'Moonset within 2hrs of sunset')

    if not reasons:
        reasons.append('Moon timing not favorable')

    return {'score': score, 'reasons': reasons}


def get_pressure_trend(hourly_pressure, day_index):
    """Get max pressure change over 6 hour windows for a given day"""
    start = day_index * 24
    end = start + 24
    day_pressure = hourly_pressure[start:end]

    if len(day_pressure) < 6:
        return 0

    max_change = 0
    for i in range(len(day_pressure) - 6):
        change = day_pressure[i + 6] - day_pressure[i]
        if abs(change) > abs(max_change):
            max_change = change
    return max_change


def score_day(day_data, day_index, hourly_pressure, avg_high_temp):
    score = 0
    reasons = []

    # --- Temperature Score (25 pts) ---
    temp_diff = avg_high_temp - day_data['temp_max']
    if temp_diff >= 15:
        score += 25
        reasons.append('Significantly below average temps')
    elif temp_diff >= 8:
        score += 18
        reasons.append('Below average temps')
    elif temp_diff >= 3:
        score += 10
        reasons.append('Slightly below average temps')
    else:
        score += 0
        reasons.append('Above average temps — deer less active')

    # --- Pressure Trend Score (25 pts) ---
    pressure_change = get_pressure_trend(hourly_pressure, day_index)

    if pressure_change <= -3:
        score += 25
        reasons.append(f'Rapid pressure drop ({pressure_change:.1f} hPa) — pre-front feed')
    elif pressure_change >= 3:
        score += 20
        reasons.append(f'Rapid pressure rise ({pressure_change:.1f} hPa) — post-front movement')
    elif pressure_change <= -1.5:
        score += 12
        reasons.append(f'Moderate pressure drop ({pressure_change:.1f} hPa)')
    elif pressure_change >= 1.5:
        score += 10
        reasons.append(f'Moderate pressure rise ({pressure_change:.1f} hPa)')
    else:
        score += 5
        reasons.append('Stable pressure')

    # --- Wind Speed Score (15 pts) ---
    wind = day_data['wind_max']
    if 5 <= wind <= 15:
        score += 15
        reasons.append(f'Ideal wind {wind} mph')
    elif wind < 5:
        score += 8
        reasons.append(f'Very light wind {wind} mph — scent risk')
    elif 15 < wind <= 25:
        score += 5
        reasons.append(f'Moderate wind {wind} mph')
    else:
        score += 0
        reasons.append(f'High wind {wind} mph — deer bedded')

    # --- Precipitation Score (10 pts) ---
    precip = day_data['precip_prob']
    if precip <= 10:
        score += 10
        reasons.append('Little to no rain')
    elif precip <= 30:
        score += 6
        reasons.append('Low chance of rain')
    elif precip <= 60:
        score += 3
        reasons.append('Moderate rain chance')
    else:
        score += 0
        reasons.append('High rain chance')

    # --- Rating Label ---
    if score >= 60:
        rating = 'Excellent'
    elif score >= 45:
        rating = 'Good'
    elif score >= 30:
        rating = 'Fair'
    else:
        rating = 'Poor'

    return {
        'score': score,
        'rating': rating,
        'reasons': reasons,
        'pressure_change': pressure_change
    }


def get_scored_forecast(latitude, longitude):
    data = get_weather_data(latitude, longitude)
    if not data:
        return None

    hourly_pressure = data['hourly']['surface_pressure']
    daily = data['daily']
    avg_temp = sum(daily['temperature_2m_max']) / len(daily['temperature_2m_max'])

    scored_days = []
    for i, date in enumerate(daily['time']):
        day_data = {
            'temp_max': daily['temperature_2m_max'][i],
            'temp_min': daily['temperature_2m_min'][i],
            'wind_max': daily['windspeed_10m_max'][i],
            'precip_prob': daily['precipitation_probability_max'][i],
        }

        weather_result = score_day(day_data, i, hourly_pressure, avg_temp)

        moon_data = get_moon_data(latitude, longitude, date)
        if moon_data:
            moon_result = score_moon(
                moon_data['sunrise'],
                moon_data['sunset'],
                moon_data['moonrise'],
                moon_data['moonset']
            )
        else:
            moon_result = {'score': 0, 'reasons': ['Moon data unavailable']}

        total_score = weather_result['score'] + moon_result['score']
        all_reasons = weather_result['reasons'] + moon_result['reasons']

        # Recalculate rating based on total score including moon
        if total_score >= 70:
            rating = 'Excellent'
        elif total_score >= 52:
            rating = 'Good'
        elif total_score >= 35:
            rating = 'Fair'
        else:
            rating = 'Poor'

        scored_days.append({
            'date': date,
            'temp_max': day_data['temp_max'],
            'temp_min': day_data['temp_min'],
            'wind_max': day_data['wind_max'],
            'precip_prob': day_data['precip_prob'],
            'score': total_score,
            'rating': rating,
            'reasons': all_reasons,
            'pressure_change': round(weather_result['pressure_change'], 1),
            'moonrise': moon_data['moonrise'] if moon_data else 'N/A',
            'moonset': moon_data['moonset'] if moon_data else 'N/A',
            'sunrise': moon_data['sunrise'] if moon_data else 'N/A',
            'sunset': moon_data['sunset'] if moon_data else 'N/A',
        })

    
    return scored_days