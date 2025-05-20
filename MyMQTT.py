import json
import paho.mqtt.client as PahoMQTT

class MyMQTT:
    def __init__(self, clientID, broker, port, notifier=None):
        self.broker = broker
        self.port = port
        self.clientID = clientID
        self.notifier = notifier
        self._topic = ""
        self._isSubscriber = False

        self._paho_mqtt = PahoMQTT.Client(clientID, clean_session=True)
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

    def myOnConnect(self, client, userdata, flags, rc):
        print(f"[MQTT] Connected to {self.broker}:{self.port} with result code {rc}")

    def myOnMessageReceived(self, client, userdata, msg):
        payload = msg.payload.decode()
        if self.notifier:
            self.notifier.notify(msg.topic, payload)

    def myPublish(self, topic, msg):
        if isinstance(msg, dict):
            msg = json.dumps(msg)
        self._paho_mqtt.publish(topic, msg, qos=2)

    def mySubscribe(self, topic):
        self._paho_mqtt.subscribe(topic, qos=2)
        self._topic = topic
        self._isSubscriber = True
        print(f"[MQTT] Subscribed to topic: {topic}")

    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def stop(self):
        if self._isSubscriber:
            self._paho_mqtt.unsubscribe(self._topic)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()
