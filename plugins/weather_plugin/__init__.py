"""
Weather Plugin
A plugin for Terminal AI Assistant that provides weather information
"""
from utils.plugin_manager import Plugin
from typing import Dict, List, Callable, Optional
import requests
import json
import os
from datetime import datetime

class WeatherPlugin(Plugin):
    """Weather Plugin provides weather information from OpenWeatherMap API"""
    name = "weather_plugin"
    description = "Get weather information for any location"
    version = "1.0.0"
    
    def __init__(self, terminal_assistant=None):
        super().__init__(terminal_assistant)
        self.api_key = os.getenv('OPENWEATHERMAP_API_KEY', '')
        self.config_file = "weather_plugin.json"
        self.default_location = "London"
        self.units = "metric"  # metric or imperial
        self.load_config()
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        # Check if we have an API key
        if not self.api_key:
            print("Warning: No OpenWeatherMap API key found. Set OPENWEATHERMAP_API_KEY in .env file.")
            print("You can get a free API key from https://openweathermap.org/")
            print("The plugin will use mock data until an API key is provided.")
        return True
    
    def load_config(self):
        """Load plugin configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.default_location = config.get('default_location', self.default_location)
                    self.units = config.get('units', self.units)
            except Exception as e:
                print(f"Error loading weather plugin config: {str(e)}")
    
    def save_config(self):
        """Save plugin configuration"""
        config = {
            'default_location': self.default_location,
            'units': self.units
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving weather plugin config: {str(e)}")
    
    def get_commands(self) -> Dict[str, Callable]:
        """Get commands provided by this plugin"""
        return {
            "weather": self.weather_command,
            "forecast": self.forecast_command,
            "weatherconfig": self.config_command
        }
    
    def get_completions(self) -> Dict[str, List[str]]:
        """Get command completions provided by this plugin"""
        return {
            "weather": ["current", "detailed"],
            "forecast": ["today", "week"],
            "weatherconfig": ["set", "view"]
        }
    
    def weather_command(self, *args) -> str:
        """Get current weather for a location
        Usage: weather [location] [--detailed]"""
        detailed = False
        location = self.default_location
        
        # Parse arguments
        for arg in args:
            if arg.lower() == "--detailed" or arg.lower() == "detailed":
                detailed = True
            elif not arg.startswith("--"):
                location = arg
        
        # Get weather data
        data = self.get_weather_data(location)
        if not data:
            return f"Failed to get weather data for {location}"
        
        # Format the response
        if detailed:
            return self.format_detailed_weather(data, location)
        else:
            return self.format_simple_weather(data, location)
    
    def forecast_command(self, *args) -> str:
        """Get weather forecast for a location
        Usage: forecast [location] [days=5]"""
        location = self.default_location
        days = 5
        
        # Parse arguments
        for arg in args:
            if arg.lower().startswith("days="):
                try:
                    days = int(arg.split("=")[1])
                    if days < 1:
                        days = 1
                    elif days > 16:
                        days = 16  # API limit
                except ValueError:
                    pass
            elif not arg.startswith("--"):
                location = arg
        
        # Get forecast data
        data = self.get_forecast_data(location, days)
        if not data:
            return f"Failed to get forecast data for {location}"
        
        # Format the response
        return self.format_forecast(data, location, days)
    
    def config_command(self, *args) -> str:
        """Configure weather plugin settings
        Usage: weatherconfig [set location=CITY] [set units=metric/imperial]"""
        if not args:
            return f"Current configuration:\n" \
                   f"Default location: {self.default_location}\n" \
                   f"Units: {self.units} (temperature in {self.get_temp_unit()})"
        
        action = args[0].lower()
        
        if action == "set" and len(args) >= 2:
            setting = args[1].lower()
            
            if setting.startswith("location="):
                self.default_location = setting[9:]
                self.save_config()
                return f"Default location set to: {self.default_location}"
                
            elif setting.startswith("units="):
                units = setting[6:].lower()
                if units in ["metric", "imperial"]:
                    self.units = units
                    self.save_config()
                    return f"Units set to: {self.units} (temperature in {self.get_temp_unit()})"
                else:
                    return "Units must be 'metric' or 'imperial'"
        
        return "Usage: weatherconfig [set location=CITY] [set units=metric/imperial]"
    
    def get_weather_data(self, location: str) -> Optional[Dict]:
        """Get current weather data for a location"""
        if not self.api_key:
            # Return mock data if no API key
            return self.get_mock_weather_data(location)
            
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': self.units
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching weather data: {str(e)}")
            return None
    
    def get_forecast_data(self, location: str, days: int = 5) -> Optional[Dict]:
        """Get forecast data for a location"""
        if not self.api_key:
            # Return mock data if no API key
            return self.get_mock_forecast_data(location, days)
            
        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': self.units,
                'cnt': min(days * 8, 40)  # 8 data points per day (3-hour intervals)
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching forecast data: {str(e)}")
            return None
    
    def format_simple_weather(self, data: Dict, location: str) -> str:
        """Format weather data into a simple string"""
        try:
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            description = data['weather'][0]['description']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            
            return f"Weather in {location}:\n" \
                   f"🌡️ {temp:.1f}{self.get_temp_unit()} (Feels like: {feels_like:.1f}{self.get_temp_unit()})\n" \
                   f"☁️ {description.capitalize()}\n" \
                   f"💧 Humidity: {humidity}%\n" \
                   f"💨 Wind: {wind_speed} {self.get_speed_unit()}"
        except Exception as e:
            return f"Error formatting weather data: {str(e)}"
    
    def format_detailed_weather(self, data: Dict, location: str) -> str:
        """Format weather data into a detailed string"""
        try:
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            description = data['weather'][0]['description']
            humidity = data['main']['humidity']
            pressure = data['main']['pressure']
            wind_speed = data['wind']['speed']
            wind_dir = self.get_wind_direction(data['wind'].get('deg', 0))
            visibility = data.get('visibility', 0) / 1000  # Convert to km
            clouds = data.get('clouds', {}).get('all', 0)
            
            sunrise = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')
            sunset = datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')
            
            return f"Detailed Weather for {location} - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n" \
                   f"------------------------------------------------------\n" \
                   f"🌡️ Temperature: {temp:.1f}{self.get_temp_unit()} (Feels like: {feels_like:.1f}{self.get_temp_unit()})\n" \
                   f"☁️ Conditions: {description.capitalize()}\n" \
                   f"💧 Humidity: {humidity}%\n" \
                   f"📊 Barometric Pressure: {pressure} hPa\n" \
                   f"💨 Wind: {wind_speed} {self.get_speed_unit()} from {wind_dir}\n" \
                   f"👁️ Visibility: {visibility:.1f} km\n" \
                   f"☁️ Cloud Cover: {clouds}%\n" \
                   f"🌅 Sunrise: {sunrise}\n" \
                   f"🌇 Sunset: {sunset}\n" \
                   f"------------------------------------------------------"
        except Exception as e:
            return f"Error formatting detailed weather data: {str(e)}"
    
    def format_forecast(self, data: Dict, location: str, days: int) -> str:
        """Format forecast data into a string"""
        try:
            result = [f"Weather Forecast for {location}:"]
            
            # Group forecast data by day
            day_forecasts = {}
            for item in data['list']:
                dt = datetime.fromtimestamp(item['dt'])
                day_key = dt.strftime('%Y-%m-%d')
                
                if day_key not in day_forecasts:
                    day_forecasts[day_key] = []
                
                day_forecasts[day_key].append(item)
            
            # Format each day (limit to requested days)
            for i, (day_key, items) in enumerate(list(day_forecasts.items())[:days]):
                day_date = datetime.strptime(day_key, '%Y-%m-%d')
                day_name = day_date.strftime('%A')
                
                # Calculate average temperature and find most common weather
                avg_temp = sum(item['main']['temp'] for item in items) / len(items)
                weather_counts = {}
                for item in items:
                    w = item['weather'][0]['description']
                    weather_counts[w] = weather_counts.get(w, 0) + 1
                
                most_common_weather = max(weather_counts.items(), key=lambda x: x[1])[0]
                
                # Calculate high and low
                high_temp = max(item['main']['temp'] for item in items)
                low_temp = min(item['main']['temp'] for item in items)
                
                result.append(f"\n{day_name} ({day_key}):")
                result.append(f"  Conditions: {most_common_weather.capitalize()}")
                result.append(f"  Temperature: {avg_temp:.1f}{self.get_temp_unit()} (High: {high_temp:.1f}{self.get_temp_unit()}, Low: {low_temp:.1f}{self.get_temp_unit()})")
                
                # Add morning, afternoon, evening forecast if available
                times = [(8, "🌅 Morning"), (14, "☀️ Afternoon"), (20, "🌙 Evening")]
                for hour, label in times:
                    # Find the closest forecast to the target hour
                    closest = min(items, key=lambda x: abs(datetime.fromtimestamp(x['dt']).hour - hour))
                    closest_dt = datetime.fromtimestamp(closest['dt'])
                    if abs(closest_dt.hour - hour) <= 3:  # Within 3 hours of target
                        result.append(f"  {label} ({closest_dt.strftime('%H:%M')}): {closest['weather'][0]['description'].capitalize()}, {closest['main']['temp']:.1f}{self.get_temp_unit()}")
            
            return "\n".join(result)
                
        except Exception as e:
            return f"Error formatting forecast data: {str(e)}"
    
    def get_temp_unit(self) -> str:
        """Get temperature unit based on units setting"""
        return "°C" if self.units == "metric" else "°F"
    
    def get_speed_unit(self) -> str:
        """Get speed unit based on units setting"""
        return "m/s" if self.units == "metric" else "mph"
    
    def get_wind_direction(self, degrees: float) -> str:
        """Convert wind direction in degrees to cardinal direction"""
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                      'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def get_mock_weather_data(self, location: str) -> Dict:
        """Get mock weather data for testing"""
        return {
            "coord": {"lon": -0.1257, "lat": 51.5085},
            "weather": [{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}],
            "base": "stations",
            "main": {
                "temp": 22.5,
                "feels_like": 21.8,
                "temp_min": 20.6,
                "temp_max": 23.9,
                "pressure": 1012,
                "humidity": 65
            },
            "visibility": 10000,
            "wind": {"speed": 3.6, "deg": 250},
            "clouds": {"all": 0},
            "dt": int(datetime.now().timestamp()),
            "sys": {
                "type": 2,
                "id": 2019646,
                "country": "GB",
                "sunrise": int((datetime.now().replace(hour=5, minute=30)).timestamp()),
                "sunset": int((datetime.now().replace(hour=20, minute=30)).timestamp())
            },
            "timezone": 3600,
            "id": 2643743,
            "name": location,
            "cod": 200
        }
    
    def get_mock_forecast_data(self, location: str, days: int) -> Dict:
        """Get mock forecast data for testing"""
        now = datetime.now()
        
        # Generate forecast list with 8 entries per day (3-hour intervals)
        forecast_list = []
        for day in range(days):
            for hour in [0, 3, 6, 9, 12, 15, 18, 21]:
                forecast_time = now.replace(hour=hour)
                forecast_time = forecast_time.replace(day=now.day + day)
                
                # Vary temperature by time of day
                if hour < 6:
                    temp = 15 + day * 0.5  # Early morning
                elif hour < 12:
                    temp = 18 + day * 0.5  # Morning
                elif hour < 18:
                    temp = 22 + day * 0.5  # Afternoon
                else:
                    temp = 17 + day * 0.5  # Evening
                
                # Add some randomness
                import random
                temp += random.uniform(-2, 2)
                
                # Alternate between weather conditions
                if day % 2 == 0:
                    if hour < 12:
                        weather = {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}
                    else:
                        weather = {"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02d"}
                else:
                    if hour < 15:
                        weather = {"id": 803, "main": "Clouds", "description": "broken clouds", "icon": "04d"}
                    else:
                        weather = {"id": 500, "main": "Rain", "description": "light rain", "icon": "10d"}
                
                forecast_list.append({
                    "dt": int(forecast_time.timestamp()),
                    "main": {
                        "temp": temp,
                        "feels_like": temp - 1,
                        "temp_min": temp - 2,
                        "temp_max": temp + 2,
                        "pressure": 1012,
                        "humidity": 65
                    },
                    "weather": [weather],
                    "clouds": {"all": 20 if "clear" in weather["description"] else 70},
                    "wind": {"speed": 3.6, "deg": 250},
                    "visibility": 10000,
                    "pop": 0.2 if "rain" in weather["description"] else 0,
                    "sys": {"pod": "d" if 6 <= hour < 18 else "n"},
                    "dt_txt": forecast_time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return {
            "cod": "200",
            "message": 0,
            "cnt": len(forecast_list),
            "list": forecast_list,
            "city": {
                "id": 2643743,
                "name": location,
                "coord": {"lat": 51.5085, "lon": -0.1257},
                "country": "GB",
                "population": 1000000,
                "timezone": 3600,
                "sunrise": int((now.replace(hour=5, minute=30)).timestamp()),
                "sunset": int((now.replace(hour=20, minute=30)).timestamp())
            }
        } 