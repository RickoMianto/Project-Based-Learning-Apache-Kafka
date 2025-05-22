from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
import sys
import os
import threading
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.kafka_config import KAFKA_SERVERS, TOPICS

class WarehouseMonitoring:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("WarehouseMonitoring") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        
        # Lock untuk thread-safe printing
        self.print_lock = threading.Lock()
    
    def safe_print(self, message):
        """Thread-safe printing method"""
        with self.print_lock:
            print(message)
            # Flush output untuk memastikan langsung tampil
            sys.stdout.flush()
    
    def create_kafka_stream(self, topic):
        """Create Kafka stream for given topic"""
        return self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", ",".join(KAFKA_SERVERS)) \
            .option("subscribe", topic) \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
    
    def process_temperature_stream(self):
        """Process temperature stream and filter high temperature"""
        temp_stream = self.create_kafka_stream(TOPICS['temperature'])
        
        # Define schema for temperature data
        temp_schema = StructType([
            StructField("gudang_id", StringType()),
            StructField("suhu", IntegerType()),
            StructField("timestamp", StringType())
        ])
        
        # Parse JSON and convert timestamp to proper timestamp type
        temp_parsed = temp_stream.select(
            from_json(col("value").cast("string"), temp_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp") \
         .withColumn("event_time", to_timestamp(col("timestamp"))) \
         .drop("timestamp") \
         .withColumnRenamed("event_time", "timestamp")
        
        # Filter temperature > 80°C
        high_temp = temp_parsed.filter(col("suhu") > 80)
        
        return high_temp, temp_parsed
    
    def process_humidity_stream(self):
        """Process humidity stream and filter high humidity"""
        humidity_stream = self.create_kafka_stream(TOPICS['humidity'])
        
        # Define schema for humidity data
        humidity_schema = StructType([
            StructField("gudang_id", StringType()),
            StructField("kelembaban", IntegerType()),
            StructField("timestamp", StringType())
        ])
        
        # Parse JSON and convert timestamp to proper timestamp type
        humidity_parsed = humidity_stream.select(
            from_json(col("value").cast("string"), humidity_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp") \
         .withColumn("event_time", to_timestamp(col("timestamp"))) \
         .drop("timestamp") \
         .withColumnRenamed("event_time", "timestamp")
        
        # Filter humidity > 70%
        high_humidity = humidity_parsed.filter(col("kelembaban") > 70)
        
        return high_humidity, humidity_parsed
    
    def join_streams_and_detect_critical(self, temp_stream, humidity_stream):
        """Join temperature and humidity streams to detect critical conditions"""
        
        # Add watermark for event time processing
        temp_with_watermark = temp_stream.withWatermark("timestamp", "10 seconds")
        humidity_with_watermark = humidity_stream.withWatermark("timestamp", "10 seconds")
        
        # Join streams based on gudang_id and time window
        joined_stream = temp_with_watermark.alias("temp").join(
            humidity_with_watermark.alias("humidity"),
            expr("""
                temp.gudang_id = humidity.gudang_id AND
                temp.timestamp >= humidity.timestamp - interval 10 seconds AND
                temp.timestamp <= humidity.timestamp + interval 10 seconds
            """),
            "inner"
        ).select(
            col("temp.gudang_id").alias("gudang_id"),
            col("temp.suhu").alias("suhu"),
            col("humidity.kelembaban").alias("kelembaban"),
            col("temp.timestamp").alias("timestamp")
        )
        
        # Add status column based on conditions
        status_stream = joined_stream.withColumn(
            "status",
            when((col("suhu") > 80) & (col("kelembaban") > 70), "PERINGATAN KRITIS - Bahaya tinggi! Barang berisiko rusak")
            .when(col("suhu") > 80, "Suhu tinggi, kelembaban normal")
            .when(col("kelembaban") > 70, "Kelembaban tinggi, suhu aman")
            .otherwise("Aman")
        )
        
        return status_stream
    
    def print_temperature_alerts(self, high_temp_stream):
        """Print temperature alerts using thread-safe method"""
        def process_temp_batch(df, epoch_id):
            if not df.isEmpty():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Build complete output string
                output_lines = []
                output_lines.append("")
                output_lines.append("="*50)
                output_lines.append(f"[PERINGATAN SUHU TINGGI] - {timestamp}")
                output_lines.append("="*50)
                
                for row in df.collect():
                    output_lines.append(f"Gudang {row.gudang_id}: Suhu {row.suhu}°C")
                
                output_lines.append("="*50)
                
                # Print as single block
                self.safe_print("\n".join(output_lines))
        
        return high_temp_stream.writeStream \
            .outputMode("append") \
            .foreachBatch(process_temp_batch) \
            .option("checkpointLocation", "/tmp/checkpoint/temp") \
            .trigger(processingTime='5 seconds') \
            .start()
    
    def print_humidity_alerts(self, high_humidity_stream):
        """Print humidity alerts using thread-safe method"""
        def process_humidity_batch(df, epoch_id):
            if not df.isEmpty():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Build complete output string
                output_lines = []
                output_lines.append("")
                output_lines.append("="*50)
                output_lines.append(f"[PERINGATAN KELEMBABAN TINGGI] - {timestamp}")
                output_lines.append("="*50)
                
                for row in df.collect():
                    output_lines.append(f"Gudang {row.gudang_id}: Kelembaban {row.kelembaban}%")
                
                output_lines.append("="*50)
                
                # Print as single block
                self.safe_print("\n".join(output_lines))
        
        return high_humidity_stream.writeStream \
            .outputMode("append") \
            .foreachBatch(process_humidity_batch) \
            .option("checkpointLocation", "/tmp/checkpoint/humidity") \
            .trigger(processingTime='6 seconds') \
            .start()
    
    def print_combined_status(self, combined_stream):
        """Print combined warehouse status using thread-safe method"""
        def process_combined_batch(df, epoch_id):
            if not df.isEmpty():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Build complete output string
                output_lines = []
                output_lines.append("")
                output_lines.append("="*70)
                output_lines.append(f"[STATUS GABUNGAN GUDANG] - {timestamp}")
                output_lines.append("="*70)
                
                for row in df.collect():
                    output_lines.append(f"Gudang {row.gudang_id}:")
                    output_lines.append(f"  - Suhu: {row.suhu}°C")
                    output_lines.append(f"  - Kelembaban: {row.kelembaban}%")
                    output_lines.append(f"  - Status: {row.status}")
                    output_lines.append("-" * 40)
                
                output_lines.append("="*70)
                
                # Print as single block
                self.safe_print("\n".join(output_lines))
        
        return combined_stream.writeStream \
            .outputMode("append") \
            .foreachBatch(process_combined_batch) \
            .option("checkpointLocation", "/tmp/checkpoint/combined") \
            .trigger(processingTime='8 seconds') \
            .start()
    
    def start_monitoring(self):
        """Start the warehouse monitoring system"""
        print("Starting Warehouse Monitoring System...")
        print("Monitoring temperature and humidity from Kafka streams...")
        
        try:
            # Process temperature stream
            high_temp_stream, temp_stream = self.process_temperature_stream()
            
            # Process humidity stream  
            high_humidity_stream, humidity_stream = self.process_humidity_stream()
            
            # Join streams for combined analysis
            combined_stream = self.join_streams_and_detect_critical(temp_stream, humidity_stream)
            
            # Start streaming queries dengan trigger yang benar
            temp_query = self.print_temperature_alerts(high_temp_stream)
            humidity_query = self.print_humidity_alerts(high_humidity_stream)
            combined_query = self.print_combined_status(combined_stream)
            
            print("All streaming queries started successfully!")
            print("Press Ctrl+C to stop monitoring...")
            
            # Wait for termination
            temp_query.awaitTermination()
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        except Exception as e:
            print(f"Error occurred: {str(e)}")
        finally:
            self.spark.stop()

if __name__ == "__main__":
    monitor = WarehouseMonitoring()
    monitor.start_monitoring()
