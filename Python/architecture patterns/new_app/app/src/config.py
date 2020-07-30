import os

from sqlalchemy import create_engine

from adapters.orm import metadata

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/db'


def get_postgres_uri(local: bool = False):
    host_string = '192.168.99.100'
    host_port = 54321
    if local:
        host_string = '127.0.0.1'
        host_port = 6379
    host = os.environ.get('DB_HOST', host_string)
    port = host_port if host == host_string else 5432
    password = os.environ.get('DB_PASSWORD', 'abc123')
    user, db_name = 'allocation', 'allocation'
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_postgres_engine():
    engine = create_engine(get_postgres_uri(), isolation_level="REPEATABLE READ", )
    metadata.create_all(engine)  # eh esse comando que gera a base de dados
    return engine


def get_sqlite_engine():
    print("diretorio sqlite: ", BASE_DIR)
    engine = create_engine('sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3'))
    metadata.create_all(engine)
    return engine


def get_api_url(local: bool = False):
    host_string = '192.168.99.100'
    host_port = 80
    if local:
        host_string = '127.0.0.1'
        host_port = 5000
    host = os.environ.get('API_HOST', host_string)
    port = host_port if host == host_string else 80
    return f"http://{host}:{port}"


def get_redis_host_and_port(local: bool = False):
    host_string = '192.168.99.100'
    host_port = 63791
    if local:
        host_string = '127.0.0.1'
        host_port = 6379
    host = os.environ.get('REDIS_HOST', host_string)
    port = host_port if host == host_string else 6379
    return dict(host=host, port=port)
