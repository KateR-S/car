"""Configuration settings for the Attendance Tracking App."""

import os

# Authentication
DEFAULT_PASSWORD = os.environ.get("ADMIN_PASS","")

# Enums
RESIDENT_TYPES = ["Local", "Term-time Only", "Vacation Only"]
LOCATIONS = ["Withycombe Raleigh", "Cathedral"]

# Data file path
DATA_FILE = "data/data.json"

# Touch settings
MAX_BELLS = 12
MAX_TOUCHES_PER_PRACTICE = 12

# Database backend: 'json' or 'neon'
# Set USE_NEON=true environment variable to use Neon database
USE_NEON = os.environ.get('USE_NEON', '').lower() in ('true', '1', 'yes')

# Database connection pool settings (for Neon)
DB_POOL_MIN_CONNECTIONS = int(os.environ.get('DB_POOL_MIN', '1'))
DB_POOL_MAX_CONNECTIONS = int(os.environ.get('DB_POOL_MAX', '5'))

# Data caching settings
CACHE_TTL_SECONDS = int(os.environ.get('CACHE_TTL', '300'))  # Default: 5 minutes
