# Sistem Monitoring Gudang dengan Apache Kafka

Sistem monitoring gudang real-time menggunakan Apache Kafka dan PySpark untuk memantau sensor suhu dan kelembaban di berbagai gudang.

## Daftar Isi
- [Gambaran Umum](#gambaran-umum)
- [Fitur](#fitur)
- [Prasyarat](#prasyarat)
- [Instalasi](#instalasi)
- [Struktur Proyek](#struktur-proyek)
- [Konfigurasi](#konfigurasi)
- [Cara Penggunaan](#cara-penggunaan)
- [Output Monitoring](#output-monitoring)
- [Troubleshooting](#troubleshooting)

## Gambaran Umum

Proyek ini mensimulasikan sistem monitoring gudang real-time untuk sebuah perusahaan logistik yang mengelola beberapa gudang penyimpanan barang sensitif (makanan, obat-obatan, elektronik). Sistem memantau sensor suhu dan kelembaban yang mengirim data setiap detik dan memberikan peringatan real-time untuk kondisi kritis.

### Latar Belakang Masalah
- Beberapa gudang dengan penyimpanan barang sensitif
- Dua jenis sensor: Sensor Suhu dan Sensor Kelembaban
- Transmisi data setiap detik
- Monitoring real-time untuk mencegah kerusakan akibat suhu tinggi atau kelembaban berlebih

## Fitur

- **Streaming Data Real-time**: Producer Kafka mensimulasikan data sensor setiap detik
- **Pemrosesan Stream**: PySpark memproses stream data dengan filtering dan join
- **Sistem Peringatan**: Peringatan otomatis untuk kondisi kritis
- **Monitoring Multi-kondisi**:
  - Suhu > 80°C → Peringatan suhu tinggi
  - Kelembaban > 70% → Peringatan kelembaban tinggi
  - Kedua kondisi → Peringatan kritis
- **Time-window Joins**: Menggabungkan data suhu dan kelembaban dalam window 10 detik

## Prasyarat

- **Sistem Operasi**: Linux/WSL2
- **Java**: OpenJDK 11 atau lebih baru
- **Python**: 3.8 atau lebih baru

## Instalasi

### 1. Update Sistem dan Instalasi Java

```bash
# Update sistem
sudo apt update && sudo apt upgrade -y

# Install OpenJDK 11
sudo apt install openjdk-11-jdk -y

# Verifikasi instalasi Java
java -version

# Set environment variable JAVA_HOME
echo 'export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64' >> ~/.bashrc
echo 'export PATH=$PATH:$JAVA_HOME/bin' >> ~/.bashrc
source ~/.bashrc
```

### 2. Dependencies Python

```bash
# Install Python dan pip
sudo apt install python3 python3-pip -y

# Install library Python yang diperlukan
pip3 install kafka-python pyspark findspark
```

### 3. Instalasi Apache Kafka

```bash
# Buat direktori Kafka
mkdir ~/kafka-setup && cd ~/kafka-setup

# Download Kafka (coba beberapa opsi jika ada yang gagal)
# Opsi 1: Kafka 3.5.1
wget https://downloads.apache.org/kafka/3.5.1/kafka_2.13-3.5.1.tgz

# Opsi 2: Jika gagal, coba 3.4.1
# wget https://downloads.apache.org/kafka/3.4.1/kafka_2.13-3.4.1.tgz

# Opsi 3: Gunakan mirror archive
# wget https://archive.apache.org/dist/kafka/3.5.1/kafka_2.13-3.5.1.tgz

# Extract Kafka
tar -xzf kafka_2.13-3.5.1.tgz
cd kafka_2.13-3.5.1

# Set environment variable Kafka
echo 'export KAFKA_HOME=~/kafka-setup/kafka_2.13-3.5.1' >> ~/.bashrc
echo 'export PATH=$PATH:$KAFKA_HOME/bin' >> ~/.bashrc
source ~/.bashrc
```

### 4. Instalasi Apache Spark

```bash
# Download Spark
cd ~/kafka-setup

# Opsi 1: Spark 3.4.1 (direkomendasikan)
wget https://downloads.apache.org/spark/spark-3.4.1/spark-3.4.1-bin-hadoop3.tgz

# Opsi 2: Jika gagal, coba 3.3.4 LTS
# wget https://downloads.apache.org/spark/spark-3.3.4/spark-3.3.4-bin-hadoop3.tgz

# Opsi 3: Gunakan mirror archive
# wget https://archive.apache.org/dist/spark/spark-3.4.1/spark-3.4.1-bin-hadoop3.tgz

# Extract Spark
tar -xzf spark-3.4.1-bin-hadoop3.tgz

# Set environment variable Spark
echo 'export SPARK_HOME=~/kafka-setup/spark-3.4.1-bin-hadoop3' >> ~/.bashrc
echo 'export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin' >> ~/.bashrc
echo 'export PYSPARK_PYTHON=python3' >> ~/.bashrc
source ~/.bashrc
```

### 5. Kafka-Spark Connector

```bash
# Download file JAR yang diperlukan untuk integrasi Kafka-Spark
cd $SPARK_HOME/jars

# Untuk Spark 3.4.1
wget https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.1/spark-sql-kafka-0-10_2.12-3.4.1.jar
wget https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar
wget https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.4.1/spark-token-provider-kafka-0-10_2.12-3.4.1.jar
wget https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar
```

### 6. Membuat Topik Kafka

```bash
# Start Zookeeper (Terminal 1)
cd ~/kafka-setup/kafka_2.13-3.5.1
bin/zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka Server (Terminal 2)
cd ~/kafka-setup/kafka_2.13-3.5.1
bin/kafka-server-start.sh config/server.properties

# Buat topik (Terminal 3)
cd ~/kafka-setup/kafka_2.13-3.5.1

# Buat topik suhu
bin/kafka-topics.sh --create --topic sensor-suhu-gudang --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# Buat topik kelembaban
bin/kafka-topics.sh --create --topic sensor-kelembaban-gudang --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# Verifikasi topik
bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

## Struktur Proyek

```
kafka-warehouse-monitoring/
├── config/
│   └── kafka_config.py          # Konfigurasi Kafka
├── producers/
│   ├── temperature_producer.py  # Producer sensor suhu
│   └── humidity_producer.py     # Producer sensor kelembaban
├── consumer/
│   └── spark_consumer.py        # Consumer stream PySpark
├── README.md
└── requirements.txt
```

### Buat Struktur Proyek

```bash
# Buat direktori proyek
mkdir -p ~/kafka-warehouse-monitoring/{producers,consumer,config}
cd ~/kafka-warehouse-monitoring
```

##  Konfigurasi

### config/kafka_config.py
```python
# Konfigurasi Kafka
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

## Cara Penggunaan

### Langkah 1: Start Layanan Kafka

```bash
# Terminal 1: Start Zookeeper
cd ~/kafka-setup/kafka_2.13-3.5.1
bin/zookeeper-server-start.sh config/zookeeper.properties

# Terminal 2: Start Kafka Server
cd ~/kafka-setup/kafka_2.13-3.5.1
bin/kafka-server-start.sh config/server.properties
```

### Langkah 2: Start Producer

```bash
# Terminal 3: Start Producer Suhu
cd ~/kafka-warehouse-monitoring
python3 producers/temperature_producer.py

# Terminal 4: Start Producer Kelembaban
cd ~/kafka-warehouse-monitoring
python3 producers/humidity_producer.py
```

### Langkah 3: Start Consumer

```bash
# Terminal 5: Start Consumer PySpark
cd ~/kafka-warehouse-monitoring
python3 consumer/spark_consumer.py
```

## Output Monitoring

Sistem menghasilkan tiga jenis output monitoring:

### 1. Peringatan Suhu
```
==================================================
[PERINGATAN SUHU TINGGI]
==================================================
Gudang G1: Suhu 85°C
Gudang G3: Suhu 82°C
==================================================
```

### 2. Peringatan Kelembaban
```
==================================================
[PERINGATAN KELEMBABAN TINGGI]
==================================================
Gudang G2: Kelembaban 75%
Gudang G1: Kelembaban 73%
==================================================
```

### 3. Status Gabungan
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

## Troubleshooting

### Masalah Umum dan Solusi

#### 1. Port Sudah Digunakan
```bash
# Cek proses yang menggunakan port 9092
sudo lsof -i :9092

# Kill proses jika diperlukan
sudo kill -9 <PID>
```

#### 2. Masalah Memory
```bash
# Set JAVA_OPTS untuk Kafka
export KAFKA_HEAP_OPTS="-Xmx512M -Xms512M"

# Set memory Spark
export SPARK_DRIVER_MEMORY=1g
export SPARK_EXECUTOR_MEMORY=1g
```

#### 3. Bersihkan Log Kafka
```bash
cd ~/kafka-setup/kafka_2.13-3.5.1
rm -rf /tmp/kafka-logs /tmp/zookeeper
```

#### 4. Error Tipe Timestamp
Jika mengalami error tipe timestamp, pastikan kode consumer mengkonversi string timestamp ke tipe timestamp dengan benar:
```python
.withColumn("event_time", to_timestamp(col("timestamp"))) \
.drop("timestamp") \
.withColumnRenamed("event_time", "timestamp")
```

### Perintah Verifikasi

#### Cek Topik Kafka
```bash
cd ~/kafka-setup/kafka_2.13-3.5.1
bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

#### Monitor Topik Manual
```bash
# Monitor topik suhu
bin/kafka-console-consumer.sh --topic sensor-suhu-gudang --from-beginning --bootstrap-server localhost:9092

# Monitor topik kelembaban
bin/kafka-console-consumer.sh --topic sensor-kelembaban-gudang --from-beginning --bootstrap-server localhost:9092
```

#### Verifikasi Java dan Python
```bash
java -version
python3 --version
spark-shell --version
```
