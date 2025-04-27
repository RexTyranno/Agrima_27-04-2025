from celery import Celery
import celeryconfig
from core.report_generator import main as generate_report_main

# create Celery app
celery = Celery('report_tasks')
celery.config_from_object(celeryconfig)

@celery.task(name='report_tasks.generate_report')
def generate_report():
    # Get the current task ID and pass it to the main function
    task_id = generate_report.request.id
    output_file = generate_report_main(task_id)
    return output_file

