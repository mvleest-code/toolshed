import asyncio
import websockets
import json
import datetime
import requests
import os
import re  # For sanitizing file names
import ssl

# Mapping of ns values to their descriptions
ns_mapping = {
    101: "Line Events (counting and line crossing)",
    102: "Object Tracking",
    103: "Intrusion",
    104: "Loitering",
    105: "Tamper",
    106: "ObjectLeftRemoved",
    107: "Fall Duress",
    108: "Crowd",
    109: "Wrong Direction",
    110: "QRCode",
    111: "IO Output Record",
    112: "IO Input Record"
}

# Initialize a session for making HTTP requests
s = requests.Session()

# Configuration details Demo Account
branding = "c022"
accountId = "00142573"
auth_key = "c022~ffa2f40b92fccae2c518236d859cb7db"

# Create an SSL context that does not verify certificates
ssl_context = ssl._create_unverified_context()

def sanitize_filename(filename):
    # Replace or remove invalid characters for filenames
    return re.sub(r'[<>:"/\\|?*]+', '_', filename).strip()

def get_cameraids(branding, auth_key):
    url = f"https://{branding}.eagleeyenetworks.com/g/device/list"
    headers = {
        'Cookie': f'auth_key={auth_key}; videobank_sessionid={auth_key}'
    }
    response = requests.get(url, headers=headers)
    camera_data_list = response.json()
    bridge_ids = ["10033654", "1008312c"]  # Add your bridge IDs here
    camera_ids = [camera_data[1] for camera_data in camera_data_list if camera_data[3] == "camera" and any(bridge_id in bridge for bridge_id in bridge_ids for bridge in camera_data[4])]
    camera_names = {camera_data[1]: camera_data[2] for camera_data in camera_data_list if camera_data[3] == "camera" and "ATTD" in camera_data}
    print("Fetched camera ids, from bridge ids: ", bridge_ids)
    return camera_ids, camera_names

camera_ids, camera_names = get_cameraids(branding, auth_key)

# Ensure required log directories exist
os.makedirs("logs/stream", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# If none of the camera_ids are found, print an error message and exit
if not camera_names:
    print("None of the specified camera IDs were found.")
    exit()

# Dictionary to store last processed timestamp and max delay event for each camera
last_processed_timestamps = {cam_id: None for cam_id in camera_names}
max_delay_events = {cam_id: None for cam_id in camera_names}
event_counters = {cam_id: {} for cam_id in camera_names}
delays = {cam_id: [] for cam_id in camera_names}
ns_counts = {cam_id: {} for cam_id in camera_names}
processed_event_uuids = set()  # Set to track processed event UUIDs

# Function to log processed event UUID to a file
def log_processed_event_uuid(event_uuid):
    with open('logs/processed_event_uuids.log', 'a') as f:
        f.write(f"{event_uuid}\n")

# Function to connect to websocket and log events
async def connect_and_log(uri, ns_values):
    async with websockets.connect(uri, ping_interval=None, ssl=ssl_context) as websocket:
        # Prepare the message to be sent for all specified camera IDs
        message = {
            "cameras": {
                cam_id: {
                    "resource": ["pre", "event"],
                    "event": ["ALRS", "ANNT"]
                } for cam_id in camera_names
            }
        }
        message_json = json.dumps(message)
        print(f"Sending initial message for all cameras")
        
        # Open log files for each camera
        stream_logs = {
            cam_id: open(f"logs/stream/{sanitize_filename(name)}_{cam_id}_stream.log", "a") for cam_id, name in camera_names.items()
        }

        try:
            # Send the message
            await websocket.send(message_json)
            while True:
                # Wait for a response
                response = await websocket.recv()
                timestamp = datetime.datetime.now(datetime.timezone.utc)
                response_json = json.loads(response)

                # Log the response for each camera
                for cam_id in camera_names:
                    if "data" in response_json and cam_id in response_json["data"]:
                        cam_data = response_json["data"][cam_id]
                        log_event_data(cam_id, cam_data, timestamp, stream_logs)
        except websockets.ConnectionClosed:
            print("Connection closed")
        except json.JSONDecodeError:
            print("Failed to decode JSON from the response")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Close all log files
            for log_file in stream_logs.values():
                log_file.close()

def log_event_data(camera_id, cam_data, timestamp, stream_logs):
    stream_log = stream_logs[camera_id]
    stream_log.write(f"{timestamp.isoformat()} -- {json.dumps(cam_data)}\n")
    if "event" in cam_data:
        for event_type, event_data in cam_data["event"].items():
            if "ns" in event_data and event_data["ns"] in ns_mapping:
                handle_event(camera_id, event_data, timestamp)

def handle_event(camera_id, event_data, timestamp):
    ns_value = event_data["ns"]
    event_uuid = event_data.get("uuid")  # Extract the UUID (event ID) from the event data
    if not event_uuid:
        print(f"Event missing 'uuid'. Skipping.")
        return

    if event_uuid in processed_event_uuids:
        return  # Skip processing if this event UUID was already processed

    # Log the processed event UUID
    log_processed_event_uuid(event_uuid)
    processed_event_uuids.add(event_uuid)  # Add to the set of processed event UUIDs

    event_timestamp_str = event_data["timestamp"]
    event_timestamp = datetime.datetime.strptime(event_timestamp_str, "%Y%m%d%H%M%S.%f").replace(tzinfo=datetime.timezone.utc)

    # Skip if the event ID has been processed more than the limit
    if ns_value not in event_counters[camera_id]:
        event_counters[camera_id][ns_value] = 0

    # Allow processing only after 4 events for this namespace
    if event_counters[camera_id][ns_value] < 4:
        event_counters[camera_id][ns_value] += 1
        return  # Skip processing for this event

    # Proceed with processing if we have reached the limit
    if last_processed_timestamps[camera_id] and event_timestamp == last_processed_timestamps[camera_id]:
        return
    last_processed_timestamps[camera_id] = event_timestamp
    delay = (timestamp - event_timestamp).total_seconds()
    if delay < 0:
        return
    
    delays[camera_id].append(delay)
    if ns_value in ns_mapping:
        if ns_value not in ns_counts[camera_id]:
            ns_counts[camera_id][ns_value] = []
        ns_counts[camera_id][ns_value].append(delay)

    # Log data preparation
    min_delay = min(delays[camera_id]) if delays[camera_id] else 0
    max_delay = max(delays[camera_id]) if delays[camera_id] else 0
    avg_delay = sum(delays[camera_id]) / len(delays[camera_id]) if delays[camera_id] else 0

    # Update max delay events
    if not max_delay_events[camera_id] or delay > max_delay_events[camera_id]["delay"]:
        max_delay_events[camera_id] = {
            "timestamp": timestamp.isoformat(),
            "event": event_data,
            "delay": delay
        }
        # Update the max delay log file
        with open("logs/maxeventdelay.log", "w") as max_log_file:
            for cam_id, event_info in max_delay_events.items():
                if event_info:
                    cam_name = camera_names[cam_id]
                    max_log_file.write(f"Websocket events testing ({cam_name} - {cam_id}):\n")
                    max_log_file.write(f"Max Delay:\n")
                    max_log_file.write(f"{event_info['timestamp']} : {json.dumps(event_info['event'], indent=4)}\n\n")

    # Prepare and write the log data
    log_data = [
        f"Websocket events testing ({camera_names[camera_id]} - {camera_id}):",
        f"Min delay = {min_delay:.4f} seconds",
        f"Max delay = {max_delay:.4f} seconds",
        f"Avg delay = {avg_delay:.4f} seconds",
        f"Latest event delay = {delay:.4f} seconds",
        ""
    ]
    if ns_counts[camera_id]:
        log_data.append("Matching ns values and descriptions:")
        for ns_value, ns_delays in ns_counts[camera_id].items():
            ns_description = ns_mapping.get(ns_value, "Unknown")
            avg_ns_delay = sum(ns_delays) / len(ns_delays) if ns_delays else 0
            log_data.append(f"{ns_value} ({ns_description}): {len(ns_delays)} events, Avg delay = {avg_ns_delay:.4f} seconds")
            latest_ns_delay = ns_delays[-1] if ns_delays else 0
            log_data.append(f"Latest delay for {ns_value} = {latest_ns_delay:.4f} seconds")

    # Write the log data to a file
    with open(f'logs/{sanitize_filename(camera_names[camera_id])}_{camera_id}.log', 'w') as log_file:
        log_file.write("\n".join(log_data))

# Main function to initiate the websocket connection for the specified cameras
async def main(branding, auth_key, accountId, ns_values):
    uri = f"wss://{branding}.eagleeyenetworks.com/api/v2/Device/{accountId}/Events?A={auth_key}"
    await connect_and_log(uri, ns_values)

# Specify the namespaces you are interested in
ns_values = list(ns_mapping.keys())

# Run the main function with the specified camera IDs
asyncio.run(main(branding, auth_key, accountId, ns_values))
