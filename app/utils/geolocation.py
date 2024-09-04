import requests
import os
from dotenv import load_dotenv 

load_dotenv()
GEOLOCATION_TOKEN  = os.getenv('GEOLOCATION_TOKEN')

def get_geolocation(ip_address: str):    
    # IPinfo API endpoint
    url = f"https://ipinfo.io/{ip_address}/json?token={GEOLOCATION_TOKEN}"
    
    # Make the request to the API
    response = requests.get(url)
    
    # Parse the response to JSON
    data = response.json()
    
    # Extract relevant information
    location = data.get("loc", "Location not found").split(',')
    city = data.get("city", "City not found")
    region = data.get("region", "Region not found")
    country = data.get("country", "Country not found")
    
    return {
        "ip": ip_address,
        "city": city,
        "region": region,
        "country": country,
        "latitude": location[0] if len(location) > 1 else "N/A",
        "longitude": location[1] if len(location) > 1 else "N/A"
    }
