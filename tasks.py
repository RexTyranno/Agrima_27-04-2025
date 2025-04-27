# tasks.py
from celery import Celery
import celeryconfig
import report

# create Celery app
celery = Celery('report_tasks')
celery.config_from_object(celeryconfig)

@celery.task(name='report_tasks.generate_report')
def generate_report():
    # run worker
    output_file = report.run_report()
    return output_file

