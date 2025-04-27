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

# Database connection settings
DB_CONFIG = {
    'user': clean_env_var("DB_USER"),
    'password': clean_env_var("DB_PASSWORD"),
    'host': clean_env_var("DB_HOST"),
    'port': clean_env_var("DB_PORT", "5432"),
    'dbname': clean_env_var("DB_NAME")
}

# Application settings
DEBUG = True
REPORTS_DIR = os.path.join('data', 'reports')
