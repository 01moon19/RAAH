import streamlit as st
import googlemaps
import pandas as pd
from datetime import datetime, timedelta
import joblib
from sklearn.preprocessing import StandardScaler
import polyline
import time as time_lib  # Renaming to avoid conflicts with time from datetime
import matplotlib.pyplot as plt
from test import get_google_maps_traffic_data, calculate_endpoint, adjust_signal_timing, convert_traffic_duration_to_seconds

# Load the model and scaler
rf_model = joblib.load('./models/congestion_model.pkl')
scaler = joblib.load('./models/scaler.pkl')

# Function to get real-time traffic data
def get_traffic_data(origin, destination, departure_time, api_key):
    gmaps = googlemaps.Client(key=api_key)
    directions_result = gmaps.directions(
        origin, destination, mode="driving", departure_time=departure_time, traffic_model="best_guess"
    )
    
    route_info = directions_result[0]['legs'][0]
    duration_in_traffic = route_info['duration_in_traffic']['value']
    distance = route_info['distance']['value']
    duration = route_info['duration']['value']
    
    start_location = route_info['start_location']
    end_location = route_info['end_location']
    
    encoded_polyline = directions_result[0]['overview_polyline']['points']
    path = polyline.decode(encoded_polyline)
    
    return {
        'origin': origin,
        'destination': destination,
        'distance_meters': distance,
        'duration_seconds': duration,
        'duration_in_traffic_seconds': duration_in_traffic,
        'start_location': (start_location['lat'], start_location['lng']),
        'end_location': (end_location['lat'], end_location['lng']),
        'path': path,
        'timestamp': datetime.now()
    }

# Function to convert seconds to hours, minutes, and seconds
def convert_seconds(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return hours, minutes, seconds

# Traffic signal control based on congestion
def adjust_signal_duration(predicted_congestion):
    base_green_time = 30  # Base green light duration in seconds
    max_green_time = 90   # Maximum green light duration in seconds
    min_green_time = 10   # Minimum green light duration in seconds

    low_congestion_threshold = 10  # Predicted congestion duration in seconds
    high_congestion_threshold = 60

    if predicted_congestion < low_congestion_threshold:
        green_time = min_green_time
    elif predicted_congestion > high_congestion_threshold:
        green_time = max_green_time
    else:
        green_time = base_green_time + (predicted_congestion / high_congestion_threshold) * (max_green_time - base_green_time)

    return green_time

# Function to display traffic signals
def display_traffic_signals(signal_states):
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown(f"<div style='text-align: center;'><h2>{'🟢' if signal_states['0'] == 'green' else '🟡' if signal_states['0'] == 'yellow' else '🔴'} Light 1 (North)</h2></div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>⬆️</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown(f"<div style='text-align: center;'><h2>{'🟢' if signal_states['270'] == 'green' else '🟡' if signal_states['270'] == 'yellow' else '🔴'} Light 4 (West)</h2></div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>⬅️</h2>", unsafe_allow_html=True)

    with col3:
        st.markdown(f"<div style='text-align: center;'><h2>{'🟢' if signal_states['90'] == 'green' else '🟡' if signal_states['90'] == 'yellow' else '🔴'} Light 2 (East)</h2></div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>➡️</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown(f"<div style='text-align: center;'><h2>{'🟢' if signal_states['180'] == 'green' else '🟡' if signal_states['180'] == 'yellow' else '🔴'} Light 3 (South)</h2></div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>⬇️</h2>", unsafe_allow_html=True)

# Function to simulate synchronized signal changes
def simulate_signals(api_key, crossroad_coords):
    signal_states = {'0': 'red', '90': 'red', '180': 'red', '270': 'red'}
    road_bearings = [0, 90, 180, 270]
    signal_display = st.empty()

    while True:
        signal_timings = []
        traffic_durations = []

        for bearing in road_bearings:
            road_endpoint = calculate_endpoint(crossroad_coords, bearing, distance=500)
            traffic_data = get_google_maps_traffic_data(api_key, str(crossroad_coords[0]) + "," + str(crossroad_coords[1]), str(road_endpoint[0]) + "," + str(road_endpoint[1]))
            
            if traffic_data:
                signal_duration = adjust_signal_timing(traffic_data)
                signal_timings.append(signal_duration)
                traffic_duration_seconds = convert_traffic_duration_to_seconds(traffic_data)
                traffic_durations.append(traffic_duration_seconds)
            else:
                signal_timings.append(20)
                traffic_durations.append(0)

        road_info = list(zip(traffic_durations, signal_timings, road_bearings))
        road_info.sort(key=lambda x: (-x[0], -x[1]))

        for traffic_duration, signal_duration, bearing in road_info:
            signal_states = {k: 'red' for k in signal_states}
            signal_states[str(bearing)] = 'green'

            with signal_display.container():
                display_traffic_signals(signal_states)
            st.write(f"Green light for road at bearing {bearing}°, duration: {signal_duration} seconds")
            time_lib.sleep(signal_duration)

            signal_states[str(bearing)] = 'yellow'
            with signal_display.container():
                display_traffic_signals(signal_states)
            st.write(f"Yellow light for road at bearing {bearing}°")
            time_lib.sleep(7)

        signal_states = {k: 'red' for k in signal_states}
        with signal_display.container():
            display_traffic_signals(signal_states)
        st.write("Red lights for all roads")
        time_lib.sleep(5)

# Function to ensure valid future time intervals for traffic predictions
def get_future_time_intervals():
    now = datetime.now()
    if now.hour >= 22:  # If the current time is after 10 PM, start from the next day
        start_time = now.replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=1)
    else:
        start_time = now if now.hour >= 6 else now.replace(hour=6, minute=0, second=0, microsecond=0)
    end_time = start_time.replace(hour=22)

    # Time intervals (e.g., every hour)
    time_intervals = [start_time + timedelta(hours=i) for i in range((end_time - start_time).seconds // 3600 + 1)]
    return time_intervals

# Streamlit app layout
st.set_page_config(page_title="Raah: Traffic Management System", layout="wide")
st.title("Raah: Traffic Congestion Prediction and Signal Simulation")

api_key = st.text_input("Enter Google Maps API Key", type="password")

# Traffic Congestion Prediction Section
with st.container():
    st.header("Traffic Congestion Prediction")
    origin = st.text_input("Enter Origin", "Times Square, New York, NY")
    destination = st.text_input("Enter Destination", "Central Park, New York, NY")
    departure_date = st.date_input("Choose Departure Date", datetime.now())
    departure_time = st.time_input("Choose Departure Time", datetime.now().time())

    if st.button("Predict Congestion"):
        if api_key:
            departure_datetime = datetime.combine(departure_date, departure_time)
            traffic_data = get_traffic_data(origin, destination, departure_datetime, api_key)

            st.write("Traffic Data:")
            st.write(f"Origin: {traffic_data['origin']}")
            st.write(f"Destination: {traffic_data['destination']}")
            st.write(f"Distance: {traffic_data['distance_meters'] / 1000:.2f} km")
            st.write(f"Duration: {traffic_data['duration_seconds'] // 60} minutes")
            st.write(f"Duration in Traffic: {traffic_data['duration_in_traffic_seconds'] // 60} minutes")
        else:
            st.warning("Please enter a valid API key.")

        
        # Display the map with the route and traffic conditions
        st.subheader("Route Map")
    
        # Create a DataFrame for the map with the decoded path (polyline)
        path_data = pd.DataFrame(traffic_data['path'], columns=['lat', 'lon'])
        
        # Plot the map with the route
        st.map(path_data)

# Traffic Signal Control Section
with st.container():
    st.header("Traffic Signal Control")
    crossroad_coords = st.text_input("Enter Crossroad Coordinates (latitude, longitude)", "28.6139, 77.2090")

    if st.button("Start Signal Simulation"):
        if api_key and crossroad_coords:
            try:
                lat, lon = map(float, crossroad_coords.split(","))
                simulate_signals(api_key, (lat, lon))
            except ValueError:
                st.error("Invalid coordinates format. Please enter in 'latitude,longitude' format.")
        else:
            st.warning("Please enter valid inputs.")

# Traffic Prediction Section
with st.container():
    st.header("Traffic Prediction")
    source = st.text_input("Enter Source Location", value="Delhi, India")
    destination = st.text_input("Enter Destination Location", value="Noida, India")

    # Button to trigger traffic prediction
    if st.button('Predict Traffic'):
        # Get future time intervals for checking traffic
        time_intervals = get_future_time_intervals()

        # Store traffic congestion levels
        traffic_conditions = []

        # Fetch directions and traffic info for different times of day
        gmaps = googlemaps.Client(key=api_key)
        for time in time_intervals:
            try:
                directions_result = gmaps.directions(
                    source,
                    destination,
                    mode="driving",
                    departure_time=time,
                    traffic_model="best_guess"
                )
                # Extract travel time in traffic (in seconds)
                travel_time = directions_result[0]['legs'][0]['duration_in_traffic']['value']
                traffic_conditions.append(travel_time / 60)  # Convert to minutes
            except Exception as e:
                st.error(f"Error fetching traffic data: {e}")
                break

        if traffic_conditions:
            # Plot traffic congestion vs. time of day
            times_of_day = [t.strftime("%I %p") for t in time_intervals]

            plt.figure(figsize=(10, 6))
            plt.plot(times_of_day, traffic_conditions, marker='o', color='b', linestyle='-', markersize=5)
            plt.xlabel('Time of Day')
            plt.ylabel('Travel Time (minutes)')
            plt.title(f'Traffic Congestion: {source} to {destination}')
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()

            # Display plot in Streamlit
            st.pyplot(plt)
