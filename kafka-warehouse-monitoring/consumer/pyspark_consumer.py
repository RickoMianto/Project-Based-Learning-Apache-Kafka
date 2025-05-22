from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.kafka_config import KAFKA_SERVERS, TOPICS

class WarehouseMonitoring:
    def __init__(self):
        # Create unique checkpoint directory to avoid state conflicts
        checkpoint_dir = f"/tmp/checkpoint_{int(time.time())}"
        
        self.spark = SparkSession.builder \
            .appName("WarehouseMonitoring") \
            .config("spark.sql.streaming.checkpointLocation", checkpoint_dir) \
            .getOrCreate()
        
        # Set log level to ERROR to suppress warnings
        self.spark.sparkContext.setLogLevel("ERROR")
        self.batch_counter = 0
    
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
            when((col("suhu") > 80) & (col("kelembaban") > 70), "Bahaya tinggi! Barang berisiko rusak")
            .when(col("suhu") > 80, "Suhu tinggi, kelembaban normal")
            .when(col("kelembaban") > 70, "Kelembaban tinggi, suhu aman")
            .otherwise("Aman")
        )
        
        return status_stream
    
    def print_table_border(self, widths, char="-"):
        """Print table border"""
        border = "+"
        for width in widths:
            border += char * (width + 2) + "+"
        print(border)
    
    def print_table_row(self, values, widths):
        """Print table row with proper formatting"""
        row = "|"
        for i, value in enumerate(values):
            formatted_value = str(value).ljust(widths[i])
            row += f" {formatted_value} |"
        print(row)
    
    def print_humidity_table(self, df):
        """Print humidity data in table format"""
        if df.isEmpty():
            return
        
        print("\n" + "="*50)
        print(f"Batch: {self.batch_counter}")
        print("="*50)
        
        # Column widths
        widths = [10, 11, 19]  # gudang_id, kelembaban, timestamp
        
        # Print table header
        self.print_table_border(widths)
        self.print_table_row(["gudang_id", "kelembaban", "timestamp"], widths)
        self.print_table_border(widths)
        
        # Print data rows
        rows = df.select("gudang_id", "kelembaban", "timestamp").collect()
        for row in rows:
            timestamp_str = row.timestamp.strftime("%Y-%m-%d %H:%M:%S") if row.timestamp else "N/A"
            self.print_table_row([row.gudang_id, row.kelembaban, timestamp_str], widths)
        
        self.print_table_border(widths)
    
    def print_temperature_table(self, df):
        """Print temperature data in table format"""
        if df.isEmpty():
            return
        
        # Column widths for temperature table
        widths = [10, 5, 19]  # gudang_id, suhu, timestamp
        
        # Print table header
        self.print_table_border(widths)
        self.print_table_row(["gudang_id", "suhu", "timestamp"], widths)
        self.print_table_border(widths)
        
        # Print data rows
        rows = df.select("gudang_id", "suhu", "timestamp").collect()
        for row in rows:
            timestamp_str = row.timestamp.strftime("%Y-%m-%d %H:%M:%S") if row.timestamp else "N/A"
            self.print_table_row([row.gudang_id, row.suhu, timestamp_str], widths)
        
        self.print_table_border(widths)
    
    def print_combined_table(self, df):
        """Print combined data in table format"""
        if df.isEmpty():
            return
        
        print(f"\nBatch: {self.batch_counter}")
        print("="*50)
        
        # Column widths for combined table
        widths = [10, 5, 11, 35]  # gudang_id, suhu, kelembaban, status
        
        # Print table header
        self.print_table_border(widths)
        self.print_table_row(["gudang_id", "suhu", "kelembaban", "status"], widths)
        self.print_table_border(widths)
        
        # Print data rows
        rows = df.select("gudang_id", "suhu", "kelembaban", "status").collect()
        for row in rows:
            self.print_table_row([row.gudang_id, row.suhu, row.kelembaban, row.status], widths)
        
        self.print_table_border(widths)
    
    def print_temperature_alerts(self, high_temp_stream):
        """Print temperature alerts in table format"""
        def process_temp_batch(df, epoch_id):
            if not df.isEmpty():
                self.batch_counter += 1
                print("\n[PERINGATAN SUHU TINGGI]")
                self.print_temperature_table(df)
        
        return high_temp_stream.writeStream \
            .outputMode("append") \
            .foreachBatch(process_temp_batch) \
            .start()
    
    def print_humidity_alerts(self, high_humidity_stream):
        """Print humidity alerts in table format"""
        def process_humidity_batch(df, epoch_id):
            if not df.isEmpty():
                self.print_humidity_table(df)
        
        return high_humidity_stream.writeStream \
            .outputMode("append") \
            .foreachBatch(process_humidity_batch) \
            .start()
    
    def print_combined_status(self, combined_stream):
        """Print combined warehouse status in table format"""
        def process_combined_batch(df, epoch_id):
            if not df.isEmpty():
                self.print_combined_table(df)
        
        return combined_stream.writeStream \
            .outputMode("append") \
            .foreachBatch(process_combined_batch) \
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
            
            # Start streaming queries
            temp_query = self.print_temperature_alerts(high_temp_stream)
            humidity_query = self.print_humidity_alerts(high_humidity_stream)
            combined_query = self.print_combined_status(combined_stream)
            
            # Wait for termination
            temp_query.awaitTermination()
            humidity_query.awaitTermination()
            combined_query.awaitTermination()
            
        except KeyboardInterrupt:
            print("Monitoring stopped by user")
        finally:
            self.spark.stop()

if __name__ == "__main__":
    monitor = WarehouseMonitoring()
    monitor.start_monitoring()
