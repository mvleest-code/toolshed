#!/bin/bash

# Variables
WEBHOOK_URL="https://discord.com/api/webhooks/********"
SCRIPT_PATH="/usr/local/bin/send_ip_to_discord.sh"
SERVICE_PATH="/etc/systemd/system/ip-notify.service"
PATH_UNIT_PATH="/etc/systemd/system/ip-notify.path"

# Create the script to send IP addresses to Discord webhook
echo "Creating the IP notification script..."
cat <<EOL > $SCRIPT_PATH
#!/bin/bash

# Discord webhook URL
WEBHOOK_URL="$WEBHOOK_URL"

# Get the hostname of the device
HOSTNAME=\$(hostname)

# Get internal IP addresses of all physical network interfaces (excluding virtual and loopback)
IP_INTERNAL=""
for iface in \$(ls /sys/class/net); do
    if [[ \$(cat /sys/class/net/\$iface/operstate) == "up" ]] && [[ ! \$iface =~ ^(lo|docker|veth|br-|virbr|vmnet|vboxnet|tun|tap) ]]; then
        IP_ADDR=\$(ip -4 addr show \$iface | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
        if [[ -n \$IP_ADDR ]]; then
            IP_INTERNAL+="Interface \$iface: \$IP_ADDR\n"
        fi
    fi
done

# Get the external IP address
IP_EXTERNAL=\$(curl -s ifconfig.me)

# Create the message to send
MESSAGE="Hostname: \$HOSTNAME\nInternal IPs:\n\$IP_INTERNAL\nExternal IP: \$IP_EXTERNAL"

# Send the message to the Discord webhook
curl -H "Content-Type: application/json" -X POST -d "{\"content\": \"\$MESSAGE\"}" \$WEBHOOK_URL
EOL

# Make the script executable
chmod +x $SCRIPT_PATH

# Create a systemd service to run the script at boot
echo "Creating systemd service..."
cat <<EOL > $SERVICE_PATH
[Unit]
Description=Send IP addresses to Discord webhook on boot and network changes
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$SCRIPT_PATH
ExecStartPost=/usr/bin/systemctl restart ip-notify.path

[Install]
WantedBy=multi-user.target
EOL

# Create a systemd path unit to monitor network changes
echo "Creating systemd path unit..."
cat <<EOL > $PATH_UNIT_PATH
[Unit]
Description=Monitor network interface changes

[Path]
PathChanged=/etc/network/interfaces
PathChanged=/run/systemd/network

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd daemon to recognize the new service and path unit
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable and start the service and path unit
echo "Enabling and starting services..."
systemctl enable ip-notify.service
systemctl enable ip-notify.path
systemctl start ip-notify.service
systemctl start ip-notify.path

echo "Setup complete. IP address notifications are now active."
