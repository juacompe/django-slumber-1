"""
    Some caches used in the implementation of the Slumber client or server.
"""
import threading


# Stores the applications via their application names
APP_FROM_APPNAME = {}

# Stores the server model for a given Django model in the server
DJANGO_MODEL_TO_SLUMBER_MODEL = {}
# Stores the slumber models for given model URLs
MODEL_URL_TO_SLUMBER_MODEL = {}

# thread local cache
PER_THREAD = threading.local()
