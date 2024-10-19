import pandas as pd

file_path = './data/traffic_data.csv'

# Define the expected column names (since there are no headers in the file)
columns = ['origin', 'destination', 'distance_meters', 'duration_seconds', 'duration_in_traffic_seconds', 'timestamp']

try:
    # Read the CSV, skip bad lines (too many or too few columns)
    data = pd.read_csv(file_path, header=None, names=columns, on_bad_lines='skip')

    # Convert the timestamp to datetime
    data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')

    # Extract useful features from the timestamp
    data['hour'] = data['timestamp'].dt.hour
    data['day'] = data['timestamp'].dt.day
    data['month'] = data['timestamp'].dt.month
    data['weekday'] = data['timestamp'].dt.weekday
    data['is_weekend'] = (data['weekday'] >= 5).astype(int)  # Weekend flag

    # Save the processed data to a new CSV file
    processed_file_path = './data/preprocessed_traffic_data.csv'
    data.to_csv(processed_file_path, index=False)

    print("Preprocessing completed. Processed data saved to:", processed_file_path)

except Exception as e:
    print(f"Error processing the file: {e}")

