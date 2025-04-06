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
    print(f"📱 Fetching JSON from: {url}")
    with urllib.request.urlopen(url) as response:
        return json.load(response)

def slugify(title):
    return re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')

# Ensure output directories exist
os.makedirs(os.path.dirname(RUGBY_MENU_PATH), exist_ok=True)
os.makedirs(MATCHES_FOLDER, exist_ok=True)

# Load data
print("🔄 Loading schedule and channels...")
schedule = fetch_json(SCHEDULE_URL)
channels_data = fetch_json(CHANNELS_URL)
channels = channels_data.get("streams", [])
now = datetime.now(ZoneInfo("Pacific/Auckland"))
print(f"🕒 Current NZ time: {now.isoformat()}")

menu = []
active_slugs = []

for match in schedule:
    title = match["title"]
    slug = slugify(title)
    match_path = f"{MATCHES_FOLDER}/{slug}.json"
    print(f"⚙️ Processing match: {title}")

    start = datetime.fromisoformat(match["start_time"]).replace(tzinfo=ZoneInfo("Pacific/Auckland"))
    end = datetime.fromisoformat(match.get("end_time")).replace(tzinfo=ZoneInfo("Pacific/Auckland")) if match.get("end_time") else start + timedelta(hours=2, minutes=30)
    appear = start - timedelta(minutes=30)
    print(f"⏰ Starts at: {start}, Appears at: {appear}, Ends at: {end}")

    if appear <= now < end:
        print(f"✅ Match is live or upcoming, including in menu: {title}")
        active_slugs.append(slug)
        streams = []

        for name in match["channels"]:
            name_lower = name.lower()
            for stream in channels:
                if isinstance(stream, dict) and name_lower in stream.get("title", "").lower():
                    streams.append({
                        "name": stream.get("title", "Stream"),
                        "url": stream.get("url", ""),
                        "thumb": stream.get("thumb", ""),
                        "plot": stream.get("plot", "")
                    })

        # Group streams by name to allow fallback
        grouped = {}
        for s in streams:
            key = s["name"]
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(s)

        # Convert to fallback stream list
        fallback_streams = []
        for title, group in grouped.items():
            fallback_streams.append({
                "name": title,
                "fallback": group
            })

        with open(match_path, "w") as mf:
            json.dump(fallback_streams, mf, indent=2)
            print(f"📁 Wrote streams to {match_path} with {len(fallback_streams)} entries")

        # Include match info from schedule for menu
        menu.append({
            "name": match.get("title", ""),
            "url": f"{GITHUB_RAW_BASE}/{match_path.replace(' ', '%20')}",
            "thumb": match.get("thumb", ""),
            "plot": match.get("plot", "")
        })
    else:
        print(f"⏳ Skipping match: {title} (Not yet visible or already ended)")

if not menu:
    print("❌ No live games found. Writing fallback message.")
    menu = [{
        "name": "No live games at the moment",
        "url": ""
    }]

with open(RUGBY_MENU_PATH, "w") as f:
    json.dump(menu, f, indent=2)
    print(f"✅ Updated rugby menu with {len(menu)} item(s)")

for file in os.listdir(MATCHES_FOLDER):
    if file.endswith(".json"):
        slug = file.replace(".json", "")
        if slug not in active_slugs:
            os.remove(os.path.join(MATCHES_FOLDER, file))
            print(f"🗑️ Removed expired match file: {file}")

print("✅ Rugby menu automation completed at:", datetime.now().isoformat())
