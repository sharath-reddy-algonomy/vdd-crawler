#!/bin/bash

URL="https://www.example.com"

Xvfb :99 -screen 0 1280x1024x24 &
export DISPLAY=:99

chromium --no-sandbox --start-maximized "$URL"
tail -f /dev/null