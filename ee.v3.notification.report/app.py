import csv
import requests
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("script_debug.log"),
        logging.StreamHandler()
    ]
)

# Configuration
baseUrl = ""
actorId = ""
actorType = "camera"
bridgeActorId = ""
actor = f"{actorType}:{actorId}"

# Get access token from environment variable
accessToken = os.getenv('EAGLEEYE_ACCESS_TOKEN')
if not accessToken:
    raise ValueError("Please set the EAGLEEYE_ACCESS_TOKEN environment variable")

logging.info("Access token retrieved")

now_utc = datetime.now(timezone.utc) # Get current time in UTC
one_day_ago_utc = now_utc - timedelta(days=10) # amount of days ago

# Format timestamps
startTimestampGte = one_day_ago_utc.strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
logging.info(f"Start timestamp (UTC): {startTimestampGte}")
endTimestampLte = now_utc.strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
logging.info(f"End timestamp (UTC): {endTimestampLte}")
startTimestamp__gte = startTimestampGte.replace(":", "%3A").replace("+", "%2B")
endTimestamp__lte = endTimestampLte.replace(":", "%3A").replace("+", "%2B")

headers = {
    'accept': 'application/json',
    'authorization': f'Bearer {accessToken}'
}

# 1. Get camera timezone
camera_info_url = f"https://{baseUrl}/api/v3.0/cameras/{actorId}?include=timeZone"
logging.info(f"Fetching camera timezone from {camera_info_url}")
camera_resp = requests.get(camera_info_url, headers=headers).json()
camera_tz_str = camera_resp.get('timeZone', {}).get('zone', 'UTC')
camera_tz = ZoneInfo(camera_tz_str)
logging.info(f"Camera timezone: {camera_tz_str}")

# 2. Get all event types for this camera
event_fields_url = f"https://{baseUrl}/api/v3.0/events:listFieldValues?actor={actorType}%3A{actorId}"
logging.info(f"Fetching event types from {event_fields_url}")
event_fields_resp = requests.get(event_fields_url, headers=headers).json()
event_types = event_fields_resp.get("type", [])
type_in_param = ",".join(event_types)
logging.info(f"Event types: {event_types}")

def parse_timestamp(ts_str):
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return None

# Fetch bridge events
def fetch_all_results(base_url):
    results = []
    current_url = base_url
    seen_tokens = set()  # To track and prevent token reuse

    while True:
        print(f"Fetching results from {current_url}")
        response = requests.get(current_url, headers=headers).json()

        # Extract results
        page_results = response.get('results', [])
        if not page_results:
            print("No more results in this page.")
            break
        results.extend(page_results)

        # Get the nextPageToken
        next_token = response.get('nextPageToken', None)
        if next_token:
            if next_token in seen_tokens:
                print("Duplicate nextPageToken detected, stopping pagination to prevent infinite loop.")
                break
            seen_tokens.add(next_token)
            # Construct the next page URL
            current_url = f"{base_url}&pageToken={next_token}"
        else:
            print("No more pages to fetch.")
            break
    return results

# Fetch bridge status events
def fetch_bridge_events():
    """Fetch bridge-specific events."""
    bridge_actor = f"bridge:{bridgeActorId}"
    bridge_event_url = (
        f"https://{baseUrl}/api/v3.0/events?pageSize=5000"
        f"&startTimestamp__gte={startTimestamp__gte}"
        f"&endTimestamp__lte={endTimestamp__lte}"
        f"&actor={bridge_actor}"
        f"&type__in=een.deviceCloudStatusUpdateEvent.v1"
        f"&include=data.een.deviceCloudStatusUpdate.v1"
    )
    logging.info(f"Fetching bridge events from {bridge_event_url}")
    bridge_events = fetch_all_results(bridge_event_url)
    bridge_event_data = []

    for event in bridge_events:
        event_timestamp = parse_timestamp(event.get('startTimestamp', ''))
        connection_status = "Unknown"
        for data_entry in event.get("data", []):
            if data_entry.get("type") == "een.deviceCloudStatusUpdate.v1":
                connection_status = data_entry.get("newStatus", {}).get("connectionStatus", "Unknown")
                break
        if event_timestamp:  # Only include valid events
            bridge_event_data.append({
                "timestamp": event_timestamp,
                "connectionStatus": connection_status,
            })
    return bridge_event_data

# Fetch all results
events_url = f"https://{baseUrl}/api/v3.0/events?pageSize=5000&startTimestamp__gte={startTimestamp__gte}&endTimestamp__lte={endTimestamp__lte}&actor={actor}&type__in={type_in_param}"
alerts_url = f"https://{baseUrl}/api/v3.0/alerts?actorId={actorId}&actorType={actorType}&pageSize=5000&timestamp__gte={startTimestamp__gte}"
notifications_url = f"https://{baseUrl}/api/v3.0/notifications?actorId={actorId}&actorType={actorType}&sort=-timestamp&pageSize=5000&timestamp__gte={startTimestamp__gte}"

logging.info(f"Fetching events from {events_url}")
events_results = fetch_all_results(events_url)
logging.info(f"Fetched {len(events_results)} events")

logging.info(f"Fetching alerts from {alerts_url}")
alerts_results = fetch_all_results(alerts_url)
logging.info(f"Fetched {len(alerts_results)} alerts")

logging.info(f"Fetching notifications from {notifications_url}")
notifications_results = fetch_all_results(notifications_url)
logging.info(f"Fetched {len(notifications_results)} notifications")

logging.info("Fetching bridge events")
bridge_events = fetch_bridge_events()
logging.info(f"Fetched {len(bridge_events)} bridge events")

# Process data
events_data = {e['id']: {
    'type': e['type'],
    'startTimestamp': parse_timestamp(e['startTimestamp'])
} for e in events_results if parse_timestamp(e['startTimestamp'])}

alerts_data = {a['id']: {
    'eventId': a['eventId'],
    'timestamp': parse_timestamp(a['timestamp'])
} for a in alerts_results if parse_timestamp(a['timestamp'])}

# Write CSV
csv_filename = f'{actorId}_delays_report.csv'
logging.info(f"Writing data to {csv_filename}")
with open(csv_filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        "eventType",
        "eventId",
        "alertId",
        "notificationId",
        "eventStartTimestampUTC",
        "notificationTimestampUTC",
        "eventStartTimestampLocal",
        "notificationTimestampLocal",
        "event >> Alert",
        "alert >> Notification",
        "totalDelaySeconds",
        "bridgeEventTimestampUTC",
        "bridgeConnectionStatus"
    ])

    for n in notifications_results:
        notification_ts = parse_timestamp(n['timestamp'])
        notification_id = n['id']
        alert_id = n.get('alertId')
        if alert_id in alerts_data:
            alert_info = alerts_data[alert_id]
            alert_ts = alert_info['timestamp']
            event_id = alert_info['eventId']

            if event_id in events_data:
                event_info = events_data[event_id]
                event_ts = event_info['startTimestamp']
                event_type = event_info['type']

                event_to_alert = (alert_ts - event_ts).total_seconds()
                alert_to_notification = (notification_ts - alert_ts).total_seconds()
                total_delay = (notification_ts - event_ts).total_seconds()

                # Bridge event matching
                bridge_event = min(
                    bridge_events,
                    key=lambda b: abs((b["timestamp"] - event_ts).total_seconds()),
                    default={"timestamp": None, "connectionStatus": "N/A"}
                )
                bridge_event_utc = bridge_event["timestamp"].strftime("%Y-%m-%dT%H:%M:%S") if bridge_event["timestamp"] else "N/A"
                bridge_status = bridge_event["connectionStatus"]

                # Format timestamps
                event_time_utc_str = event_ts.strftime("%Y-%m-%dT%H:%M:%S")
                notification_time_utc_str = notification_ts.strftime("%Y-%m-%dT%H:%M:%S")
                event_time_local_str = event_ts.astimezone(camera_tz).strftime("%Y-%m-%dT%H:%M:%S")
                notification_time_local_str = notification_ts.astimezone(camera_tz).strftime("%Y-%m-%dT%H:%M:%S")

                writer.writerow([
                    event_type,
                    event_id,
                    alert_id,
                    notification_id,
                    event_time_utc_str,
                    notification_time_utc_str,
                    event_time_local_str,
                    notification_time_local_str,
                    f"{event_to_alert:.2f}",
                    f"{alert_to_notification:.2f}",
                    f"{total_delay:.2f}",
                    bridge_event_utc,
                    bridge_status
                ])
logging.info("CSV writing completed")