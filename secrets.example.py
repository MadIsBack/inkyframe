# secrets.example.py – Vorlage. Kopiere nach secrets.py und trage deine Werte ein.
# secrets.py wird NICHT committen (in .gitignore).

# --- WiFi ---
WIFI_SSID = ""
WIFI_PASSWORD = ""

# --- Standort fuer Open-Meteo (Breitengrad, Laengengrad) ---
LATITUDE = 52.52
LONGITUDE = 13.405

# --- Kalender (zwei Quellen, beide optional) ---
# Google Calendar: Settings -> "Secret address in iCal format"
ICS_URL_GOOGLE = ""
# Nextcloud: https://cloud.example.org/remote.php/dav/public-calendars/<id>/?export
ICS_URL_NEXTCLOUD = ""

# --- Shelly EM3 (zwei Module) ---
SHELLY_EM3_IP_A = ""
SHELLY_EM3_IP_B = ""
# Optional: API-Token bei aktiviertem Auth-Schutz (Gen2: ?auth=<token>)
SHELLY_EM3_TOKEN = ""

# --- Aktualisierungsintervall in Minuten ---
# (Shelly-Historie wird bei jedem Wake gepuffert; Wetter/Kalender je Aufwand)
UPDATE_INTERVAL_MINUTES = 5
