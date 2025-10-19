import requests
import json
import time
from MyMQTT import MyMQTT


with open("catalog.json") as f:
    catalog_data = json.load(f)
    bot_config = catalog_data.get("botConfig", {})
    TELEGRAM_BOT_TOKEN = bot_config.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = bot_config.get("TELEGRAM_CHAT_ID")

    
class GasController:
    def __init__(self, client_id, broker, port, catalog_url, alert_topic):
        self.catalog_url = catalog_url
        self.alert_topic = alert_topic

        self.client = MyMQTT(client_id, broker, port, self)
        self.client.start()
        self.client.mySubscribe("gasDetector/sensor/gas/#")

    def notify(self, topic, payload):
        try:
            data = json.loads(payload)
            sensor_id = int(data["bn"])
            value = float(data["e"][0]["v"])
            timestamp = data["e"][0]["t"]

            print(f"[Controller] Received value {value} from sensor {sensor_id}")

            thresholds = self.get_thresholds(sensor_id)
            if thresholds:
                min_val = float(thresholds["min"])
                max_val = float(thresholds["max"])
                if value > max_val or value < min_val:
                    print("⚠️ ALERT: Gas level outside safe threshold!")
                    self.send_alert(sensor_id, value, timestamp)
                else:
                    print("✅ Gas level is normal.")
            else:
                print("⚠️ No threshold data found for sensor.")

        except Exception as e:
            print("Error in notify:", e)

    def get_thresholds(self, sensor_id):
        try:
            res = requests.get(f"{self.catalog_url}/buildings")
            for building in res.json():
                for device in building["devices"]:
                    if device["deviceID"] == sensor_id and "Gas" in device.get("measureType", []):
                        return {
                            "min": float(device.get("min_threshold", 0)),
                            "max": float(device.get("max_threshold", 100))
                        }
        except Exception as e:
            print("Error fetching thresholds:", e)
        return None

    def send_alert(self, sensor_id, value, timestamp):
        alert = {
            "deviceID": sensor_id,
            "alertType": "GasLeak",
            "value": value,
            "timestamp": timestamp
        }
        self.client.myPublish(self.alert_topic, alert)

        # Also send Telegram message
        try:
            telegram_msg = f"🚨 GAS ALERT 🚨\nSensor ID: {sensor_id}\nValue: {value} ppm"
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={telegram_msg}"
            requests.get(url)
        except Exception as e:
            print("[Controller] Failed to notify Telegram:", e)


    def stop(self):
        self.client.stop()

if __name__ == "__main__":
    controller = GasController(
        client_id="gas_controller",
        broker="mqtt.eclipseprojects.io",
        port=1883,
        catalog_url="http://127.0.0.1:8080",
        alert_topic="gasDetector/alert/gas"
    )

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        controller.stop()
