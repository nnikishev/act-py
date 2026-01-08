#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""
import os
import sys
from pathlib import Path

# Добавляем текущую директорию в путь Python
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app import create_app
from db import db, Report

def init_database():
    """Инициализация базы данных"""
    print("Инициализация базы данных...")
    
    # Создаем Flask приложение
    app = create_app()
    
    with app.app_context():
        try:
            # Создаем все таблицы
            db.create_all()
            
            # Проверяем создание
            report_count = Report.query.count()
            
            print(f"✓ База данных успешно инициализирована")
            print(f"✓ Путь к БД: {app.config['SQLALCHEMY_DATABASE_URI']}")
            print(f"✓ Таблицы созданы")
            print(f"✓ Записей в таблице reports: {report_count}")
            
            # Создаем тестовый отчет если таблица пуста
            if report_count == 0:
                create_sample_report(app)
                
        except Exception as e:
            print(f"✗ Ошибка при инициализации БД: {e}")
            return False
    
    return True

def create_sample_report(app):
    """Создание тестового отчета"""
    with app.app_context():
        try:
            sample_report = Report(
                order_number="TEST-001",
                order_date="1 января 2024 г.",
                
                executor_name="ООО «Автосервис»",
                executor_address="г. Москва, ул. Примерная, д. 1",
                executor_phone="+7 (495) 123-45-67",
                
                customer_name="Иванов Иван Иванович",
                customer_address="г. Москва, ул. Тестовая, д. 10",
                customer_phone="+7 (999) 123-45-67",
                
                vehicle_make="Lada",
                vehicle_model="Vesta",
                vehicle_registration="А123ВС77",
                vehicle_vin="XTA1234567890",
                vehicle_year=2020,
                vehicle_mileage=45000,
                
                reason="Замена масла, диагностика подвески",
                warranty_info="Гарантия на работы 6 месяцев или 10000 км",
                
                works_data='[{"name": "Замена масла двигателя", "time": 1, "discount": 0, "rate": 1000, "total": 1000}, {"name": "Диагностика подвески", "time": 0.5, "discount": 0, "rate": 800, "total": 400}]',
                parts_data='[{"name": "Масло моторное 5W-40", "unit": "л", "quantity": 4, "price": 500, "total": 2000}, {"name": "Масляный фильтр", "unit": "шт", "quantity": 1, "price": 300, "total": 300}]',
                
                total_amount=3700.0,
                status='generated'
            )
            
            db.session.add(sample_report)
            db.session.commit()
            
            print("✓ Тестовый отчет создан")
            print(f"  Номер: TEST-001")
            print(f"  Сумма: 3700 руб.")
            
        except Exception as e:
            print(f"✗ Ошибка при создании тестового отчета: {e}")
            db.session.rollback()

def create_directories():
    """Создание необходимых директорий"""
    directories = [
        'instance',
        'reports',
        'uploads',
        'static/css',
        'static/js',
        'static/images',
        'templates'
    ]
    
    print("\nСоздание структуры проекта...")
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Создана директория: {directory}")
        else:
            print(f"✓ Директория уже существует: {directory}")
    
    # Создаем .gitkeep файлы
    for dir_with_gitkeep in ['reports', 'uploads']:
        gitkeep_file = Path(dir_with_gitkeep) / '.gitkeep'
        if not gitkeep_file.exists():
            gitkeep_file.touch()
            print(f"✓ Создан файл: {gitkeep_file}")

def check_templates():
    """Проверка наличия шаблонов"""
    required_templates = [
        'base.html',
        'index.html',
        'create_report.html',
        'view_report.html',
        'report_list.html',
        'preview.html',
        '404.html'
    ]
    
    print("\nПроверка шаблонов...")
    templates_dir = Path('templates')
    
    if not templates_dir.exists():
        print(f"✗ Директория templates не найдена!")
        return False
    
    missing_templates = []
    for template in required_templates:
        template_file = templates_dir / template
        if not template_file.exists():
            missing_templates.append(template)
    
    if missing_templates:
        print(f"✗ Отсутствуют шаблоны: {', '.join(missing_templates)}")
        print("  Создайте недостающие файлы или скачайте полную версию проекта")
        return False
    else:
        print(f"✓ Все необходимые шаблоны найдены")
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("ИНИЦИАЛИЗАЦИЯ ПРОЕКТА")
    print("=" * 60)
    
    # Создаем директории
    create_directories()
    
    # Проверяем шаблоны
    if not check_templates():
        print("\nСоздайте недостающие шаблоны или скачайте полную версию проекта")
        sys.exit(1)
    
    # Инициализируем БД
    print("\n" + "=" * 60)
    if init_database():
        print("\n" + "=" * 60)
        print("ПРОЕКТ УСПЕШНО ИНИЦИАЛИЗИРОВАН!")
        print("=" * 60)
        print("\nДля запуска приложения выполните:")
        print("  python app.py")
        print("\nИли:")
        print("  flask run")
        print("\nЗатем откройте в браузере:")
        print("  http://localhost:5000")
    else:
        print("\n✗ Ошибка при инициализации проекта")
        sys.exit(1)