#include <Arduino.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <time.h>

#if __has_include("nongsi_config.h")
#include "nongsi_config.h"
#else
#define NONGSI_WIFI_SSID "your-wifi"
#define NONGSI_WIFI_PASSWORD "your-password"
#define NONGSI_MQTT_HOST "192.168.0.10"
#define NONGSI_MQTT_PORT 1883
#define NONGSI_DEVICE_ID "sprayer-001"
#endif

WiFiClient networkClient;
PubSubClient mqttClient(networkClient);
uint32_t sequenceNumber = 0;
uint32_t lastPublishedAt = 0;

String isoTimestamp() {
  struct tm timeInfo;
  if (!getLocalTime(&timeInfo, 100)) return "1970-01-01T00:00:00+00:00";
  char value[30];
  strftime(value, sizeof(value), "%Y-%m-%dT%H:%M:%S+09:00", &timeInfo);
  return String(value);
}

void publishStatus(const char *status, bool retained) {
  JsonDocument document;
  document["device_id"] = NONGSI_DEVICE_ID;
  document["status"] = status;
  document["timestamp"] = isoTimestamp();
  document["source"] = "esp32_virtual_sensor";
  String payload;
  serializeJson(document, payload);
  String topic = "nongsi/devices/" + String(NONGSI_DEVICE_ID) + "/status";
  mqttClient.publish(topic.c_str(), payload.c_str(), retained);
}

void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA);
  WiFi.begin(NONGSI_WIFI_SSID, NONGSI_WIFI_PASSWORD);
  Serial.printf("Connecting Wi-Fi: %s", NONGSI_WIFI_SSID);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }
  Serial.printf(" connected, IP=%s\n", WiFi.localIP().toString().c_str());
}

void connectMqtt() {
  while (!mqttClient.connected()) {
    String clientId = "nongsi-esp32-" + String(NONGSI_DEVICE_ID);
    String statusTopic = "nongsi/devices/" + String(NONGSI_DEVICE_ID) + "/status";
    const char *offline = "{\"status\":\"offline\",\"source\":\"esp32_lwt\"}";
    if (mqttClient.connect(clientId.c_str(), statusTopic.c_str(), 1, true, offline)) {
      publishStatus("online", true);
      Serial.println("MQTT connected");
    } else {
      Serial.printf("MQTT connection failed, state=%d\n", mqttClient.state());
      delay(2000);
    }
  }
}

void publishVirtualTelemetry() {
  const uint8_t phase = sequenceNumber % 25;
  float rms = 0.04F, current = 0.05F, pressure = 0.2F;
  bool running = false;
  if (phase >= 5 && phase < 10) {
    rms = 0.55F;
    current = 0.08F;
  } else if (phase >= 10 && phase < 20) {
    rms = 0.65F;
    current = 2.7F;
    pressure = 8.2F;
    running = true;
  } else if (phase >= 20) {
    rms = 0.63F;
    current = 2.7F;
    pressure = 3.4F;
    running = true;
  }

  JsonDocument document;
  document["device_id"] = NONGSI_DEVICE_ID;
  document["timestamp"] = isoTimestamp();
  document["sequence"] = sequenceNumber++;
  document["imu"]["ax"] = 0.12;
  document["imu"]["ay"] = -0.08;
  document["imu"]["az"] = 1.01;
  document["imu"]["gx"] = 1.2;
  document["imu"]["gy"] = 0.4;
  document["imu"]["gz"] = -0.7;
  document["imu"]["rms"] = rms;
  document["pump"]["current_a"] = current;
  document["pump"]["is_running"] = running;
  document["pressure"]["bar"] = pressure;
  document["pressure"]["valid"] = true;
  document["battery"]["voltage"] = 4.02;
  document["battery"]["percent"] = 82;
  document["signal"]["rssi"] = WiFi.RSSI();

  String payload;
  serializeJson(document, payload);
  String topic = "nongsi/devices/" + String(NONGSI_DEVICE_ID) + "/telemetry";
  if (!mqttClient.publish(topic.c_str(), payload.c_str())) {
    Serial.println("Telemetry publish failed");
  } else {
    Serial.println(payload);
  }
}

void setup() {
  Serial.begin(115200);
  connectWifi();
  configTime(9 * 3600, 0, "pool.ntp.org", "time.google.com");
  mqttClient.setServer(NONGSI_MQTT_HOST, NONGSI_MQTT_PORT);
  mqttClient.setBufferSize(1024);
  connectMqtt();
}

void loop() {
  connectWifi();
  connectMqtt();
  mqttClient.loop();
  const uint32_t now = millis();
  if (now - lastPublishedAt >= 1000) {
    lastPublishedAt = now;
    publishVirtualTelemetry();
  }
  delay(10);
}
