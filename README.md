# Airflow Clickstream Pipeline

An automated data pipeline built with Apache Airflow that orchestrates 
the entire clickstream analytics workflow on AWS.

## Architecture
Airflow DAG (daily schedule)
↓
Task 1: Generate Events → sends 50 events to AWS SQS
↓
Task 2: Verify S3 Files → confirms data landed in S3
↓
Task 3: Run Glue Crawler → catalogs schema in Glue
↓
Task 4: Run Glue ETL → converts JSON to Parquet
↓
Task 5: Send Notification → pipeline complete!

## AWS Services Used

- Amazon SQS — event queue buffer
- AWS Lambda — serverless event processing
- Amazon S3 — data lake storage
- AWS Glue Crawler — schema cataloging
- AWS Glue ETL — JSON to Parquet conversion
- Amazon Athena — SQL analytics

## Tech Stack

- Apache Airflow 2.11.2
- Python 3.12
- Ubuntu (WSL)
- AWS boto3

## Setup Instructions

### Prerequisites
- Ubuntu/WSL installed
- Python 3.12
- AWS account with credentials

### Installation

1. Create virtual environment:
```bash
mkdir ~/airflow-project
cd ~/airflow-project
python3 -m venv airflow-env
source airflow-env/bin/activate
```

2. Install Airflow:
```bash
pip install "apache-airflow==2.11.2" \
--constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.11.2/constraints-3.12.txt"
```

3. Install providers:
```bash
pip install apache-airflow-providers-amazon faker
```

4. Initialize database:
```bash
export AIRFLOW_HOME=~/airflow-project/airflow-home
airflow db init
```

5. Create admin user:
```bash
airflow users create \
    --username admin \
    --firstname Your Name \
    --role Admin \
    --email your@email.com \
    --password yourpassword
```

6. Copy DAG file:
```bash
cp dags/clickstream_pipeline.py ~/airflow-project/airflow-home/dags/
```

7. Add your AWS credentials in the DAG file:
```python
AWS_ACCESS_KEY = 'your-access-key'
AWS_SECRET_KEY = 'your-secret-key'
```

### Running Airflow

Terminal 1 — Start webserver:
```bash
cd ~/airflow-project
source airflow-env/bin/activate
export AIRFLOW_HOME=~/airflow-project/airflow-home
airflow webserver --port 8080
```

Terminal 2 — Start scheduler:
```bash
cd ~/airflow-project
source airflow-env/bin/activate
export AIRFLOW_HOME=~/airflow-project/airflow-home
airflow scheduler
```

Open browser:http://localhost:8080/
## DAG Structure
clickstream_pipeline_aws
├── generate_events    → sends events to SQS
├── verify_s3_files    → checks S3 for files
├── run_glue_crawler   → starts Glue crawler
├── run_glue_etl       → starts Glue ETL job
└── send_notification  → logs success message

## Key Concepts Learned

- DAG definition and structure
- PythonOperator for custom tasks
- Task dependencies with >> operator
- XCom for passing data between tasks
- Connecting Airflow to AWS using boto3
- Scheduling pipelines automatically

## Related Project

This project automates the pipeline built in:
[clickstream-aws-pipeline](https://github.com/praveen12194-gif/clickstream-aws-pipeline)