"""Configuration settings for the Attendance Tracking App."""

import os

# Authentication
DEFAULT_PASSWORD = "admin123"

# Enums
RESIDENT_TYPES = ["Local", "Regional", "National", "International"]
LOCATIONS = ["Office A", "Office B", "Office C", "Remote"]

# Data file path
DATA_FILE = "data/data.json"

# Touch settings
MAX_BELLS = 12
MAX_TOUCHES_PER_PRACTICE = 8

# Database backend: 'json' or 'neon'
# Set USE_NEON=true environment variable to use Neon database
USE_NEON = os.environ.get('USE_NEON', '').lower() in ('true', '1', 'yes')
