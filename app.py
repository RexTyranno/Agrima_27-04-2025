from flask import Flask, jsonify, send_file, abort
from tasks import generate_report, celery

app = Flask(__name__)

#report generation triggered as celery task. Report_id = task id
@app.route('/trigger_report', methods=['POST'])
def trigger_report():
    task = generate_report.delay()
    return jsonify({'report_id': task.id}), 202

#check status of report using report_id(task_id)
@app.route('/get_report/<report_id>', methods=['GET'])
def get_report(report_id):
    
    async_res = celery.AsyncResult(report_id)

    # in progress
    if not async_res.ready():
        return jsonify({'status': 'Running'}), 200

    if async_res.failed():
        return jsonify({
            'status': 'Failed',
            'error': str(async_res.result)
        }), 500

    # task succeeded so return the csv file
    csv_path = async_res.result  
    try:
        return send_file(
            csv_path,
            mimetype='text/csv',
            as_attachment=True,
            attachment_filename='store_uptime_report.csv',
            conditional=False
        )
    except FileNotFoundError:
        # If for some reason the worker returned a bad path
        abort(404, description="Report file not found")


if __name__ == '__main__':
    app.run(debug=True)
