import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, date, time
import pytz
import csv
from collections import defaultdict
import os
import dotenv

dotenv.load_dotenv()

DB_CONN_PARAMS = dict(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
)

DEFAULT_TZ = "America/Chicago"

def python_to_menu_dow(py_date):
    return (py_date.weekday() + 1) % 7

def main(task_id=None):
    now_utc = datetime.now(pytz.UTC)
    
    windows = {
        'last_hour':  (now_utc - timedelta(hours=1), now_utc),
        'last_day':   (now_utc - timedelta(days=1), now_utc),
        'last_week':  (now_utc - timedelta(weeks=1), now_utc),
    }

    conn = psycopg2.connect(**DB_CONN_PARAMS)
    try:
        # batch queries for optimisation
        store_timezones = get_all_timezones(conn)
        store_hours = get_all_store_hours(conn)
        store_statuses = get_all_store_statuses(conn, min(w[0] for w in windows.values()))

        report = []
        for store_id in store_statuses.keys():
            row = {'store_id': store_id}
            for name, (start, end) in windows.items():
                up_s, down_s = compute_uptime_downtime(
                    store_id, start, end,
                    store_timezones.get(store_id, DEFAULT_TZ),
                    store_hours.get(store_id, {}),
                    store_statuses[store_id]
                )

                if name == 'last_hour':
                    row['uptime_last_hour'] = up_s / 60.0
                    row['downtime_last_hour'] = down_s / 60.0
                else:
                    row[f'uptime_{name}'] = up_s / 3600.0
                    row[f'downtime_{name}'] = down_s / 3600.0
            report.append(row)

        filename = write_report_to_csv(report, task_id)
        print(f"Report saved as {filename}")
        return filename
    finally:
        conn.close()

def get_all_timezones(conn):
    timezones = {}
    with conn.cursor() as cur:
        cur.execute("SELECT store_id, timezone_str FROM timezones")
        for store_id, tz_str in cur:
            timezones[store_id] = tz_str
    return timezones

def get_all_store_hours(conn):
    store_hours = defaultdict(lambda: defaultdict(list))
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT store_id, dayofweek, start_time_local, end_time_local
            FROM menu_hours
        """)
        for row in cur:
            store_hours[row['store_id']][row['dayofweek']].append({
                'start_time_local': row['start_time_local'],
                'end_time_local': row['end_time_local']
            })
    return store_hours

def get_all_store_statuses(conn, earliest_time):
    store_statuses = defaultdict(list)
    store_ids = set()
    with conn.cursor() as cur:
        cur.execute("SELECT store_id FROM store_status")
        for (id_value,) in cur.fetchall():
            store_ids.add(id_value)

        for store_id in store_ids:
            cur.execute("""
                SELECT timestamp_utc, status
                FROM store_status
                WHERE store_id = %s AND timestamp_utc < %s
                ORDER BY timestamp_utc DESC
                LIMIT 1
            """, (store_id, earliest_time))
            pre = cur.fetchone()
            
            statuses = []
            if pre:
                statuses.append({
                    'timestamp_utc': earliest_time,
                    'status': pre[1]  
                })

            cur.execute("""
                SELECT timestamp_utc, status
                FROM store_status
                WHERE store_id = %s AND timestamp_utc >= %s
                ORDER BY timestamp_utc ASC
            """, (store_id, earliest_time))
            
            in_window = cur.fetchall()
            if not pre and in_window:
                statuses.append({
                    'timestamp_utc': earliest_time,
                    'status': in_window[0][1]
                })
            elif not pre and not in_window:
                statuses.append({
                    'timestamp_utc': earliest_time,
                    'status': 'inactive'
                })
            
            for row in in_window:
                # Fix for timestamp with timezone offset
                timestamp = row[0]
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp).astimezone(pytz.UTC)
                
                statuses.append({
                    'timestamp_utc': timestamp, 
                    'status': row[1]
                })
            
            store_statuses[store_id] = statuses
    return store_statuses

def get_business_intervals(store_id, window_start_utc, window_end_utc, tz_name, store_hours):
    tz = pytz.timezone(tz_name)

    local_start = window_start_utc.astimezone(tz)
    local_end = window_end_utc.astimezone(tz)

    intervals_utc = []
    cur_date = local_start.date()
    last_date = local_end.date()
    
    while cur_date <= last_date:
        dow = python_to_menu_dow(cur_date)
        hours_today = store_hours.get(dow, [])
        
        if not hours_today:
            hours_today = [{'start_time_local': time(0, 0),
                          'end_time_local': time(23, 59, 59)}]
        
        for hour in hours_today:
            local_s = tz.localize(datetime.combine(cur_date, hour['start_time_local']))
            local_e = tz.localize(datetime.combine(cur_date, hour['end_time_local']))

            utc_s = local_s.astimezone(pytz.utc)
            utc_e = local_e.astimezone(pytz.utc)

            seg_s = max(utc_s, window_start_utc)
            seg_e = min(utc_e, window_end_utc)
            
            if seg_e > seg_s:
                intervals_utc.append((seg_s, seg_e))
        cur_date += timedelta(days=1)
    
    if intervals_utc:
        intervals_utc.sort()
        merged = []
        for s, e in intervals_utc:
            if not merged or s > merged[-1][1]:
                merged.append((s, e))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        
        return merged
    
    return []

def compute_uptime_downtime(store_id, window_start, window_end, tz_name, store_hours, statuses):
    business_intervals = get_business_intervals(
        store_id, window_start, window_end, tz_name, store_hours
    )

    timeline = [s for s in statuses if window_start <= s['timestamp_utc'] <= window_end]

    if not timeline or timeline[0]['timestamp_utc'] > window_start:
        pre_window = [s for s in statuses if s['timestamp_utc'] <= window_start]
        if pre_window:
            timeline.insert(0, {
                'timestamp_utc': window_start,
                'status': pre_window[-1]['status']
            })
        else:
            timeline.insert(0, {
                'timestamp_utc': window_start,
                'status': 'inactive'
            })
    
    if not timeline or timeline[-1]['timestamp_utc'] < window_end:
        last_status = 'inactive'
        if timeline:
            last_status = timeline[-1]['status']
        
        timeline.append({
            'timestamp_utc': window_end,
            'status': last_status
        })
    
    up_seconds = 0
    down_seconds = 0

    for i in range(len(timeline) - 1):
        seg_s = timeline[i]['timestamp_utc']
        seg_e = timeline[i+1]['timestamp_utc']
        state = timeline[i]['status']
        
        if seg_e <= seg_s:
            continue
        
        for b_s, b_e in business_intervals:
            overlap_start = max(seg_s, b_s)
            overlap_end = min(seg_e, b_e)
            
            if overlap_end > overlap_start:
                duration = (overlap_end - overlap_start).total_seconds()
                if state == 'active':
                    up_seconds += duration
                else:
                    down_seconds += duration
    
    return up_seconds, down_seconds

def write_report_to_csv(report, task_id=None):
    fieldnames = [
        'store_id',
        'uptime_last_hour', 'downtime_last_hour',
        'uptime_last_day', 'downtime_last_day',
        'uptime_last_week', 'downtime_last_week',
    ]
    
    # Create reports directory if it doesn't exist
    reports_dir = os.path.join('data', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Create filename with task_id if provided
    filename = f"store_uptime_report_{task_id}.csv" if task_id else "store_uptime_report.csv"
    filepath = os.path.join(reports_dir, filename)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in report:
            writer.writerow(row)
    
    return filepath
