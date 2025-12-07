from enviro import logging
from enviro.constants import UPLOAD_SUCCESS, UPLOAD_FAILED, UPLOAD_SKIP_FILE
import urequests
import config
import enviro.helpers as helpers
from enviro import ENVIRO_VERSION

SENSOR_COMMUNITY_API_URL = "https://api.sensor.community/v1/push-sensor-data/"

# Mapping of enviro reading keys to (value_type, x_pin)
# P1 = PM10, P2 = PM2.5, P0 = PM1
SENSOR_MAPPING = {
  "pm10": ("P1", "1"),
  "pm2_5": ("P2", "1"),
  "pm1": ("P0", "1"),
  "temperature": ("temperature", "11"),
  "humidity": ("humidity", "11"),
  "pressure": ("pressure", "11")
}

def log_destination():
  logging.info(f"> uploading cached readings to Sensor.Community")

def upload_reading(reading):
  # Group readings by X-Pin
  pins_data = {}

  readings_data = reading["readings"]

  for key, value in readings_data.items():
    if key in SENSOR_MAPPING:
      value_type, pin = SENSOR_MAPPING[key]
      if pin not in pins_data:
        pins_data[pin] = []
      pins_data[pin].append({
        "value_type": value_type,
        "value": str(value)
      })

  if not pins_data:
    logging.info(f"  - no supported readings for Sensor.Community, skipping")
    return UPLOAD_SKIP_FILE

  all_success = True

  uid = f"rpi-pico-{helpers.uid()}"

  for pin, values in pins_data.items():
    headers = {
      "Content-Type": "application/json",
      "X-Pin": pin,
      "X-Sensor": uid
    }

    payload = {
      "software_version": f"enviro-{ENVIRO_VERSION}",
      "sensordatavalues": values
    }

    try:
      result = urequests.post(SENSOR_COMMUNITY_API_URL, json=payload, headers=headers)
      result.close()

      if result.status_code not in [200, 201, 202]:
        logging.debug(f"  - upload issue for pin {pin} ({result.status_code} {result.reason})")
        all_success = False
      else:
        logging.debug(f"  - uploaded pin {pin} data")

    except Exception as e:
      logging.debug(f"  - exception uploading pin {pin}: {e}")
      all_success = False

  if all_success:
    return UPLOAD_SUCCESS

  return UPLOAD_FAILED
