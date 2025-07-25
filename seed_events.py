from pymongo import MongoClient, errors
from datetime import datetime, timedelta
import random
import sys

# MongoDB connection string
MONGO_URI = "mongodb://localhost:27017/"

# Connect to MongoDB with error handling
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # Force connection on a request as the connect=True parameter of MongoClient seems to be useless here
except errors.ServerSelectionTimeoutError as err:
    print(f"Error: Could not connect to MongoDB at {MONGO_URI}")
    print(f"Details: {err}")
    sys.exit(1)

try:
    db = client["events"]
    events_collection = db["parties"]
except Exception as e:
    print("Error: Could not access the 'events' database or 'parties' collection.")
    print(f"Details: {e}")
    sys.exit(1)

event_categories = [
    "Party",
    "Concerts",
    "Open Mic",
    "Stand Up",
    "Other"
]

places = {
    "Kochi": "Lulu Mall",
    "Bangalore": "Cubbon Park",
    "Mumbai": "Marine Drive",
    "Delhi": "India Gate"
}

sample_events = [
    # Party
    {"Name": "Beach Bash", "Category": "Party", "Place": "Kochi"},
    {"Name": "Neon Night", "Category": "Party", "Place": "Bangalore"},
    {"Name": "Rooftop Revelry", "Category": "Party", "Place": "Mumbai"},
    {"Name": "Bollywood Blast", "Category": "Party", "Place": "Delhi"},
    # Concerts
    {"Name": "Rock Legends Live", "Category": "Concerts", "Place": "Mumbai"},
    {"Name": "Jazz Under the Stars", "Category": "Concerts", "Place": "Kochi"},
    {"Name": "EDM Extravaganza", "Category": "Concerts", "Place": "Bangalore"},
    {"Name": "Classical Evenings", "Category": "Concerts", "Place": "Delhi"},
    # Open Mic
    {"Name": "Poetry Slam", "Category": "Open Mic", "Place": "Delhi"},
    {"Name": "Comedy Open Mic", "Category": "Open Mic", "Place": "Bangalore"},
    {"Name": "Acoustic Sessions", "Category": "Open Mic", "Place": "Kochi"},
    {"Name": "Storytellers' Night", "Category": "Open Mic", "Place": "Mumbai"},
    # Stand Up
    {"Name": "Laugh Riot", "Category": "Stand Up", "Place": "Bangalore"},
    {"Name": "Stand Up Saturday", "Category": "Stand Up", "Place": "Kochi"},
    {"Name": "Comedy Carnival", "Category": "Stand Up", "Place": "Delhi"},
    {"Name": "Mic Drop", "Category": "Stand Up", "Place": "Mumbai"},
    # Other
    {"Name": "Artisan Market", "Category": "Other", "Place": "Kochi"},
    {"Name": "Food Fest", "Category": "Other", "Place": "Delhi"},
    {"Name": "Tech Expo", "Category": "Other", "Place": "Bangalore"},
    {"Name": "Book Fair", "Category": "Other", "Place": "Mumbai"},
]

def random_future_datetime():
    days = random.randint(1, 60)
    hours = random.randint(10, 22)
    return datetime.now() + timedelta(days=days, hours=hours)

def random_distance():
    return random.randint(1, 20)

def seed_events():
    try:
        events_collection.delete_many({})  # Clear existing events
        for event in sample_events:
            event_datetime = random_future_datetime()
            event_doc = {
                "Name": event["Name"],
                "Date": event_datetime,
                "Place": event["Place"],
                "Distance": random_distance(),
                "Category": event["Category"],
                "Checkpoint": places[event["Place"]]
            }
            events_collection.insert_one(event_doc)
        print(f"Inserted {len(sample_events)} sample events into 'events.parties'.")
    except Exception as e:
        print("Error: Failed to insert events.")
        print(f"Details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    seed_events() 