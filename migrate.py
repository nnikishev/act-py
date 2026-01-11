#!/usr/bin/env python
"""Скрипт для управления миграциями"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
project_path = Path(__file__).parent
sys.path.append(str(project_path))

from app import create_app
from flask_migrate import Migrate, upgrade, downgrade, revision, migrate

def run_migration():
    """Запуск миграций"""
    app = create_app('default')
    
    with app.app_context():
        print("Запуск миграций...")
        upgrade()
        print("Миграции успешно применены")

def create_migration(message):
    """Создание новой миграции"""
    app = create_app('default')
    
    with app.app_context():
        print(f"Создание миграции: {message}")
        revision(message, autogenerate=True)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'upgrade':
            run_migration()
        elif command == 'revision' and len(sys.argv) > 2:
            message = sys.argv[2]
            create_migration(message)
        elif command == 'downgrade':
            app = create_app('default')
            with app.app_context():
                downgrade()
                print("Откат миграции выполнен")
        elif command == 'history':
            os.system('alembic history')
        elif command == 'current':
            os.system('alembic current')
        else:
            print("Доступные команды:")
            print("  python migrate.py upgrade    - применить все миграции")
            print("  python migrate.py revision <message> - создать новую миграцию")
            print("  python migrate.py downgrade  - откатить последнюю миграцию")
            print("  python migrate.py history    - показать историю миграций")
            print("  python migrate.py current    - показать текущую миграцию")
    else:
        print("Использование: python migrate.py <команда>")