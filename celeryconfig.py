import os
import dotenv

dotenv.load_dotenv()

def clean_env_var(var_name, default=""):
    value = os.getenv(var_name, default)
    if value and (
        (value.startswith('"') and value.endswith('"')) or 
        (value.startswith("'") and value.endswith("'"))
    ):
        value = value[1:-1]
    return value

broker_url = 'pyamqp://guest:guest@localhost:5672//'

result_backend = 'db+postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
    user=clean_env_var("DB_USER"),
    password=clean_env_var("DB_PASSWORD"),
    host=clean_env_var("DB_HOST"),
    port=clean_env_var("DB_PORT", "5432"),
    dbname=clean_env_var("DB_NAME")
)

database_table_names = {
    'task': 'celery_taskmeta',
    'group': 'celery_tasksetmeta',
}
