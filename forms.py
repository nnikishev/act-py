from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, FieldList, FormField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms.fields import DateField

class WorkForm(FlaskForm):
    """Форма для одной работы"""
    name = StringField('Наименование работы', validators=[DataRequired()])
    time = FloatField('Норма времени (час)', validators=[DataRequired(), NumberRange(min=0)])
    discount = FloatField('Скидка (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0)
    rate = FloatField('Стоимость нормо-часа (руб.)', validators=[DataRequired(), NumberRange(min=0)])
    total = FloatField('Стоимость работ (руб.)', validators=[DataRequired(), NumberRange(min=0)])

class PartForm(FlaskForm):
    """Форма для одной запчасти"""
    name = StringField('Наименование материала', validators=[DataRequired()])
    unit = StringField('Ед. изм.', validators=[DataRequired()], default='шт.')
    quantity = IntegerField('Количество', validators=[DataRequired(), NumberRange(min=1)])
    price = FloatField('Цена (руб.)', validators=[DataRequired(), NumberRange(min=0)])
    total = FloatField('Сумма (руб.)', validators=[DataRequired(), NumberRange(min=0)])

class ReportForm(FlaskForm):
    """Основная форма отчета"""
    
    # Основная информация
    order_number = StringField('Номер заказ-наряда', validators=[DataRequired(), Length(max=50)])
    order_date = StringField('Дата заказ-наряда', validators=[DataRequired()])
    
    # Исполнитель
    executor_name = StringField('Наименование исполнителя', validators=[DataRequired(), Length(max=200)])
    executor_address = TextAreaField('Адрес исполнителя', validators=[DataRequired(), Length(max=300)])
    executor_phone = StringField('Телефон исполнителя', validators=[DataRequired(), Length(max=50)])
    
    # Заказчик
    customer_name = StringField('ФИО заказчика', validators=[DataRequired(), Length(max=200)])
    customer_address = TextAreaField('Адрес заказчика', validators=[DataRequired(), Length(max=300)])
    customer_phone = StringField('Телефон заказчика', validators=[DataRequired(), Length(max=50)])
    
    # Транспортное средство
    vehicle_make = StringField('Марка ТС', validators=[DataRequired(), Length(max=50)])
    vehicle_model = StringField('Модель ТС', validators=[DataRequired(), Length(max=50)])
    vehicle_registration = StringField('Регистрационный знак', validators=[Optional(), Length(max=50)])
    vehicle_vin = StringField('VIN/Заводской номер', validators=[Optional(), Length(max=100)])
    vehicle_year = IntegerField('Год выпуска', validators=[Optional(), NumberRange(min=1900, max=2100)])
    vehicle_mileage = IntegerField('Пробег (км)', validators=[Optional(), NumberRange(min=0)])
    
    # Причина обращения
    reason = TextAreaField('Причина обращения', validators=[DataRequired()])
    
    # Работы и запчасти
    works = FieldList(FormField(WorkForm), min_entries=1, label='Выполненные работы')
    parts = FieldList(FormField(PartForm), min_entries=1, label='Запасные части')
    
    # Гарантия
    warranty_info = TextAreaField('Гарантийные обязательства', 
                                 default="Гарантия на работу предоставляется сроком на 6 (шесть) месяцев или 10000 км пробега автомобиля. Гарантия на запчасти предоставляется согласно гарантии производителя.")
    
    # Кнопки
    submit = SubmitField('Сохранить черновик')
    generate_pdf = SubmitField('Сгенерировать PDF')
    preview = SubmitField('Предпросмотр')