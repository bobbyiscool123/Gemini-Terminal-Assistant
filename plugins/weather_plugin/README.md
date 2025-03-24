# Weather Plugin

A plugin for Terminal AI Assistant that provides weather information and forecasts.

## Features

- Get current weather for any location
- Get detailed weather reports including temperature, humidity, wind, etc.
- View 5-day weather forecasts
- Configure default location and units (metric/imperial)
- Works with or without an API key (uses mock data if no API key provided)

## Installation

1. Ensure the plugin directory exists in your Terminal AI Assistant installation
2. For real weather data, obtain a free API key from [OpenWeatherMap](https://openweathermap.org/)
3. Add your API key to the `.env` file:
   ```
   OPENWEATHERMAP_API_KEY=your_api_key_here
   ```

## Commands

The plugin provides the following commands:

- `weather [location] [--detailed]` - Get current weather for a location
- `forecast [location] [days=N]` - Get a weather forecast for a location
- `weatherconfig [set location=CITY] [set units=metric/imperial]` - Configure plugin settings

## Examples

### Current Weather

```
> weather London
Weather in London:
🌡️ 22.5°C (Feels like: 21.8°C)
☁️ Clear sky
💧 Humidity: 65%
💨 Wind: 3.6 m/s
```

### Detailed Weather

```
> weather New York --detailed
Detailed Weather for New York - 2025-03-24 23:45
------------------------------------------------------
🌡️ Temperature: 18.3°C (Feels like: 17.5°C)
☁️ Conditions: Partly cloudy
💧 Humidity: 72%
📊 Barometric Pressure: 1008 hPa
💨 Wind: 4.2 m/s from WSW
👁️ Visibility: 10.0 km
☁️ Cloud Cover: 45%
🌅 Sunrise: 06:42
🌇 Sunset: 19:23
------------------------------------------------------
```

### Weather Forecast

```
> forecast Tokyo days=3
Weather Forecast for Tokyo:

Monday (2025-03-25):
  Conditions: Clear sky
  Temperature: 19.5°C (High: 22.3°C, Low: 16.2°C)
  🌅 Morning (08:00): Clear sky, 18.2°C
  ☀️ Afternoon (15:00): Few clouds, 22.1°C
  🌙 Evening (21:00): Clear sky, 17.5°C

Tuesday (2025-03-26):
  Conditions: Broken clouds
  Temperature: 18.7°C (High: 21.4°C, Low: 15.9°C)
  🌅 Morning (09:00): Broken clouds, 17.6°C
  ☀️ Afternoon (15:00): Broken clouds, 21.2°C
  🌙 Evening (21:00): Light rain, 16.3°C

Wednesday (2025-03-27):
  Conditions: Few clouds
  Temperature: 20.1°C (High: 23.8°C, Low: 16.5°C)
  🌅 Morning (08:00): Clear sky, 18.9°C
  ☀️ Afternoon (14:00): Few clouds, 23.5°C
  🌙 Evening (20:00): Few clouds, 18.2°C
```

### Configuration

```
> weatherconfig
Current configuration:
Default location: London
Units: metric (temperature in °C)

> weatherconfig set location=Paris
Default location set to: Paris

> weatherconfig set units=imperial
Units set to: imperial (temperature in °F)
```

## Mock Data

If no API key is provided, the plugin will use mock data to demonstrate its functionality. This is useful for testing or if you don't want to sign up for an API key.

The mock data provides realistic weather information, including:
- Current weather conditions with temperature, humidity, wind, etc.
- Time-appropriate data (different temperatures for morning/afternoon/evening)
- 5-day forecasts with varying conditions

## Note

This plugin uses the [OpenWeatherMap API](https://openweathermap.org/). The free tier allows up to 1,000 API calls per day, which should be more than sufficient for personal use. 