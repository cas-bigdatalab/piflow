import psycopg2

from infra.config_loader import get_settings

def get_connection():
    settings = get_settings()
    db = settings.database
    return psycopg2.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        dbname=db.name,
        connect_timeout=10,
    )