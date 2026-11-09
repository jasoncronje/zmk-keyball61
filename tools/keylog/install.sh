#!/bin/sh
# Builds keylogd and runs it at login as a LaunchAgent (restarted if it exits).
#   tools/keylog/install.sh            install or update
#   tools/keylog/install.sh uninstall  stop it and remove the agent (keeps the log)
set -eu

label=io.cronje.keyball-keylogd
bin="$HOME/.local/bin/keyball-keylogd"
plist="$HOME/Library/LaunchAgents/$label.plist"
logfile="$HOME/Library/Logs/keyball-keylogd.log"
domain="gui/$(id -u)"

launchctl bootout "$domain/$label" 2>/dev/null || true

if [ "${1:-}" = uninstall ]; then
    rm -f "$plist" "$bin"
    echo "Removed $label (the log database is kept)"
    exit 0
fi

mkdir -p "$(dirname "$bin")" "$(dirname "$plist")"
swiftc -O -o "$bin" "$(dirname "$0")/keylogd.swift"

cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$label</string>
    <key>ProgramArguments</key>
    <array>
        <string>$bin</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>30</integer>
    <key>ProcessType</key>
    <string>Background</string>
    <key>StandardErrorPath</key>
    <string>$logfile</string>
</dict>
</plist>
EOF

launchctl bootstrap "$domain" "$plist"
echo "Running $label; log: $logfile"
