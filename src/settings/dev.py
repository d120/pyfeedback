from .base import *

DEBUG = True

# Disable secure cookies for local HTTP development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

ALLOWED_HOSTS = []

CSRF_TRUSTED_ORIGINS = []


## for testing SSO, set DEBUG=False and ALLOWED_HOSTS = ["*"]
# from dotenv import load_dotenv, find_dotenv

# load_dotenv(find_dotenv())

# SOCIALACCOUNT_PROVIDERS = {
#     "openid_connect": {
#         "APPS": [
#             {
#                 "provider_id": "keycloak",
#                 "name": "Keycloak",
#                 "client_id": os.getenv("KEYCLOAK_CLIENT_ID"),
#                 "secret": os.getenv("KEYCLOAK_SECRET"),
#                 "settings": {
#                     "server_url": os.getenv("KEYCLOAK_SERVER_URL"),
#                 },
#             }
#         ]
#     }
# }
