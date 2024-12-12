# IP Notify Script

This is a simple Bash script that sends the internal and external IP addresses of a machine to a Discord webhook. It’s designed to run on Linux systems at boot and whenever network changes are detected. Perfect for keeping tabs on devices in your network!

---

## What Does It Do?

1. **Sends IP Addresses to Discord**:  
   - Internal IPs for active physical interfaces.
   - External IP retrieved via `curl`.
   - Includes the hostname of the device.

2. **Runs Automatically**:  
   - Executes at system startup.
   - Monitors for network changes using `systemd`.

---

## Setup

1. **Clone or Download the Script**:  
   Save the script on your Linux machine.

2. **Set the Webhook URL**:  
   Replace `WEBHOOK_URL="https://discord.com/api/webhooks/********"` with your Discord webhook URL.

3. **Run the Script**:  
   Execute the script to create:
   - The IP notification script at `/usr/local/bin/send_ip_to_discord.sh`
   - A `systemd` service (`ip-notify.service`) to run the script.
   - A `systemd` path unit (`ip-notify.path`) to monitor network changes.

4. **Reload and Enable Services**:  
   The script automatically reloads the `systemd` daemon and enables the service and path unit for you.

---

## How It Works

- **Notification Script**:  
  The script gathers IP information, formats a message, and sends it to your Discord webhook.

- **Systemd Service**:  
  Ensures the script runs at boot and after certain system events.

- **Path Monitoring**:  
  Watches for changes to `/etc/network/interfaces` and `/run/systemd/network` to detect network updates.

---

## Why Use This?

Sometimes you need to know the IP address of a headless device or a server without logging in. This script sends the details directly to Discord, so you always have them handy.

---

## Notes

- **Customization**: You can edit the script path or systemd service name as needed.
- **Dependencies**: Ensure `curl` is installed on your system.
- **Logging**: Systemd manages the logging for this script.

---

**Use at your own risk!** This script is simple and straightforward but might need tweaks depending on your system configuration. Happy IP hunting!