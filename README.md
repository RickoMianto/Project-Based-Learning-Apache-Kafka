# Apache Kafka

# Apache Kafka Warehouse Monitoring System

Real-time warehouse monitoring system using Apache Kafka and PySpark for tracking temperature and humidity sensors in multiple warehouses.

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Usage](#usage)
- [Monitoring Output](#monitoring-output)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎯 Overview

This project simulates a real-time warehouse monitoring system for a logistics company managing multiple warehouses storing sensitive goods (food, medicine, electronics). The system monitors temperature and humidity sensors that send data every second and provides real-time alerts for critical conditions.

### Problem Statement
- Multiple warehouses with sensitive goods storage
- Two types of sensors: Temperature and Humidity sensors
- Data transmission every second
- Real-time monitoring to prevent damage from high temperature or excessive humidity

## ✨ Features

- **Real-time Data Streaming**: Kafka producers simulate sensor data every second
- **Stream Processing**: PySpark processes data streams with filtering and joins
- **Alert System**: Automated alerts for critical conditions
- **Multi-condition Monitoring**:
  - Temperature > 80°C → High temperature warning
  - Humidity > 70% → High humidity warning
  - Both conditions → Critical warning
- **Time-window Joins**: Combines temperature and humidity data within 10-second windows

## 🏗️ Architecture

```
Sensors → Kafka Producers → Kafka Topics → PySpark Consumer → Alerts
    ↓           ↓               ↓              ↓             ↓
Temperature  Humidity    sensor-suhu-    Stream Processing  Console
  Sensor     Sensor     gudang Topic    & Filtering       Output
                        sensor-kelembaban-
                        gudang Topic
```

## 📋 Prerequisites

- **Operating System**: Linux/WSL2
- **Java**: OpenJDK 11 or later
- **Python**: 3.8 or later
- **Memory**: At least 4GB RAM
- **Storage**: 2GB free space

## 🔧 Installation

### 1. System Updates and Java Installation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install OpenJDK 11
sudo apt install openjdk-11-jdk -y

# Verify Java installation
java -version

# Set JAVA_HOME environment variable
echo 'export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64' >> ~/.bashrc
echo 'export PATH=$PATH:$JAVA_HOME/bin' >> ~/.bashrc
source ~/.bashrc
```

### 2. Python Dependencies

```bash
# Install Python and pip
sudo apt install python3 python3-pip -y

# Install required Python libraries
pip3 install kafka-python pyspark findspark
```

### 3. Apache Kafka Installation

```bash
# Create Kafka directory
mkdir ~/kafka-setup && cd ~/kafka-setup

# Download Kafka (try multiple options if one fails)
# Option 1: Kafka 3.5.1
wget https://downloads.apache.org/kafka/3.5.1/kafka_2.13-3.5.1.tgz

# Option 2: If above fails, try 3.4.1
# wget https://downloads.apache.org/kafka/3.4.1/kafka_2.13-3.4.1.tgz

# Option 3: Use archive mirror
# wget https://archive.apache.org/dist/kafka/3.5.1/kafka_2.13-3.5.1.tgz

# Extract Kafka
tar -xzf kafka_2.13-3.5.1.tgz
cd kafka_2.13-3.5.1

# Set Kafka environment variables
echo 'export KAFKA_HOME=~/kafka-setup/kafka_2.13-3.5.1' >> ~/.bashrc
echo 'export PATH=$PATH:$KAFKA_HOME/bin' >> ~/.bashrc
source ~/.bashrc
```

### 4. Apache Spark Installation

```bash
# Download Spark
cd ~/kafka-setup

# Option 1: Spark 3.4.1 (recommended)
wget https://downloads.apache.org/spark/spark-3.4.1/spark-3.4.1-bin-hadoop3.tgz

# Option 2: If above fails, try 3.3.4 LTS
# wget https://downloads.apache.org/spark/spark-3.3.4/spark-3.3.4-bin-hadoop3.tgz

# Option 3: Use archive mirror
# wget https://archive.apache.org/dist/spark/spark-3.4.1/spark-3.4.1-bin-hadoop3.tgz

# Extract Spark
tar -xzf spark-3.4.1-bin-hadoop3.tgz

# Set Spark environment variables
echo 'export SPARK_HOME=~/kafka-setup/spark-3.4.1-bin-hadoop3' >> ~/.bashrc
echo 'export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin' >> ~/.bashrc
echo 'export PYSPARK_PYTHON=python3' >> ~/.bashrc
source ~/.bashrc
```

### 5. Kafka-Spark Connector

```bash
# Download required JAR files for Kafka-Spark integration
cd $SPARK_HOME/jars

# For Spark 3.4.1
wget https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.1/spark-sql-kafka-0-10_2.12-3.4.1.jar
wget https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar
wget https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.4.1/spark-token-provider-kafka-0-10_2.12-3.4.1.jar
wget https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar
```

### 6. Create Kafka Topics

```bash
# Start Zookeeper (Terminal 1)
cd ~/kafka-setup/kafka_2.13-3.5.1
bin/zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka Server (Terminal 2)
cd ~/kafka-setup/kafka_2.13-3.5.1
bin/kafka-server-start.sh config/server.properties

# Create topics (Terminal 3)
cd ~/kafka-setup/kafka_2.13-3.5.1

# Create temperature topic
bin/kafka-topics.sh --create --topic sensor-suhu-gudang --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# Create humidity topic
bin/kafka-topics.sh --create --topic sensor-kelembaban-gudang --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# Verify topics
bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

## 📁 Project Structure

```
kafka-warehouse-monitoring/
├── config/
│   └── kafka_config.py          # Kafka configuration
├── producers/
│   ├── temperature_producer.py  # Temperature sensor producer
│   └── humidity_producer.py     # Humidity sensor producer
├── consumer/
│   └── spark_consumer.py        # PySpark stream consumer
├── README.md
└── requirements.txt
```

### Create Project Structure

```bash
# Create project directory
mkdir -p ~/kafka-warehouse-monitoring/{producers,consumer,config}
cd ~/kafka-warehouse-monitoring
```

## ⚙️ Configuration

### config/kafka_config.py
```python
# Kafka configuration
KAFKA_SERVERS = ['localhost:9092']
TOPICS = {
    'temperature': 'sensor-suhu-gudang',
    'humidity': 'sensor-kelembaban-gudang'
}
WAREHOUSES = ['G1', 'G2', 'G3']
```

### requirements.txt
```
kafka-python==2.0.2
pyspark==3.4.1
findspark==2.0.1
```

## 🚀 Usage

### Step 1: Start Kafka Services

```bash
# Terminal 1: Start Zookeeper
cd ~/kafka-setup/kafka_2.13-3.5.1
bin/zookeeper-server-start.sh config/zookeeper.properties

# Terminal 2: Start Kafka Server
cd ~/kafka-setup/kafka_2.13-3.5.1
bin/kafka-server-start.sh config/server.properties
```

### Step 2: Start Producers

```bash
# Terminal 3: Start Temperature Producer
cd ~/kafka-warehouse-monitoring
python3 producers/temperature_producer.py

# Terminal 4: Start Humidity Producer
cd ~/kafka-warehouse-monitoring
python3 producers/humidity_producer.py
```

### Step 3: Start Consumer

```bash
# Terminal 5: Start PySpark Consumer
cd ~/kafka-warehouse-monitoring
python3 consumer/spark_consumer.py
```

## 📊 Monitoring Output

The system produces three types of monitoring outputs:

### 1. Temperature Alerts
```
==================================================
[PERINGATAN SUHU TINGGI]
==================================================
Gudang G1: Suhu 85°C
Gudang G3: Suhu 82°C
==================================================
```

### 2. Humidity Alerts
```
==================================================
[PERINGATAN KELEMBABAN TINGGI]
==================================================
Gudang G2: Kelembaban 75%
Gudang G1: Kelembaban 73%
==================================================
```

### 3. Combined Status
```
======================================================================
[STATUS GABUNGAN GUDANG]
======================================================================
Gudang G1:
  - Suhu: 84°C
  - Kelembaban: 73%
  - Status: PERINGATAN KRITIS - Bahaya tinggi! Barang berisiko rusak
----------------------------------------
Gudang G2:
  - Suhu: 78°C
  - Kelembaban: 68%
  - Status: Aman
----------------------------------------
Gudang G3:
  - Suhu: 85°C
  - Kelembaban: 65%
  - Status: Suhu tinggi, kelembaban normal
======================================================================
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Port Already in Use
```bash
# Check processes using port 9092
sudo lsof -i :9092

# Kill process if necessary
sudo kill -9 <PID>
```

#### 2. Memory Issues
```bash
# Set JAVA_OPTS for Kafka
export KAFKA_HEAP_OPTS="-Xmx512M -Xms512M"

# Set Spark memory
export SPARK_DRIVER_MEMORY=1g
export SPARK_EXECUTOR_MEMORY=1g
```

#### 3. Clear Kafka Logs
```bash
cd ~/kafka-setup/kafka_2.13-3.5.1
rm -rf /tmp/kafka-logs /tmp/zookeeper
```

#### 4. Timestamp Type Error
If you encounter timestamp type errors, ensure the consumer code properly converts string timestamps to timestamp type:
```python
.withColumn("event_time", to_timestamp(col("timestamp"))) \
.drop("timestamp") \
.withColumnRenamed("event_time", "timestamp")
```

### Verification Commands

#### Check Kafka Topics
```bash
cd ~/kafka-setup/kafka_2.13-3.5.1
bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

#### Monitor Topics Manually
```bash
# Monitor temperature topic
bin/kafka-console-consumer.sh --topic sensor-suhu-gudang --from-beginning --bootstrap-server localhost:9092

# Monitor humidity topic
bin/kafka-console-consumer.sh --topic sensor-kelembaban-gudang --from-beginning --bootstrap-server localhost:9092
```

#### Verify Java and Python
```bash
java -version
python3 --version
spark-shell --version
```

## 🏆 Learning Objectives

This project demonstrates:
- Real-time data processing with Apache Kafka
- Stream processing and filtering with PySpark
- Multi-stream joins with time windows
- Event-time processing and watermarking
- Real-time alerting systems
- Microservices architecture with message queues

## 📝 Features Implemented

- [x] Two Kafka topics: `sensor-suhu-gudang` and `sensor-kelembaban-gudang`
- [x] Temperature producer sending data every second
- [x] Humidity producer sending data every second
- [x] Support for 3 warehouses: G1, G2, G3
- [x] PySpark consumer for data consumption
- [x] Filtering: temperature > 80°C and humidity > 70%
- [x] Stream joining based on warehouse ID and time window
- [x] Critical condition detection (temperature > 80°C AND humidity > 70%)
- [x] Formatted console output with alerts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Apache Kafka Community
- Apache Spark Community
- Python Kafka Community

## 📞 Support

If you encounter any issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Verify all prerequisites are met
3. Ensure all services are running in the correct order
4. Check logs for specific error messages

---

**Happy Monitoring! 🚀**
