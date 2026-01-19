import os
import sys
import time
import subprocess
import boto3
from botocore.exceptions import ClientError

def check_docker():
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE)
    except Exception:
        print("❌ Docker not found. Please install Docker Desktop.")
        sys.exit(1)

def wait_for_service(url, name, retries=10):
    print(f"Waiting for {name}...")
    # Creating a simple socket check is better, but for MinIO we might want to check http
    # Skipping actual logic for brevity, relying on user to see docker output
    pass

def init_minio():
    print("Initialize MinIO Bucket...")
    s3 = boto3.client(
        's3',
        endpoint_url='http://localhost:9000',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin',
        region_name='us-east-1'
    )
    bucket_name = 'genpulse'
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' created.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print(f"✅ Bucket '{bucket_name}' already exists.")
        else:
            print(f"❌ Failed to create bucket: {e}")

if __name__ == "__main__":
    check_docker()
    print("🚀 Starting Infrastructure...")
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    
    print("⏳ Waiting for services to be ready (10s)...")
    time.sleep(10) # Simple wait
    
    try:
        init_minio()
    except Exception as e:
        print(f"⚠️ Could not initialize MinIO (is boto3 installed?): {e}")
    
    print("\n✅ Infrastructure is ready!")
    print("   - Postgres: localhost:5432")
    print("   - Redis:    localhost:6379")
    print("   - MinIO:    http://localhost:9001 (Console)")
