# Web-socket Event Delay Logger

This project connects to a web-socket to receive event notifications from cameras, processes the events, and logs delays in notifications. It also provides detailed logs for analysis of camera events.

---

## Features

- Connects to a web-socket to listen for event notifications from multiple cameras.
- Processes events, calculates delays, and tracks event-specific data.
- Logs:
  - Stream data for each camera.
  - Maximum delay events.
  - Processed event statistics.
- Supports multiple namespaces with descriptions for various event types.

---

## Setup

1. Install Dependencies  
   Ensure you have Python 3.6 or higher installed. Install the required dependencies using pip:

```bash
   pip install -r requirements.txt
```

2. Configuration  
   Update the following configuration details in the script:

```python
   branding = "c000" # Active band subdomain instead of "login" https://{branding}.eagleeyenetworks.com
   accountId = "" # Account id of the end users account.
   auth_key = "" # Auth_key would be: c000~ffa2f40b92fccae2c518236d859cb7db
```

---

## Usage

1. Run the Script  
   Start the application by running:

```bash
   $ python app.py
```

2. Logs

- `Stream Logs`: Stored in `the logs/stream` directory, with separate files for each camera.
- `Event Logs`: Detailed delay analysis for each camera in `logs/`.
- `Max Delay Events`: Summary of maximum delay events stored in `logs/maxeventdelay.log`.

---

## Functions

- `sanitize_filename(filename)`: Ensures filenames are valid by replacing invalid characters.
- `get_cameraids(branding, auth_key)`: Fetches camera IDs and names associated with the given branding and auth key.
- `log_processed_event_uuid(event_uuid)`: Logs processed event UUIDs to avoid duplicate processing.
- `connect_and_log(uri, ns_values)`: Connects to the web-socket, listens for events, and logs responses.
- `log_event_data(camera_id, cam_data, timestamp, stream_logs)`: Logs event data for a specific camera.
- `handle_event(camera_id, event_data, timestamp)`: Processes individual events and calculates delays.
