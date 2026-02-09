import requests
import json

try:
    response = requests.get("http://localhost:8000/api/forecast/BBCA.JK/quick", timeout=5)
    data = response.json()
    
    print("Keys in response:", data.keys())
    if "forecast" in data:
        print("Keys in data['forecast']:", data["forecast"].keys())
        if "nextDayPrediction" in data["forecast"]:
            print("nextDayPrediction:", data["forecast"]["nextDayPrediction"])
        else:
            print("nextDayPrediction MISSING in data['forecast']")
    else:
        print("forecast key MISSING")

except Exception as e:
    print(f"Error: {e}")
