from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import boto3
import json
import random
from faker import Faker

fake = Faker()

default_args = {
    'owner': 'praveen',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

AWS_ACCESS_KEY = 'YOUR AWS ACCESS KEY'
AWS_SECRET_KEY = 'YOUR SECRETE KEY'
REGION = 'us-east-1'
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/287553036629/clickstream-queue'
BUCKET = 'clickstream-processed-pk'

dag = DAG(
    'clickstream_pipeline_aws',
    default_args=default_args,
    description='Real clickstream pipeline connected to AWS',
    schedule_interval='@daily',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['clickstream', 'aws'],
)

def generate_and_send_events():
    sqs = boto3.client(
        'sqs',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION
    )
    PAGES = ['/home', '/products', '/cart', '/checkout']
    EVENTS = ['page_view', 'click', 'add_to_cart', 'purchase']
    WEIGHTS = [50, 30, 15, 5]
    events_sent = 0
    for _ in range(50):
        event = {
            'event_id':   fake.uuid4(),
            'user_id':    f'user_{random.randint(1, 500)}',
            'event_type': random.choices(EVENTS, weights=WEIGHTS)[0],
            'page':       random.choice(PAGES),
            'timestamp':  datetime.utcnow().isoformat(),
            'device':     random.choice(['mobile', 'desktop', 'tablet']),
            'country':    fake.country_code()
        }
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(event)
        )
        events_sent += 1
    print(f'Sent {events_sent} events to SQS!')
    return events_sent

def verify_s3_files():
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION
    )
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix='events/')
    files = response.get('Contents', [])
    print(f'Found {len(files)} files in S3!')
    if len(files) == 0:
        raise ValueError('No files found in S3!')
    return len(files)

def trigger_glue_crawler():
    glue = boto3.client(
        'glue',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION
    )
    glue.start_crawler(Name='clickstream-crawler')
    print('Glue crawler started!')
    return 'crawler_started'

def trigger_glue_etl():
    glue = boto3.client(
        'glue',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION
    )
    # Check if job is already running
    response = glue.get_job_runs(JobName='clickstream-json-to-parquet')
    runs = response.get('JobRuns', [])
    
    for run in runs:
        if run['JobRunState'] in ['STARTING', 'RUNNING', 'STOPPING']:
            print(f'Job already running! State: {run["JobRunState"]}')
            print('Skipping this run...')
            return 'job_already_running'
    
    # Start job if not running
    glue.start_job_run(JobName='clickstream-json-to-parquet')
    print('Glue ETL job started!')
    return 'etl_started'

def send_notification(**context):
    events = context['task_instance'].xcom_pull(
        task_ids='generate_events'
    )
    print(f'Pipeline completed!')
    print(f'Events sent to SQS: {events}')
    print(f'Data available in Athena!')

task1 = PythonOperator(
    task_id='generate_events',
    python_callable=generate_and_send_events,
    dag=dag,
)

task2 = PythonOperator(
    task_id='verify_s3_files',
    python_callable=verify_s3_files,
    dag=dag,
)

task3 = PythonOperator(
    task_id='run_glue_crawler',
    python_callable=trigger_glue_crawler,
    dag=dag,
)

task4 = PythonOperator(
    task_id='run_glue_etl',
    python_callable=trigger_glue_etl,
    dag=dag,
)

task5 = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification,
    dag=dag,
)

