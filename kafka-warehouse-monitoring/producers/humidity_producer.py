from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.kafka_config import KAFKA_SERVERS, TOPICS, WAREHOUSES

class HumidityProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic = TOPICS['humidity']
    
    def generate_humidity_data(self):
        """Generate random humidity data for warehouses"""
        return {
            'gudang_id': random.choice(WAREHOUSES),
            'kelembaban': random.randint(60, 80),  # Humidity range 60-80%
            'timestamp': datetime.now().isoformat()
        }
    
    def start_producing(self):
        """Start producing humidity data every second"""
        print(f"Starting Humidity Producer for topic: {self.topic}")
        try:
            while True:
                data = self.generate_humidity_data()
                self.producer.send(self.topic, data)
                print(f"Sent: {data}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("Humidity Producer stopped")
        finally:
            self.producer.close()

if __name__ == "__main__":
    producer = HumidityProducer()
    producer.start_producing()

