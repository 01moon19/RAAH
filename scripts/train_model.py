import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import joblib

# Load the preprocessed data
data = pd.read_csv('./data/preprocessed_traffic_data.csv')

# Split data into features (X) and target variable (y)
X = data[['hour', 'day', 'month', 'weekday', 'is_weekend', 'distance_meters', 'duration_seconds']]
y = data['duration_in_traffic_seconds']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create and fit the scaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)  # Fit and transform the training data
X_test_scaled = scaler.transform(X_test)        # Transform the testing data

# Train the model
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train_scaled, y_train)

# Evaluate the model
y_pred = rf_model.predict(X_test_scaled)
mae = mean_absolute_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred, squared=False)

print(f'Mean Absolute Error: {mae}')
print(f'Root Mean Squared Error: {rmse}')

# Save the model and scaler
joblib.dump(rf_model, './models/congestion_model.pkl')  # Save the trained model
joblib.dump(scaler, './models/scaler.pkl')              # Save the scaler

