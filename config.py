import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Базовая конфигурация"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # База данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'reports.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки загрузки файлов
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    REPORTS_FOLDER = os.path.join(basedir, 'reports')
    
    # Настройки сессии
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Настройки приложения
    APP_NAME = "Генератор актов выполненных работ"
    APP_VERSION = "1.0.0"
    
    @staticmethod
    def init_app(app):
        """Инициализация приложения"""
        # Создаем необходимые директории
        for folder in [app.config['UPLOAD_FOLDER'], 
                      app.config['REPORTS_FOLDER'],
                      'instance']:
            os.makedirs(folder, exist_ok=True)

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}