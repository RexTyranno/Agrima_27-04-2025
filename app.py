from flask import Flask, jsonify, send_file, abort
from tasks import generate_report, celery
import os

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
    if not csv_path:  # if none 
        return jsonify({
            'status': 'Completed',
            'error': 'No report path returned from task'
        }), 500
        
    try:
        if not os.path.exists(csv_path):
            return jsonify({
                'status': 'Completed', 
                'error': f'File not found at path: {csv_path}'
            }), 404
            
        return send_file(
            csv_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name='store_uptime_report.csv',
            conditional=False
        )
    except Exception as e:
        return jsonify({
            'status': 'Error',
            'error': f'Error accessing report file: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
