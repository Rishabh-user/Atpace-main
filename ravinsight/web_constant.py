import os

if os.environ["PLATFORM"] == "dev":
    BASE_URL = "http://dev.growatpace.com"
    DOMAIN = "dev.growatpace.com"
    PROTOCOL = "http"
    COMMUNITY_DOMAIN = "forum.dev.growatpace.com"
    COMMUNITY_URL = "http://forum.dev.growatpace.com"
    Space_Group_ID = "b988c1bd-025b-4bc3-9f48-fbc57a825837"
elif os.environ["PLATFORM"] == "stage":
    BASE_URL = "https://stage.growatpace.com"
    DOMAIN = "stage.growatpace.com"
    PROTOCOL = "https"
    COMMUNITY_DOMAIN = "forum.growatpace.com"
    COMMUNITY_URL = "https://forum.growatpace.com"
    Space_Group_ID = "bb29a77d-9fce-47d9-add8-8e13f7c2355f"
    
elif os.environ["PLATFORM"] == "prod":
    BASE_URL = "https://growatpace.com"
    DOMAIN = "growatpace.com"
    PROTOCOL = "https"
    COMMUNITY_DOMAIN = "forum.growatpace.com"
    COMMUNITY_URL = "https://forum.growatpace.com"
    Space_Group_ID = "bb29a77d-9fce-47d9-add8-8e13f7c2355f"

INFO_CONTACT_EMAIL = "info@growatpace.com"
SITE_NAME = "Growatpace"
DEFAULT_TIMEZONE = "Asia/Singapore"

LOGIN_URL = f"{BASE_URL}/login"

VONAGE_KEY = "1a6051b6"
VONAGE_SECRET = "caDusNN9UAUcatDG"
# VONAGE_NUMBER = "14157386102"

#Vonage details
VONAGE_URL = "https://api.nexmo.com/v1/messages"
VONAGE_NUMBER = "6531051924"
VONAGE_NAMESPACE = "e45f8724_53d6_423b_bbf0_df214cb4f9d5"
JWT_SECRET_KEY = "kBhOXxDwVK4sxK9bJF-PlZf58uWBnmjdXVJwYfzVATHkrWsssS-uGS2iQB8KZuP-"