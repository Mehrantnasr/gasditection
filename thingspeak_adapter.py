import json
import paho.mqtt.client as mqtt
import requests

MQTT_BROKER = "mqtt.eclipseprojects.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gasDetector/sensor/gas/#"
THINGSPEAK_WRITE_KEY = "UZJF3ZQ1AKOEWVHT"

def on_connect(client, userdata, flags, rc):
    print("[Adapter] Connected to MQTT broker with result code", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        value = float(data["e"][0]["v"])
        print(f"[Adapter] Forwarding gas value: {value} ppm to ThingSpeak")
        requests.get(f"https://api.thingspeak.com/update?api_key={THINGSPEAK_WRITE_KEY}&field1={value}")
    except Exception as e:
        print("[Adapter] Error forwarding data:", e)

def start_adapter():
    client = mqtt.Client(clean_session=True)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_forever()

if __name__ == "__main__":
    start_adapter()
