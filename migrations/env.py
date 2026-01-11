from __future__ import with_statement
import logging
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Импортируем настройки и модели
from app import create_app
from db import db

config = context.config

# Создаем Flask приложение
app = create_app('default')

# Переопределяем sqlalchemy.url
config.set_main_option('sqlalchemy.url', app.config['SQLALCHEMY_DATABASE_URI'])

def get_metadata():
    """Возвращаем метаданные SQLAlchemy"""
    return db.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()