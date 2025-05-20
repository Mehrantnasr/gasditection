import time
import random
import json
from MyMQTT import MyMQTT

class GasSensorPublisher:
    def __init__(self, sensor_id, topic, broker, port):
        self.sensor_id = sensor_id
        self.topic = topic
        self.mqtt_client = MyMQTT(f"sensor_{sensor_id}", broker, port)
        self.mqtt_client.start()

    def publish_loop(self, interval=5):
        while True:
            gas_value = round(random.uniform(5, 90), 2)
            payload = {
                "bn": self.sensor_id,
                "e": [{
                    "n": "gas",
                    "u": "ppm",
                    "t": time.time(),
                    "v": gas_value
                }]
            }
            print(f"[Sensor {self.sensor_id}] Publishing to {self.topic}: {gas_value} ppm")
            self.mqtt_client.myPublish(self.topic, payload)
            time.sleep(interval)

    def stop(self):
        self.mqtt_client.stop()

if __name__ == "__main__":
    sensor = GasSensorPublisher(
        sensor_id=101,
        topic="gasDetector/sensor/gas/101",
        broker="mqtt.eclipseprojects.io",
        port=1883
    )
    try:
        sensor.publish_loop()
    except KeyboardInterrupt:
        sensor.stop()
