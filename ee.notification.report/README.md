# Delay Report Generator

This script generates a CSV report analyzing delays between events, alerts, and notifications from the Eagle Eye Networks API.

**Environment Variable**:  
Set the API access token as an environment variable:  
```bash
export EAGLEEYE_ACCESS_TOKEN="your_api_token_here"
```
**Install Dependencies**:
Run the following command to install required libraries:
```bash
pip install -r requirements.txt
```
**Configuration**:
Within the code add the needed values:
```python
# Configuration
baseUrl = "" # baseurl api.c**.eagleeyenetworks.com
actorId = "" # CameraId 
actorType = "camera"
bridgeActorId = "" # Bridge ID
```
**Run the code**:
```bash
python3 app.py
```
**Output**
CSV File: 
`{cameraId}_delays_report.csv`
Contains delay analysis between events, alerts, notifications, and bridge statuses.
***Log File***: 
`script_debug.log`
includes detailed logs for debugging.