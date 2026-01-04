import requests
import time
import random
import threading

# IMPORTANT: Ensure this URL matches the port in your app.py file
BACKEND_URL = 'http://localhost:5001/api/v1/location_update'

def simulate_vehicle(vehicle_id, start_lat, start_lng):
    """Simulates a single vehicle sending GPS updates."""
    lat = start_lat
    lng = start_lng
    
    print(f"Starting simulation for Vehicle ID: {vehicle_id}...")

    while True:
        # Simulate movement with small random changes
        lat += (random.random() - 0.5) * 0.001
        lng += (random.random() - 0.5) * 0.001

        payload = {
            'vehicle_id': vehicle_id,
            'latitude': round(lat, 6),
            'longitude': round(lng, 6)
        }

        try:
            response = requests.post(BACKEND_URL, json=payload)
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status() 
            print(f"Vehicle {vehicle_id}: Location sent successfully. Lat: {payload['latitude']}, Lng: {payload['longitude']}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending data for Vehicle {vehicle_id}: {e}")

        # Send data every 5 seconds
        time.sleep(5)

if __name__ == '__main__':
    # --- THIS IS THE FIX ---
    # The starting coordinates have been updated to Hyderabad
    # so the markers will appear on the map.
    
    # Vehicle 1 starts in central Hyderabad
    thread1 = threading.Thread(target=simulate_vehicle, args=(1, 17.3850, 78.4867))
    
    # Vehicle 2 starts nearby
    thread2 = threading.Thread(target=simulate_vehicle, args=(2, 17.3900, 78.4800))
    
    # Start the threads
    thread1.start()
    thread2.start()
