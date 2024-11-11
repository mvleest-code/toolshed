# Websocket Event Delay Logger

This project connects to a websocket to receive event notifications from cameras, processes the events, and logs the delays in notifications.

## Features

- Connects to a websocket to receive event notifications.
- Processes events and calculates delays.
- Logs event data and delays to files.
- Supports multiple namespaces for different types of events.

## Setup
1. **Install dependencies:**

    This project requires Python 3.6 or higher. Install the required packages using pip:

    ```sh
    pip install -r requirements.txt
    ```

2. **Configuration:**

    Update the following configuration details in the script:

    ```python
    branding = "c022"
    accountId = "00142573"
    auth_key = "c022~ffa2f40b92fccae2c518236d859cb7db"
    ```

## Usage

1. **Run the script:**

    ```sh
    python app.py
    ```

2. **Logs:**

    - Event data and delays are logged in the `logs` directory.
    - Stream logs for each camera are stored in `logs/stream`.
    - Maximum delay events are logged in `logs/maxeventdelay.log`.

## Functions

- `sanitize_filename(filename)`: Replaces or removes invalid characters for filenames.
- `get_cameraids(branding, auth_key)`: Fetches camera IDs and names from the specified branding and auth key.
- `log_processed_event_uuid(event_uuid)`: Logs processed event UUID to a file.
- `connect_and_log(uri, ns_values)`: Connects to the websocket and logs events.
- `log_event_data(camera_id, cam_data, timestamp, stream_logs)`: Logs event data for a camera.
- `handle_event(camera_id, event_data, timestamp)`: Handles and processes an event for a camera.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.