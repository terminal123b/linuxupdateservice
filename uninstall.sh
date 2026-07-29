#!/bin/bash
# Uninstall keylogger

echo "============================================================"
echo " UNINSTALLING KEYLOGGER"
echo "============================================================"

# Stop service
echo "Stopping service..."
sudo systemctl stop windowsupdateservice.service 2>/dev/null
sudo systemctl disable windowsupdateservice.service 2>/dev/null

# Remove files
echo "Removing files..."
sudo rm -f /etc/systemd/system/windowsupdateservice.service
sudo rm -rf /opt/WindowsUpdateService
sudo rm -rf /etc/windowsupdateservice
sudo rm -rf /var/log/windowsupdateservice
sudo rm -rf /var/lib/windowsupdateservice

# Remove from crontab
echo "Removing from crontab..."
(crontab -l 2>/dev/null | grep -v "keylogger.py") | crontab - 2>/dev/null

# Remove from bashrc
echo "Removing from bashrc..."
for user_home in /home/* /root; do
    if [ -f "$user_home/.bashrc" ]; then
        sed -i '/keylogger.py/d' "$user_home/.bashrc"
    fi
done

# Remove from rc.local
echo "Removing from rc.local..."
if [ -f /etc/rc.local ]; then
    sed -i '/keylogger.py/d' /etc/rc.local
fi

# Reload systemd
sudo systemctl daemon-reload

echo "============================================================"
echo " UNINSTALL COMPLETE!"
echo "============================================================"
