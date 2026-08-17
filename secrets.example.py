# secrets.example.py – Vorlage. Kopiere diese Datei nach secrets.py und trage deine Werte ein.
# secrets.py wird NICHT committen (in .gitignore).

# --- WiFi ---
WIFI_SSID = ""
WIFI_PASSWORD = ""

# --- Standort fuer Open-Meteo (Breitengrad, Laengengrad) ---
# Beispiel Berlin: 52.52, 13.405
LATITUDE = 52.52
LONGITUDE = 13.405

# --- Kalender (oeffentliche .ics URL) ---
# z.B. Nextcloud: https://cloud.example.org/remote.php/dav/public-calendars/<id>/?export
# oder Google Calendar: Settings -> "Secret address in iCal format"
ICS_URL = ""

# --- Aktualisierungsintervall in Minuten ---
UPDATE_INTERVAL_MINUTES = 30
