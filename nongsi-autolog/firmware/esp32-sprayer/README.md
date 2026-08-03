# ESP32 가상 센서 송신기

실제 센서나 펌프를 연결하지 않고 Python 시뮬레이터와 동일한 상태 주기와 JSON payload를 Wi-Fi/MQTT로 보냅니다.

```powershell
Copy-Item .\include\nongsi_config.example.h .\include\nongsi_config.h
# nongsi_config.h에서 Wi-Fi와 개발 PC의 LAN IP 수정
pio run
pio run --target upload
pio device monitor
```

Docker의 `localhost`는 ESP32에서 개발 PC를 뜻하지 않으므로 `NONGSI_MQTT_HOST`에는 Windows PC의 LAN IPv4를 사용합니다. Windows 방화벽과 공유기 네트워크에서 TCP 1883 접근을 별도로 허용해야 할 수 있습니다. 실제 센서 핀과 펌프 제어는 포함하지 않습니다.
