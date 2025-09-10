import json
import paho.mqtt.client as mqtt

class MqttBridge:
    def __init__(self, host, port, on_cmd):
        self.c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        def _on_connect(c, ud, flg, rc, props=None):
            c.subscribe("bioreactor/cmd/#", qos=1)
            c.subscribe("bioreactor/simCmd/#", qos=1)
        self.c.on_connect = _on_connect
        self.c.on_message = lambda c,ud,msg: on_cmd(msg.topic, msg.payload.decode("utf-8"))
        self.c.connect(host, port, 60)

    def loop_start(self): self.c.loop_start()

    def publish_state(self, state: dict, actuators: dict | None = None):
        # Only publish known sensor keys under sensors/*
        sensor_keys = ("level", "temperature", "do", "ph", "agitation_rpm", "biomass", "pressure_kpa")
        sensors_payload = {}
        for k in sensor_keys:
            if k in state:
                v = state[k]
                sensors_payload[k] = v
                self.c.publish(f"bioreactor/sensors/{k}", v, qos=1, retain=True)
        # Publish aggregate state (sensors only) as JSON
        self.c.publish("bioreactor/state", json.dumps(sensors_payload), qos=1, retain=True)

        # Publish actuators under actuators/*
        if actuators:
            for k, v in actuators.items():
                self.c.publish(f"bioreactor/actuators/{k}", v, qos=1, retain=True)
