from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.kafka_config import KAFKA_SERVERS, TOPICS, WAREHOUSES

class TemperatureProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic = TOPICS['temperature']
    
    def generate_temperature_data(self):
        """Generate random temperature data for warehouses"""
        return {
            'gudang_id': random.choice(WAREHOUSES),
            'suhu': random.randint(75, 90),  # Temperature range 75-90°C
            'timestamp': datetime.now().isoformat()
        }
    
    def start_producing(self):
        """Start producing temperature data every second"""
        print(f"Starting Temperature Producer for topic: {self.topic}")
        try:
            while True:
                data = self.generate_temperature_data()
                self.producer.send(self.topic, data)
                print(f"Sent: {data}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("Temperature Producer stopped")
        finally:
            self.producer.close()

if __name__ == "__main__":
    producer = TemperatureProducer()
    producer.start_producing()
