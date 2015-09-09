
DEBUG = True

SECRET_KEY = "OVERWRITE ME IN local_settings.py"

TIMEZONE = 'America/Kentucky/Louisville'

# Levels
# CRITICAL
# DEBUG
# ERROR
# FATAL
# INFO
# WARN
# WARNING
LOG_LEVEL = 'DEBUG'

## Mongodb configuration
# MONGO_HOST = "localhost"
# MONGO_PORT = 27017
MONGO_DBNAME = "lexsocial"
# MONGO_USERNAME = None
# MONGO_PASSWORD = None
# MONGO_REPLICA_SET = None

# Admin Settings
ADMIN_URL = '/admin/'

try:
    from local_settings import *
except ImportError, inst:
    logging.error("Unable to import local_settings : %s" % inst)
