from tasks import generate_report

if __name__ == '__main__':
    # task is added to the queue
    result = generate_report.delay()
    print(f"Dispatched report generation task → task id: {result.id!r}")
