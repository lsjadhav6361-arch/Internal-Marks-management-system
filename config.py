import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'imms_secret_key_123')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'imms_mysql')
    MYSQL_AUTOCOMMIT = False

    SESSION_PERMANENT = False
    SESSION_COOKIE_NAME = 'imms_session'
