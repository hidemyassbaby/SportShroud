# rugby_automation.py
import json
import urllib.request
from datetime import datetime, timedelta
import os
import re
from zoneinfo import ZoneInfo

# Remote URLs
SCHEDULE_URL = "https://raw.githubusercontent.com/hidemyassbaby/SportShroud/refs/heads/main/schedule/rugbyschedule.json"
CHANNELS_URL = "https://raw.githubusercontent.com/hidemyassbaby/SportShroud/refs/heads/main/Streams/channellist.json"
RUGBY_MENU_PATH = "Main Menu/sportsmenus/rugby.json"
MATCHES_FOLDER = "Main Menu/sportsmenus/matches"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/hidemyassbaby/SportShroud/refs/heads/main"

# Utility functions
def fetch_json(url):
    with urllib.request.urlopen(url) as response:
        return json.load(response)

def slugify(title):
    return re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')

# Ensure output directories exist
os.makedirs(os.path.dirname(RUGBY_MENU_PATH), exist_ok=True)
os.makedirs(MATCHES_FOLDER, exist_ok=True)

# Load data
schedule = fetch_json(SCHEDULE_URL)
channels_data = fetch_json(CHANNELS_URL)
channels = channels_data.get("streams", [])
now = datetime.now(ZoneInfo("Pacific/Auckland"))

menu = []
active_slugs = []

for match in schedule:
    title = match["title"]
    slug = slugify(title)
    match_path = f"{MATCHES_FOLDER}/{slug}.json"

    start = datetime.fromisoformat(match["start_time"]).replace(tzinfo=ZoneInfo("Pacific/Auckland"))
    end = datetime.fromisoformat(match.get("end_time")).replace(tzinfo=ZoneInfo("Pacific/Auckland")) if match.get("end_time") else start + timedelta(hours=2, minutes=30)
    appear = start - timedelta(minutes=30)

    if appear <= now < end:
        active_slugs.append(slug)
        streams = []

        for name in match["channels"]:
            name_lower = name.lower()
            for stream in channels:
                if isinstance(stream, dict) and name_lower in stream.get("title", "").lower():
                    streams.append(stream)

        with open(match_path, "w") as mf:
            json.dump(streams, mf, indent=2)

        menu.append({
            "name": title,
            "url": f"{GITHUB_RAW_BASE}/{match_path.replace(' ', '%20')}",
            "thumb": match.get("thumb", ""),
            "plot": match.get("plot", "")
        })

if not menu:
    menu = [{
        "name": "No live games at the moment",
        "url": ""
    }]

with open(RUGBY_MENU_PATH, "w") as f:
    json.dump(menu, f, indent=2)

for file in os.listdir(MATCHES_FOLDER):
    if file.endswith(".json"):
        slug = file.replace(".json", "")
        if slug not in active_slugs:
            os.remove(os.path.join(MATCHES_FOLDER, file))

print("✅ Rugby menu updated at:", datetime.now().isoformat())
