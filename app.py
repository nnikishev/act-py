import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import json
from pathlib import Path

from config import config
from db import db, Report
from forms import ReportForm, WorkForm, PartForm
from report_generator import report_generator

def create_app(config_name='default'):
    """Фабрика приложения"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Инициализация расширений
    db.init_app(app)
    report_generator.init_app(app)
    
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

def register_routes(app):
    """Регистрация маршрутов"""
    
    @app.route('/')
    def index():
        """Главная страница"""
        total_reports = Report.query.count()
        generated_reports = Report.query.filter_by(status='generated').count()
        draft_reports = Report.query.filter_by(status='draft').count()
        
        return render_template(
            'index.html',
            total_reports=total_reports,
            generated_reports=generated_reports,
            draft_reports=draft_reports
            )
    
    @app.route('/reports')
    def report_list():
        """Список отчетов"""
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Фильтрация
        status = request.args.get('status', 'all')
        query = Report.query
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        # Поиск
        search = request.args.get('search', '')
        if search:
            query = query.filter(
                (Report.order_number.contains(search)) |
                (Report.customer_name.contains(search)) |
                (Report.vehicle_make.contains(search)) |
                (Report.vehicle_model.contains(search))
            )
        
        reports = query.order_by(Report.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('report_list.html', reports=reports, 
                             status=status, search=search)
    
    @app.route('/reports/new', methods=['GET', 'POST'])
    def create_report():
        """Создание нового отчета"""
        if request.method == 'POST':
            try:
                # Получаем данные из формы
                order_date = request.form.get('order_date', '').strip()
                
                executor_name = request.form.get('executor_name', '').strip()
                executor_address = request.form.get('executor_address', '').strip()
                executor_phone = request.form.get('executor_phone', '').strip()
                
                customer_name = request.form.get('customer_name', '').strip()
                customer_address = request.form.get('customer_address', '').strip()
                customer_phone = request.form.get('customer_phone', '').strip()
                
                vehicle_make = request.form.get('vehicle_make', '').strip()
                vehicle_model = request.form.get('vehicle_model', '').strip()
                vehicle_registration = request.form.get('vehicle_registration', '').strip()
                vehicle_vin = request.form.get('vehicle_vin', '').strip()
                
                vehicle_year = request.form.get('vehicle_year', '')
                vehicle_year = int(vehicle_year) if vehicle_year and vehicle_year.isdigit() else None
                
                vehicle_mileage = request.form.get('vehicle_mileage', '')
                vehicle_mileage = int(vehicle_mileage) if vehicle_mileage and vehicle_mileage.isdigit() else None
                
                reason = request.form.get('reason', '').strip()
                warranty_info = request.form.get('warranty_info', '').strip()
                
                if not executor_name or not customer_name:
                    flash('Заполните обязательные поля: исполнитель, заказчик', 'danger')
                    return redirect(url_for('create_report'))
                
                # Обрабатываем работы
                works = []
                work_index = 0
                while True:
                    name_key = f'works-{work_index}-name'
                    if name_key not in request.form:
                        break
                    
                    name = request.form.get(name_key, '').strip()
                    if name:  # Только если есть название работы
                        time_str = request.form.get(f'works-{work_index}-time', '0')
                        discount_str = request.form.get(f'works-{work_index}-discount', '0')
                        rate_str = request.form.get(f'works-{work_index}-rate', '0')
                        total_str = request.form.get(f'works-{work_index}-total', '0')
                        
                        try:
                            time_val = float(time_str) if time_str else 0
                            discount_val = float(discount_str) if discount_str else 0
                            rate_val = float(rate_str) if rate_str else 0
                            total_val = float(total_str) if total_str else 0
                        except ValueError:
                            time_val = discount_val = rate_val = total_val = 0
                        
                        works.append({
                            'name': name,
                            'time': time_val,
                            'discount': discount_val,
                            'rate': rate_val,
                            'total': total_val
                        })
                    
                    work_index += 1
                
                # Обрабатываем запчасти
                parts = []
                part_index = 0
                while True:
                    name_key = f'parts-{part_index}-name'
                    if name_key not in request.form:
                        break
                    
                    name = request.form.get(name_key, '').strip()
                    if name:  # Только если есть название запчасти
                        unit = request.form.get(f'parts-{part_index}-unit', 'шт.').strip()
                        quantity_str = request.form.get(f'parts-{part_index}-quantity', '0')
                        price_str = request.form.get(f'parts-{part_index}-price', '0')
                        total_str = request.form.get(f'parts-{part_index}-total', '0')
                        
                        try:
                            quantity_val = int(quantity_str) if quantity_str and quantity_str.isdigit() else 0
                            price_val = float(price_str) if price_str else 0
                            total_val = float(total_str) if total_str else 0
                        except ValueError:
                            quantity_val = price_val = total_val = 0
                        
                        parts.append({
                            'name': name,
                            'unit': unit,
                            'quantity': quantity_val,
                            'price': price_val,
                            'total': total_val
                        })
                    
                    part_index += 1
                
                # Рассчитываем итоговую сумму
                works_total = sum(w.get('total', 0) for w in works)
                parts_total = sum(p.get('total', 0) for p in parts)
                total_amount = works_total + parts_total
                
                # Создаем новый отчет
                report = Report(
                    order_date=order_date,
                    
                    executor_name=executor_name,
                    executor_address=executor_address,
                    executor_phone=executor_phone,
                    
                    customer_name=customer_name,
                    customer_address=customer_address,
                    customer_phone=customer_phone,
                    
                    vehicle_make=vehicle_make,
                    vehicle_model=vehicle_model,
                    vehicle_registration=vehicle_registration,
                    vehicle_vin=vehicle_vin,
                    vehicle_year=vehicle_year,
                    vehicle_mileage=vehicle_mileage,
                    
                    reason=reason,
                    warranty_info=warranty_info,
                    
                    works_data=json.dumps(works, ensure_ascii=False),
                    parts_data=json.dumps(parts, ensure_ascii=False),
                    total_amount=total_amount,
                )
                
                # Определяем действие
                if 'generate_pdf' in request.form:
                    report.status = 'generated'
                    
                    # Сохраняем в БД
                    db.session.add(report)
                    db.session.commit()
                    report.order_number = report.id
                    db.session.commit()
                    
                    # Генерируем PDF
                    success, result = report_generator.generate_pdf(report)
                    if success:
                        db.session.commit()
                        flash('Отчет успешно сгенерирован и сохранен!', 'success')
                        return redirect(url_for('view_report', report_id=report.id))
                    else:
                        flash(f'Ошибка при генерации PDF: {result}', 'danger')
                        return redirect(url_for('edit_report', report_id=report.id))
                
                elif 'preview' in request.form:
                    report.status = 'draft'
                    db.session.add(report)
                    db.session.commit()
                    report.order_number = report.id
                    db.session.commit()
                    # Показываем HTML предпросмотр
                    html_content = report_generator.render_report_html(report)
                    return render_template('preview.html', html_content=html_content, report=report)
                
                else:  # Сохранить черновик
                    report.status = 'draft'
                    db.session.add(report)
                    
                    db.session.commit()
                    report.order_number = report.id
                    db.session.commit()
                    flash('Черновик отчета сохранен!', 'success')
                    return redirect(url_for('edit_report', report_id=report.id))
                    
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Ошибка при создании отчета: {e}", exc_info=True)
                flash(f'Ошибка при сохранении отчета: {str(e)}', 'danger')
                return redirect(url_for('create_report'))
        
        # GET запрос - показываем пустую форму
        form = ReportForm()
        if len(form.works) == 0:
            form.works.append_entry()
        if len(form.parts) == 0:
            form.parts.append_entry()
        
        return render_template('create_report.html', form=form, title="Создание отчета")
    
    @app.route('/reports/<int:report_id>')
    def view_report(report_id):
        """Просмотр отчета"""
        report = Report.query.get_or_404(report_id)
        works = json.loads(report.works_data) if report.works_data else []
        parts = json.loads(report.parts_data) if report.parts_data else []
        return render_template('view_report.html', report=report, works=works, parts=parts)
    
    @app.route('/reports/<int:report_id>/edit', methods=['GET', 'POST'])
    def edit_report(report_id):
        """Редактирование отчета"""
        report = Report.query.get_or_404(report_id)
        
        if request.method == 'POST':
            try:
                # Получаем данные из формы
                report.order_number = report.id
                report.order_date = request.form.get('order_date', '').strip()
                
                report.executor_name = request.form.get('executor_name', '').strip()
                report.executor_address = request.form.get('executor_address', '').strip()
                report.executor_phone = request.form.get('executor_phone', '').strip()
                
                report.customer_name = request.form.get('customer_name', '').strip()
                report.customer_address = request.form.get('customer_address', '').strip()
                report.customer_phone = request.form.get('customer_phone', '').strip()
                
                report.vehicle_make = request.form.get('vehicle_make', '').strip()
                report.vehicle_model = request.form.get('vehicle_model', '').strip()
                report.vehicle_registration = request.form.get('vehicle_registration', '').strip()
                report.vehicle_vin = request.form.get('vehicle_vin', '').strip()
                
                vehicle_year = request.form.get('vehicle_year', '')
                report.vehicle_year = int(vehicle_year) if vehicle_year and vehicle_year.isdigit() else None
                
                vehicle_mileage = request.form.get('vehicle_mileage', '')
                report.vehicle_mileage = int(vehicle_mileage) if vehicle_mileage and vehicle_mileage.isdigit() else None
                
                report.reason = request.form.get('reason', '').strip()
                report.warranty_info = request.form.get('warranty_info', '').strip()
                
                # Обрабатываем работы
                works = []
                work_index = 0
                while True:
                    name_key = f'works-{work_index}-name'
                    if name_key not in request.form:
                        break
                    
                    name = request.form.get(name_key, '').strip()
                    if name:
                        time_str = request.form.get(f'works-{work_index}-time', '0')
                        discount_str = request.form.get(f'works-{work_index}-discount', '0')
                        rate_str = request.form.get(f'works-{work_index}-rate', '0')
                        total_str = request.form.get(f'works-{work_index}-total', '0')
                        
                        try:
                            time_val = float(time_str) if time_str else 0
                            discount_val = float(discount_str) if discount_str else 0
                            rate_val = float(rate_str) if rate_str else 0
                            total_val = float(total_str) if total_str else 0
                        except ValueError:
                            time_val = discount_val = rate_val = total_val = 0
                        
                        works.append({
                            'name': name,
                            'time': time_val,
                            'discount': discount_val,
                            'rate': rate_val,
                            'total': total_val
                        })
                    
                    work_index += 1
                
                # Обрабатываем запчасти
                parts = []
                part_index = 0
                while True:
                    name_key = f'parts-{part_index}-name'
                    if name_key not in request.form:
                        break
                    
                    name = request.form.get(name_key, '').strip()
                    if name:
                        unit = request.form.get(f'parts-{part_index}-unit', 'шт.').strip()
                        quantity_str = request.form.get(f'parts-{part_index}-quantity', '0')
                        price_str = request.form.get(f'parts-{part_index}-price', '0')
                        total_str = request.form.get(f'parts-{part_index}-total', '0')
                        
                        try:
                            quantity_val = int(quantity_str) if quantity_str and quantity_str.isdigit() else 0
                            price_val = float(price_str) if price_str else 0
                            total_val = float(total_str) if total_str else 0
                        except ValueError:
                            quantity_val = price_val = total_val = 0
                        
                        parts.append({
                            'name': name,
                            'unit': unit,
                            'quantity': quantity_val,
                            'price': price_val,
                            'total': total_val
                        })
                    
                    part_index += 1
                
                # Пересчитываем сумму
                works_total = sum(w.get('total', 0) for w in works)
                parts_total = sum(p.get('total', 0) for p in parts)
                report.total_amount = works_total + parts_total
                report.works_data = json.dumps(works, ensure_ascii=False)
                report.parts_data = json.dumps(parts, ensure_ascii=False)
                
                # Определяем действие
                if 'generate_pdf' in request.form:
                    report.status = 'generated'
                    db.session.commit()
                    
                    # Генерируем PDF
                    success, result = report_generator.generate_pdf(report)
                    if success:
                        db.session.commit()
                        flash('Отчет успешно обновлен и PDF сгенерирован!', 'success')
                    else:
                        flash(f'Ошибка при генерации PDF: {result}', 'danger')
                    
                    return redirect(url_for('view_report', report_id=report.id))
                
                elif 'preview' in request.form:
                    db.session.commit()
                    # Показываем HTML предпросмотр
                    html_content = report_generator.render_report_html(report)
                    return render_template('preview.html', html_content=html_content, report=report)
                
                else:
                    report.status = 'draft'
                    db.session.commit()
                    flash('Черновик отчета обновлен!', 'success')
                    return redirect(url_for('edit_report', report_id=report.id))
                    
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Ошибка при редактировании отчета: {e}", exc_info=True)
                flash(f'Ошибка при обновлении отчета: {str(e)}', 'danger')
                return redirect(url_for('edit_report', report_id=report_id))
        
        # GET запрос - заполняем форму данными отчета
        form = ReportForm(obj=report)
        
        # Заполняем работы
        works = report.get_works()
        while len(form.works) > 0:
            form.works.pop_entry()
        for work in works:
            work_form = WorkForm()
            work_form.name.data = work.get('name', '')
            work_form.time.data = work.get('time', 0)
            work_form.discount.data = work.get('discount', 0)
            work_form.rate.data = work.get('rate', 0)
            work_form.total.data = work.get('total', 0)
            form.works.append_entry(work_form)
        
        # Заполняем запчасти
        parts = report.get_parts()
        while len(form.parts) > 0:
            form.parts.pop_entry()
        for part in parts:
            part_form = PartForm()
            part_form.name.data = part.get('name', '')
            part_form.unit.data = part.get('unit', 'шт.')
            part_form.quantity.data = part.get('quantity', 0)
            part_form.price.data = part.get('price', 0)
            part_form.total.data = part.get('total', 0)
            form.parts.append_entry(part_form)
        
        # Добавляем пустые строки если нет работ/запчастей
        if len(form.works) == 0:
            form.works.append_entry()
        if len(form.parts) == 0:
            form.parts.append_entry()
        
        return render_template('create_report.html', form=form, report=report, title="Редактирование отчета")
    
    @app.route('/reports/<int:report_id>/preview')
    def preview_report(report_id):
        """Предпросмотр отчета в HTML (GET запрос)"""
        report = Report.query.get_or_404(report_id)
        html_content = report_generator.render_report_html(report)
        return render_template('preview.html', html_content=html_content, report=report)
    
    @app.route('/reports/<int:report_id>/pdf')
    def download_pdf(report_id):
        """Скачивание PDF"""
        report = Report.query.get_or_404(report_id)
        
        if not report.pdf_path or not os.path.exists(report.pdf_path):
            # Генерируем PDF если его нет
            success, result = report_generator.generate_pdf(report)
            if not success:
                flash('Не удалось сгенерировать PDF', 'danger')
                return redirect(url_for('view_report', report_id=report_id))
            db.session.commit()
        
        return send_file(
            report.pdf_path,
            as_attachment=True,
            download_name=f'act_{report.order_number}.pdf',
            mimetype='application/pdf'
        )
    
    @app.route('/reports/<int:report_id>/regenerate', methods=['POST'])
    def regenerate_pdf(report_id):
        """Перегенерация PDF"""
        report = Report.query.get_or_404(report_id)
        
        success, result = report_generator.generate_pdf(report)
        if success:
            db.session.commit()
            flash('PDF успешно перегенерирован!', 'success')
        else:
            flash(f'Ошибка при генерации PDF: {result}', 'danger')
        
        return redirect(url_for('view_report', report_id=report_id))
    
    @app.route('/reports/<int:report_id>/delete', methods=['POST'])
    def delete_report(report_id):
        """Удаление отчета"""
        report = Report.query.get_or_404(report_id)
        
        # Удаляем PDF файл если существует
        if report.pdf_path and os.path.exists(report.pdf_path):
            try:
                os.remove(report.pdf_path)
            except:
                pass
        
        db.session.delete(report)
        db.session.commit()
        
        flash('Отчет успешно удален!', 'success')
        return redirect(url_for('report_list'))
    
    # @app.route('/api/statistics')
    # def get_statistics():
    #     """Получение статистики"""
    #     try:
    #         total_reports = Report.query.count()
    #         generated_reports = Report.query.filter_by(status='generated').count()
    #         draft_reports = Report.query.filter_by(status='draft').count()
            
    #         return jsonify({
    #             'total_reports': total_reports,
    #             'generated_reports': generated_reports,
    #             'draft_reports': draft_reports
    #         })
    #     except Exception as e:
    #         app.logger.error(f"Ошибка при получении статистики: {e}")
    #         return jsonify({
    #             'total_reports': 0,
    #             'generated_reports': 0,
    #             'draft_reports': 0
    #         })
    
    @app.route('/init-db')
    def init_database():
        """Ручная инициализация БД (для отладки)"""
        try:
            db.create_all()
            
            # Создаем тестовый отчет если нет данных
            if Report.query.count() == 0:
                test_report = Report(
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
                    status='draft'
                )
                db.session.add(test_report)
                db.session.commit()
                flash('Создан тестовый отчет TEST-001', 'info')
            
            flash('База данных успешно инициализирована!', 'success')
        except Exception as e:
            flash(f'Ошибка инициализации БД: {str(e)}', 'danger')
        
        return redirect(url_for('index'))

def register_error_handlers(app):
    """Обработчики ошибок"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Internal server error: {error}")
        return render_template('500.html'), 500

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