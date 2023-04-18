#!/bin/bash

# Change to the directory where your Django project is located
cd /Users/nik.gorbunov/Projects/binance-alarm || exit

# Activate the virtual environment
source /Users/nik.gorbunov/Projects/binance-alarm/venv/bin/activate

# Check for data in the database
if python manage.py shell -c "from alarm.models import Threshold; exit(0 if Threshold.objects.exists() else 1)"; then
    # Run the management command if data is present
    python manage.py price_break_threshold_alarm
fi
