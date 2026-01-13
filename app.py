import os
import sys
from datetime import datetime
from flask import Flask

from api.routes import register_routes, register_error_handlers
from config import config
from db import db, Report
from report_generator import report_generator
from flask_migrate import Migrate

def create_app(config_name='default'):
    """Фабрика приложения"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Инициализация расширений
    db.init_app(app)
    report_generator.init_app(app)
    migrate = Migrate(app, db)
    
    # Создаем директории
    with app.app_context():
        # Создаем все необходимые директории
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
        os.makedirs('instance', exist_ok=True)
        
        # Создаем таблицы в БД
        db.create_all()
        print(f"✓ База данных инициализирована: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"✓ Директория отчетов: {app.config['REPORTS_FOLDER']}")
    
    # Регистрация маршрутов
    register_routes(app)
    register_error_handlers(app)
    register_template_filters(app)
    
    return app

def register_template_filters(app):
    """Регистрация фильтров для шаблонов"""
    @app.template_filter('format_currency')
    def format_currency(value):
        """Форматирование валюты"""
        try:
            return f"{float(value):.2f}"
        except:
            return str(value)
    
    @app.template_filter('format_date')
    def format_date(value):
        """Форматирование даты"""
        if value:
            if isinstance(value, str):
                return value
            return value.strftime('%d.%m.%Y')
        return ''
    
    @app.template_filter('format_datetime')
    def format_datetime(value):
        """Форматирование даты и времени"""
        if value:
            if isinstance(value, str):
                return value
            return value.strftime('%d.%m.%Y %H:%M')
        return ''
    
    @app.context_processor
    def inject_now():
        """Добавление текущей даты в контекст шаблонов"""
        return {'now': datetime.now()}
    
    @app.context_processor
    def inject_stats():
        """Добавление статистики в контекст"""
        with app.app_context():
            try:
                total_reports = Report.query.count()
                generated_reports = Report.query.filter_by(status='generated').count()
                draft_reports = Report.query.filter_by(status='draft').count()
                
                return {
                    'total_reports': total_reports,
                    'generated_reports': generated_reports,
                    'draft_reports': draft_reports,
                    'recent_reports': Report.query.order_by(Report.created_at.desc()).limit(5).all()
                }
            except:
                return {
                    'total_reports': 0,
                    'generated_reports': 0,
                    'draft_reports': 0,
                    'recent_reports': []
                }
            
            
# Создаем приложение
app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("Запуск генератора актов выполненных работ")
    print("=" * 60)
    
    # Проверяем наличие необходимых директорий
    for folder in ['templates', 'static/css', 'static/js', 'static/images', 'reports', 'uploads']:
        os.makedirs(folder, exist_ok=True)
        print(f"✓ Директория: {folder}")
    
    # Запускаем приложение
    app.run(
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('DEBUG', 'True').lower() == 'true'
    )