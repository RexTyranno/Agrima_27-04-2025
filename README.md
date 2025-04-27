A system that generates reports on store uptime and downtime based on status data. This application monitors store activity, calculates uptime/downtime metrics across different time windows, and provides an API to request and download reports.

## Features

- Generate uptime/downtime reports for stores across multiple time windows (last hour, day, week)
- RESTful API endpoints for triggering reports and retrieving results
- Asynchronous task processing with Celery
- Database storage of store status data and business hours
- Timezone-aware calculations for accurate business hour reporting

## Technologies

- Python3
- Flask
- Celery
- PostgreSQL
- RabbitMQ

## Installation

1. Clone the repository
2. Create a virtual environment and activate it
   ```
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # OR
   .venv\Scripts\activate     # Windows
   ```
3. Install dependencies
   ```
   pip install -r requirements.txt
   ```
4. Configure environment variables (create a `.env` file)
   ```
   DB_NAME=database_name
   DB_USER=database_user
   DB_PASSWORD=database_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

## Usage

### Running the API server

flask run

### Triggering a report

Trigger report generation by sending a POST request to the `/trigger_report` endpoint. Use postman or curl to send the request.
curl -X POST http://localhost:5000/trigger_report

This will dispatch a report generation task and display the task ID.

### Checking the status of a report

Check the status of a report by sending a GET request to the `/check_status` endpoint. Use postman or curl to send the request.
curl http://localhost:5000/check_status

This will return the status of the report.

## Project Structure

- `/api` - API routes and endpoints
- `/core` - Core logic
- `/config` - Configuration settings
- `/data/reports` - Generated report files
- `app.py` - Flask application entry point
- `tasks.py` - Celery task definitions
- `celeryconfig.py` - Celery configuration
- `run_task.py` - Command-line script to trigger tasks

## Report Format

The generated reports include the following metrics for each store:

- `store_id` - The unique identifier for the store
- `uptime_last_hour` - Uptime in minutes for the last hour
- `downtime_last_hour` - Downtime in minutes for the last hour
- `uptime_last_day` - Uptime in hours for the last day
- `downtime_last_day` - Downtime in hours for the last day
- `uptime_last_week` - Uptime in hours for the last week
- `downtime_last_week` - Downtime in hours for the last week

## Development

To set up the development environment:

1. Install RabbitMQ (or another message broker compatible with Celery)
2. Start the Celery worker:
   ```
   celery -A tasks worker --loglevel=info
   ```
3. Run the Flask development server:
   ```
   flask run
   ```

## Suggestions for improvement

- Instead of running SQL queries directly in the report.py file, we can use a database ORM like SQLAlchemy to connect to the database.
- Instead of using a CSV file to store the report, we can use a database table to store the report.
