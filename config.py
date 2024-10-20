import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Shashank'
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = '2005'
    DB_NAME = 'supermarket_db'
