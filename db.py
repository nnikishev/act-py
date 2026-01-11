from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.sqlite import JSON
import json

db = SQLAlchemy()

class Report(db.Model):
    """Модель отчета"""
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Основная информация
    order_number = db.Column(db.String(50), nullable=True, index=True)
    order_date = db.Column(db.String(50), nullable=False)
    
    # Исполнитель
    executor_name = db.Column(db.String(200), nullable=False)
    executor_address = db.Column(db.String(300))
    executor_phone = db.Column(db.String(50))
    
    # Заказчик
    customer_name = db.Column(db.String(200), nullable=False)
    customer_address = db.Column(db.String(300))
    customer_phone = db.Column(db.String(50))
    
    # Транспортное средство
    vehicle_make = db.Column(db.String(50))
    vehicle_model = db.Column(db.String(50))
    vehicle_registration = db.Column(db.String(50))
    vehicle_vin = db.Column(db.String(100))
    vehicle_year = db.Column(db.Integer)
    vehicle_mileage = db.Column(db.Integer)
    
    # Причина обращения
    reason = db.Column(db.Text)
    
    # Работы (храним как JSON)
    works_data = db.Column(db.Text)
    
    # Запчасти (храним как JSON)
    parts_data = db.Column(db.Text)
    
    # Стоимость
    total_amount = db.Column(db.Float, default=0.0)
    
    # Гарантия
    warranty_info = db.Column(db.Text)
    
    # Статус и метаданные
    status = db.Column(db.String(20), default='draft', index=True)  # draft, generated, archived
    pdf_path = db.Column(db.String(500))
    html_content = db.Column(db.Text)
    
    # Даты
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    generated_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Report {self.order_number}>'
    
    def to_dict(self):
        """Конвертация в словарь"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'order_date': self.order_date,
            'executor_name': self.executor_name,
            'customer_name': self.customer_name,
            'vehicle_make': self.vehicle_make,
            'vehicle_model': self.vehicle_model,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'pdf_path': self.pdf_path
        }
    
    def get_works(self):
        """Получение работ из JSON"""
        if self.works_data:
            return json.loads(self.works_data)
        return []
    
    def get_parts(self):
        """Получение запчастей из JSON"""
        if self.parts_data:
            return json.loads(self.parts_data)
        return []
    
    def get_vehicle_data(self):
        """Получение данных о транспорте"""
        return {
            'make': self.vehicle_make,
            'model': self.vehicle_model,
            'registration': self.vehicle_registration,
            'vin': self.vehicle_vin,
            'year': self.vehicle_year,
            'mileage': self.vehicle_mileage
        }
 
    
class Customer(db.Model):
    """Модель клиента"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Основная информация
    last_name = db.Column(db.String(100), nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    
    # Контактная информация
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(200))
    address = db.Column(db.String(300))
    
    # Дополнительная информация
    driver_license = db.Column(db.String(50), index=True)
    
    # Автомобили (храним как JSON)
    vehicles_data = db.Column(db.Text, default='[]')
    
    # Статус и метаданные
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='active', index=True)  # active, inactive
    
    # Даты
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Customer {self.last_name} {self.first_name}>'
    
    def get_full_name(self):
        """Полное имя клиента"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)
    
    def get_short_name(self):
        """Короткое имя"""
        return f"{self.last_name} {self.first_name[0]}." + (f" {self.middle_name[0]}." if self.middle_name else "")
    
    def get_vehicles(self):
        """Получение списка автомобилей из JSON"""
        if self.vehicles_data:
            return json.loads(self.vehicles_data)
        return []
    
    def add_vehicle(self, vehicle_data):
        """Добавление автомобиля"""
        vehicles = self.get_vehicles()
        vehicles.append(vehicle_data)
        self.vehicles_data = json.dumps(vehicles, ensure_ascii=False)
    
    def to_dict(self):
        """Конвертация в словарь"""
        return {
            'id': self.id,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'full_name': self.get_full_name(),
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'driver_license': self.driver_license,
            'vehicles': self.get_vehicles(),
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }