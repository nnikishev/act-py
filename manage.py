#!/usr/bin/env python
"""Управление приложением и миграциями"""

import os
import sys
from flask_migrate import Migrate
from app import create_app, db
from flask_script import Manager, Shell

# Создаем приложение
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    """Контекст для shell"""
    return dict(app=app, db=db)

manager.add_command("shell", Shell(make_context=make_shell_context))

@manager.command
def init_db():
    """Инициализация базы данных"""
    with app.app_context():
        db.create_all()
        print("База данных инициализирована")

@manager.command
def drop_db():
    """Удаление базы данных"""
    with app.app_context():
        db.drop_all()
        print("База данных удалена")

@manager.command
def seed_db():
    """Заполнение базы тестовыми данными"""
    from db import Customer, Report
    from datetime import datetime
    import json
    
    with app.app_context():
        # Тестовые клиенты
        customers = [
            Customer(
                last_name="Иванов",
                first_name="Иван",
                middle_name="Иванович",
                phone="+7 (999) 123-45-67",
                email="ivanov@example.com",
                address="г. Москва, ул. Ленина, д. 1",
                driver_license="77АА123456",
                vehicles_data=json.dumps([
                    {
                        "vehicle_make": "Toyota",
                        "vehicle_model": "Camry",
                        "vehicle_registration": "А123АА777",
                        "vehicle_vin": "JTDBR32E160123456",
                        "vehicle_year": 2016,
                        "vehicle_mileage": 85000
                    }
                ])
            ),
            Customer(
                last_name="Петров",
                first_name="Петр",
                phone="+7 (999) 987-65-43",
                email="petrov@example.com",
                address="г. Москва, ул. Пушкина, д. 10",
                driver_license="77ВВ789012",
                vehicles_data=json.dumps([
                    {
                        "vehicle_make": "Hyundai",
                        "vehicle_model": "Solaris",
                        "vehicle_registration": "В456ВВ777",
                        "vehicle_vin": "Z94CB41BAHR123456",
                        "vehicle_year": 2017,
                        "vehicle_mileage": 65000
                    }
                ])
            )
        ]
        
        for customer in customers:
            db.session.add(customer)
        
        # Тестовые акты
        reports = [
            Report(
                order_number="1001",
                order_date="15.01.2024",
                executor_name="ООО 'Автосервис'",
                executor_address="г. Москва, ул. Сервисная, 15",
                executor_phone="+7 (495) 123-45-67",
                customer_name="Иванов Иван Иванович",
                customer_address="г. Москва, ул. Ленина, д. 1",
                customer_phone="+7 (999) 123-45-67",
                vehicle_make="Toyota",
                vehicle_model="Camry",
                vehicle_registration="А123АА777",
                vehicle_vin="JTDBR32E160123456",
                vehicle_year=2016,
                vehicle_mileage=85000,
                reason="Замена масла и фильтров",
                works_data=json.dumps([
                    {"name": "Замена масла двигателя", "time": 1.0, "discount": 0, "rate": 1500, "total": 1500},
                    {"name": "Замена масляного фильтра", "time": 0.5, "discount": 0, "rate": 1500, "total": 750}
                ]),
                parts_data=json.dumps([
                    {"name": "Масло моторное 5W-30", "unit": "л", "quantity": 5, "price": 600, "total": 3000},
                    {"name": "Фильтр масляный", "unit": "шт", "quantity": 1, "price": 1200, "total": 1200}
                ]),
                total_amount=6450,
                status="generated",
                created_at=datetime(2024, 1, 15, 10, 30, 0)
            )
        ]
        
        for report in reports:
            db.session.add(report)
        
        db.session.commit()
        print("Тестовые данные добавлены")

@manager.command
def reset_db():
    """Сброс базы данных и заполнение тестовыми данными"""
    drop_db()
    init_db()
    seed_db()

if __name__ == '__main__':
    manager.run()