import os
import googlemaps
import pandas as pd
from datetime import datetime, timedelta
from itertools import combinations

# Define the directory paths
data_dir = './data'  # Ensure this points to your project's data directory

# Create the directories if they don't exist
os.makedirs(data_dir, exist_ok=True)


google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
gmaps = googlemaps.Client(key=google_maps_api_key)

# Function to fetch traffic data from the Google Maps Directions API
def get_traffic_data(origin, destination, departure_time='now'):
    directions_result = gmaps.directions(origin,
                                         destination,
                                         mode="driving",
                                         departure_time=departure_time,
                                         traffic_model="best_guess")
    
    # Extract useful information
    if directions_result:  # Check if any results were returned
        route_info = directions_result[0]['legs'][0]
        duration_in_traffic = route_info['duration_in_traffic']['value']  # Duration in seconds
        distance = route_info['distance']['value']  # Distance in meters
        duration = route_info['duration']['value']  # Normal duration (no traffic)

        # Extract arrival time
        arrival_time = datetime.now() + timedelta(seconds=duration_in_traffic)
        
        # Extract day of the week and is_weekend
        day_of_week = arrival_time.strftime("%A")  # Full name of the day
        is_weekend = int(day_of_week in ["Saturday", "Sunday"])  # 1 if weekend, else 0

        # Extract steps in the route
        route_steps = [step['html_instructions'] for step in route_info['steps']]

        return {
            'origin': origin,
            'destination': destination,
            'distance_meters': distance,
            'duration_seconds': duration,
            'duration_in_traffic_seconds': duration_in_traffic,
            'timestamp': datetime.now().isoformat(),  # Save timestamp in ISO format
            'arrival_time': arrival_time.isoformat(),
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'route_steps': route_steps
        }
    else:
        return None  # Return None if no results found

# List of Points of Interest (POIs) in New Delhi
pois = [
    "India Gate, Delhi, India",
    "Qutub Minar, Delhi, India",
    "Lotus Temple, Delhi, India",
    "Red Fort, Delhi, India",
    "Humayun's Tomb, Delhi, India",
    "Akshardham Temple, Delhi, India",
    "Connaught Place, Delhi, India",
    "Chandni Chowk, Delhi, India",
    "Raj Ghat, Delhi, India",
    "Jama Masjid, Delhi, India",
    "National Museum, Delhi, India",
    "Lodhi Garden, Delhi, India",
    "National Gallery of Modern Art, Delhi, India",
    "Parliament House, Delhi, India",
    "Presidential Palace (Rashtrapati Bhavan), Delhi, India",
    "Gurudwara Bangla Sahib, Delhi, India",
    "Dilli Haat, Delhi, India",
    "Saket Mall, Delhi, India",
    "Khan Market, Delhi, India",
    "Hauz Khas Village, Delhi, India",
    "Chhatarpur Temple, Delhi, India",
    "Kingdom of Dreams, Gurgaon, Delhi, India",
    "Sanjay Gandhi Transport Nagar, Delhi, India",
    "Nehru Planetarium, Delhi, India",
    "Shankar's International Dolls Museum, Delhi, India",
    "ISKCON Temple, Delhi, India",
    "Rashtrapati Bhavan Gardens, Delhi, India",
    "Delhi Zoo, Delhi, India",
    "Gurudwara Sis Ganj Sahib, Delhi, India",
    "Mahatma Gandhi Memorial, Delhi, India",
    "National Handicrafts and Handlooms Museum, Delhi, India",
    "Baha'i House of Worship (Lotus Temple), Delhi, India",
    "Tughlaqabad Fort, Delhi, India",
    "Feroz Shah Kotla Fort, Delhi, India",
    "Safdarjung's Tomb, Delhi, India",
    "Jantar Mantar, Delhi, India",
    "Shah Jahan Park, Delhi, India",
    "Connaught Place, Delhi, India",
    "Paharganj, Delhi, India",
    "Chandni Chowk, Delhi, India",
    "Pitampura TV Tower, Delhi, India",
    "Mundka Industrial Area, Delhi, India",
    "Dwarka Sector 21, Delhi, India",
    "Khan Market, Delhi, India",
    "Sarai Rohilla, Delhi, India",
    "Lajpat Nagar, Delhi, India",
    "Punjabi Bagh, Delhi, India",
    "Greater Kailash, Delhi, India",
    "Vasant Kunj, Delhi, India",
    "Noida Sector 18, Delhi, India",
    "Azadpur Mandi, Delhi, India",
    "Delhi Airport (Indira Gandhi International Airport), Delhi, India",
]

# Generate all combinations of origin-destination pairs
origin_dest_pairs = list(combinations(pois, 2))

# Define the CSV file path
traffic_data_file = os.path.join(data_dir, 'traffic_data.csv')

# Collect traffic data for each origin-destination pair
for origin, destination in origin_dest_pairs:
    try:
        traffic_data = get_traffic_data(origin, destination)
        
        if traffic_data:  # Proceed only if data was returned
            # Convert the traffic data to a DataFrame
            df = pd.DataFrame([traffic_data])
            
            # Write to CSV, checking if file already exists to handle header correctly
            if not os.path.isfile(traffic_data_file):
                df.to_csv(traffic_data_file, index=False)  # Write header for the first time
            else:
                df.to_csv(traffic_data_file, mode='a', header=False, index=False)  # Append without header

            print(f"Traffic data collected for {origin} to {destination}")

    except Exception as e:
        print(f"Error collecting data for {origin} to {destination}: {e}")

print("Traffic data collection completed.")

