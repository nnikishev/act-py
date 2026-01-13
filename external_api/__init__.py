"""
Модуль для интеграции внешних API
"""
import os
from typing import Optional

class RosskoConfig:
    """Конфигурация для API Rossko"""
    
    @staticmethod
    def get_credentials():
        """Получение учетных данных из переменных окружения"""
        key1 = os.environ.get('ROSSKO_KEY1', '')
        key2 = os.environ.get('ROSSKO_KEY2', '')
        delivery_id = os.environ.get('ROSSKO_DELIVERY_ID', '')
        address_id = os.environ.get('ROSSKO_ADDRESS_ID')
        
        if not all([key1, key2, delivery_id]):
            raise ValueError(
                "Не заданы обязательные переменные окружения: "
                "ROSSKO_KEY1, ROSSKO_KEY2, ROSSKO_DELIVERY_ID"
            )
        
        return {
            'key1': key1,
            'key2': key2,
            'delivery_id': delivery_id,
            'address_id': address_id
        }
    
    @staticmethod
    def create_client():
        """Создание клиента Rossko"""
        from external_api.rossko import RosskoSoapSearchClient
        
        credentials = RosskoConfig.get_credentials()
        return RosskoSoapSearchClient(**credentials)