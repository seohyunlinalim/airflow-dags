import airflow 
from datetime import timedelta 
from airflow import DAG 
from datetime import datetime, timedelta 
from airflow.operators.python import PythonOperator 
from airflow.operators.email import EmailOperator
from airflow.sensors.python import PythonSensor
from email_threads import check_for_response
from jinja2 import Environment, FileSystemLoader
import os

receiver = 'seohyunlim98@gmail.com'
subject = 'Alert Test Mail 9'

default_args = { 
    # 'owner': 'airflow', 
    # 'start_date': airflow.utils.dates.days_ago(2), 
    # 'end_date': datetime(), 
    # 'depends_on_past': False, 
    'email': ['linapenguin@gmail.com'], 
    'email_on_failure': True, 
    # 'email_on_retry': False, 
    # If a task fails, retry it once after waiting 
    # at least 5 minutes 
    # 'retries': 1, 'retry_delay': timedelta(minutes=5), 
    }

dag_email = DAG( 
    dag_id = 'email_operator', 
    default_args=default_args,
    schedule_interval='@once', 
    dagrun_timeout=timedelta(minutes=60), 
    description='use case of email operator in airflow', 
    start_date = airflow.utils.dates.days_ago(1))

def start_task_func(): 
    print("task started") 

start_task = PythonOperator( 
    task_id='execute_task', 
    python_callable=start_task_func, 
    dag=dag_email) 


current_directory = os.path.dirname(os.path.abspath(__file__))
env = Environment(loader=FileSystemLoader(current_directory))

# def approve():
#     return env.get_template('approved_email.j2').render()

# def reject():
#     return env.get_template('rejected_email.j2').render()

send_email = EmailOperator( 
    task_id='send_email', 
    to=receiver, 
    subject=subject, 
    html_content=env.get_template('email_template.j2').render(), 
    dag=dag_email)

start_task >> send_email

def response_callable():
    if check_for_response(receiver, subject): # if an unread response exists
        return True

wait_for_email = PythonSensor( # checks every minute (default)
    task_id='wait_for_response',
    python_callable=response_callable,
    dag=dag_email
)
    
send_email >> wait_for_email

def end_task_func(): 
    print("task ended") 

end_task = PythonOperator( 
    task_id='end_task', 
    python_callable=end_task_func, 
    dag=dag_email) 

wait_for_email >> end_task

if __name__ == "__main__": 
    dag_email.cli()