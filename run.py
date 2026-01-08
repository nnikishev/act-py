#!/usr/bin/env python3
"""
Точка входа для запуска Flask приложения
"""
import os
from app import app

if __name__ == '__main__':
    # Создаем необходимые директории
    for folder in ['instance', 'reports', 'uploads', 'static/css', 'static/js', 'static/images']:
        os.makedirs(folder, exist_ok=True)
    
    # Запускаем приложение
    app.run(
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('DEBUG', 'True').lower() == 'true'
    )