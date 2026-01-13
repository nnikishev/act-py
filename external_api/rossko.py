import zeep
from zeep import Client
from zeep.transports import Transport
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StockInfo:
    """Информация о наличии товара на конкретном складе."""
    stock_id: str
    price: float
    count: int
    multiplicity: int
    delivery_days: int
    warehouse_description: str
    delivery_start: Optional[str] = None
    delivery_end: Optional[str] = None

@dataclass
class PartInfo:
    """Основная информация о найденной запчасти."""
    guid: str
    brand: str
    part_number: str
    name: str
    stocks: List[StockInfo] = field(default_factory=list)

@dataclass
class SearchResult:
    """Полный результат поискового запроса."""
    success: bool
    search_text: str
    message: Optional[str] = None
    parts: List[PartInfo] = field(default_factory=list)

class RosskoSoapSearchClient:
    """
    Клиент для поиска запчастей через SOAP API Росско (GetSearch).
    """
    
    # WSDL URL для сервиса GetSearch (из документации)
    WSDL_URL = "http://api.rossko.ru/service/v2.1/GetSearch"
    
    def __init__(self, key1: str, key2: str, delivery_id: str, address_id: Optional[str] = None):
        """
        Инициализация клиента.
        
        :param key1: Первый ключ авторизации из личного кабинета
        :param key2: Второй ключ авторизации из личного кабинета
        :param delivery_id: Идентификатор типа доставки (получается из GetCheckoutDetails)
        :param address_id: Идентификатор адреса доставки (обязателен, если не самовывоз)
        """
        self.key1 = key1
        self.key2 = key2
        self.delivery_id = delivery_id
        self.address_id = address_id
        
        # Создаем SOAP клиент
        transport = Transport(timeout=10)
        self.client = Client(self.WSDL_URL, transport=transport)
        
        logger.info("SOAP клиент для Rossko API инициализирован")
    
    def search_parts(self, search_text: str) -> SearchResult:
        """
        Выполняет поиск запчастей по артикулу, бренду или названию.
        
        :param search_text: Поисковый запрос (артикул, артикул+бренд, название)
        :return: Объект SearchResult с результатами поиска
        """
        logger.info(f"Выполняю поиск по запросу: '{search_text}'")
        
        # Подготавливаем параметры для SOAP запроса
        params = {
            'KEY1': self.key1,
            'KEY2': self.key2,
            'text': search_text,
            'delivery_id': self.delivery_id,
        }
        
        # Добавляем address_id, если он указан
        if self.address_id:
            params['address_id'] = self.address_id
        
        try:
            # Выполняем SOAP вызов
            soap_response = self.client.service.GetSearch(**params)
            
            # Преобразуем SOAP ответ в наш объект SearchResult
            return self._parse_soap_response(soap_response, search_text)
            
        except zeep.exceptions.Fault as fault:
            logger.error(f"SOAP ошибка: {fault.message}")
            return SearchResult(
                success=False,
                search_text=search_text,
                message=f"SOAP Fault: {fault.message}"
            )
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            return SearchResult(
                success=False,
                search_text=search_text,
                message=f"Ошибка соединения: {str(e)}"
            )
    
    def _parse_soap_response(self, soap_response: Any, search_text: str) -> SearchResult:
        """
        Парсит SOAP ответ в структурированный объект SearchResult.
        """
        # Извлекаем основной результат из SOAP ответа
        # Структура ответа: GetSearchResponse -> SearchResult
        search_result = soap_response.SearchResult
        
        # Базовый результат
        result = SearchResult(
            success=search_result.Success,
            search_text=search_text
        )
        
        # Если есть сообщение об ошибке
        if hasattr(search_result, 'message') and search_result.message:
            result.message = search_result.message
        
        # Если поиск неудачный, возвращаем пустой результат
        if not result.success:
            return result
        
        # Парсим найденные запчасти
        if hasattr(search_result, 'PartsList') and search_result.PartsList:
            for soap_part in search_result.PartsList.Part:
                part_info = self._parse_soap_part(soap_part)
                result.parts.append(part_info)
        
        logger.info(f"Найдено {len(result.parts)} запчастей")
        return result
    
    def _parse_soap_part(self, soap_part: Any) -> PartInfo:
        """
        Парсит информацию об одной запчасти из SOAP структуры.
        """
        # Основная информация о запчасти
        part_info = PartInfo(
            guid=soap_part.guid,
            brand=soap_part.brand,
            part_number=soap_part.partnumber,
            name=soap_part.name
        )
        
        # Парсим информацию о наличии на складах
        if hasattr(soap_part, 'stocks') and soap_part.stocks:
            for soap_stock in soap_part.stocks.stock:
                stock_info = StockInfo(
                    stock_id=soap_stock.id,
                    price=float(soap_stock.price),
                    count=int(soap_stock.count),
                    multiplicity=int(soap_stock.multiplicity),
                    delivery_days=int(soap_stock.delivery),
                    warehouse_description=soap_stock.description,
                    delivery_start=getattr(soap_stock, 'deliveryStart', None),
                    delivery_end=getattr(soap_stock, 'deliveryEnd', None)
                )
                part_info.stocks.append(stock_info)
        
        return part_info

def format_search_results(result: SearchResult) -> str:
    """
    Форматирует результаты поиска для удобного отображения.
    
    :param result: Результат поиска
    :return: Отформатированная строка с результатами
    """
    if not result.success:
        return f"❌ Поиск не удался. Причина: {result.message or 'Неизвестная ошибка'}"
    
    if not result.parts:
        return f"🔍 По запросу '{result.search_text}' ничего не найдено."
    
    output_lines = [f"✅ Найдено запчастей: {len(result.parts)}\n"]
    
    for i, part in enumerate(result.parts, 1):
        output_lines.append(f"\n{i}. {part.brand} {part.part_number} - {part.name}")
        output_lines.append(f"   GUID: {part.guid}")
        
        if part.stocks:
            # Сортируем склады по цене или наличию
            available_stocks = [s for s in part.stocks if s.count > 0]
            if available_stocks:
                best_stock = min(available_stocks, key=lambda x: x.price)
                output_lines.append(f"   🏪 В наличии: {best_stock.count} шт.")
                output_lines.append(f"   💰 Цена: {best_stock.price:.2f} руб.")
                output_lines.append(f"   📦 Доставка: {best_stock.delivery_days} дн.")
                output_lines.append(f"   📍 Склад: {best_stock.warehouse_description}")
            else:
                output_lines.append("   📭 Нет в наличии")
        
        # Показываем общее количество складов
        if len(part.stocks) > 1:
            output_lines.append(f"   📊 Всего предложений: {len(part.stocks)}")
    
    return "\n".join(output_lines)

# Пример использования клиента
# def main():
#     """
#     Пример использования SOAP клиента для поиска запчастей.
#     ЗАМЕНИТЕ значения ключей и идентификаторов на свои!
#     """
#     # Ваши данные авторизации (получить в личном кабинете Rossko)
#     KEY1 = "cba94510b02ecccef994b52711c84413"  # Замените на свой KEY1
#     KEY2 = "8c7b4ba7acc716fe5bd7a80c513ad930"  # Замените на свой KEY2
    
#     # Идентификаторы доставки (получить через GetCheckoutDetails)
#     DELIVERY_ID = "000000002"  # Пример из документации
#     ADDRESS_ID = "112233"      # Пример из документации, можно None для самовывоза
    
#     # Создаем клиент
#     client = RosskoSoapSearchClient(
#         key1=KEY1,
#         key2=KEY2,
#         delivery_id=DELIVERY_ID,
#         address_id=ADDRESS_ID
#     )
    
#     # Примеры поисковых запросов
#     search_queries = [
#         "333114",               # Поиск по артикулу
#         "KYB 333114",           # Поиск по бренду и артикулу
#         "амортизационная стойка", # Поиск по названию
#     ]
    
#     # Выполняем поиск для каждого запроса
#     for query in search_queries:
#         print(f"\n{'='*50}")
#         print(f"Поиск: {query}")
#         print('='*50)
        
#         result = client.search_parts(query)
#         formatted_result = format_search_results(result)
#         print(formatted_result)