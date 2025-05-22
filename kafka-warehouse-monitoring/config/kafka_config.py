# config/kafka_config.py
KAFKA_SERVERS = ['localhost:9092']
TOPICS = {
    'temperature': 'sensor-suhu-gudang',
    'humidity': 'sensor-kelembaban-gudang'
}
WAREHOUSES = ['G1', 'G2', 'G3']

