# GasLeakDetector

An IoT-based gas leak detection system that monitors gas sensor readings, forwards data to ThingSpeak for visualization, manages device configurations via a RESTful catalog, and provides real-time alerts through MQTT and Telegram.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Usage](#usage)
- [File Structure](#file-structure)
- [Contributing](#contributing)
- [License](#license)
- [Authors](#authors)

---

## Features

- **Sensor Simulation**: `sensor_publisher.py` generates random gas readings and publishes to MQTT.
- **Data Forwarding**: `thingspeak_adapter.py` subscribes to MQTT and pushes readings to ThingSpeak.
- **Threshold Monitoring**: `controller_unit.py` checks readings against configurable thresholds and publishes alerts when violated.
- **Catalog Registry**: `catalog_registery.py` exposes a CherryPy-based REST API to manage buildings and devices via JSON.
- **Telegram Bot**: `GasBot.py` allows users to view device statuses, manage catalog entries, and receive real-time gas alerts over Telegram.
- **MQTT Wrapper**: `MyMQTT.py` simplifies publishing/subscribing with callback integration.

## Architecture

\`\`\`
[SensorPublisher] --> MQTT Broker --> [ThingSpeak Adapter] --> ThingSpeak Dashboard
                         |
                         +--> [GasController] --> MQTT Alert Topic --> [GasBot]
                                                         |
                                                         +--> Telegram Notifications

REST Clients <--> [CatalogRegistry API] <--> catalog.json
\`\`\`

- **MQTT Broker**: \`mqtt.eclipseprojects.io:1883\` (default)  
- **Topics**:  
  - Sensor data: \`gasDetector/sensor/gas/{sensor_id}\`  
  - Alerts: \`gasDetector/alert/gas\`  

## Getting Started

### Prerequisites

- Python 3.7+  
- \`pip\` package manager  

Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`
*Example \`requirements.txt\` contents:*
\`\`\`
paho-mqtt
requests
cherrypy
telepot
\`\`\`

### Installation

1. Clone the repository:
   \`\`\`bash
git clone https://github.com/Group5/GasLeakDetector.git
cd GasLeakDetector
\`\`\`
2. Ensure \`catalog.json\` is present in the project root.

### Configuration

- **catalog.json**: Defines project metadata, MQTT broker settings, admin credentials, buildings, and devices.  
- **ThingSpeak**:
  - \`THINGSPEAK_WRITE_KEY\` in \`thingspeak_adapter.py\`  
  - \`THINGSPEAK_READ_URL\` in \`GasBot.py\`  
- **Telegram Bot**:
  - \`TELEGRAM_BOT_TOKEN\` and \`TELEGRAM_CHAT_ID\` in \`GasBot.py\`  

> **Tip**: For security, consider using environment variables or a \`.env\` file instead of hardcoding tokens.

### Usage

1. **Start Catalog Registry** (port 8080 by default):
   \`\`\`bash
python catalog_registery.py
\`\`\`
2. **Run Sensor Publisher** (simulates sensor 101):
   \`\`\`bash
python sensor_publisher.py
\`\`\`
3. **Start ThingSpeak Adapter** (forwards data to ThingSpeak):
   \`\`\`bash
python thingspeak_adapter.py
\`\`\`
4. **Launch GasController** (monitors thresholds and alerts):
   \`\`\`bash
python controller_unit.py
\`\`\`
5. **Run Telegram Bot** (interact with devices and alerts):
   \`\`\`bash
python GasBot.py
\`\`\`

## File Structure

- \`catalog.json\` – Project configuration and device registry  
- \`catalog_registery.py\` – RESTful API for catalog management  
- \`sensor_publisher.py\` – Simulates gas sensors and publishes MQTT messages  
- \`thingspeak_adapter.py\` – Forwards MQTT data to ThingSpeak  
- \`controller_unit.py\` – Monitors gas levels, checks thresholds, publishes alerts, and sends Telegram notifications  
- \`GasBot.py\` – Telegram bot interface for device status, catalog management, and alerts  
- \`MyMQTT.py\` – MQTT client wrapper for simplified publish/subscribe  

## Contributing

1. Fork the repository.  
2. Create a feature branch: \`git checkout -b feature/YourFeature\`  
3. Commit your changes: \`git commit -m 'Add YourFeature'\`  
4. Push to the branch: \`git push origin feature/YourFeature\`  
5. Open a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Authors

- **G5_Mehran_Kamran_Keyvan_Erfan_Pezhman** – Project Owner and Development Team

---

*Last Updated: May 11, 2025*
