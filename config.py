import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'parking-app-secret-key-2024'
    DATABASE_PATH = 'parking_system.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False