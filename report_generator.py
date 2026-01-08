import os
import json
from datetime import datetime
from pathlib import Path
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from flask import current_app
import tempfile

class ReportGenerator:
    """Класс для генерации отчетов с использованием reportlab"""
    
    def __init__(self, app=None):
        self.app = app
        self.font_name = 'Helvetica'  # шрифт по умолчанию
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация с Flask приложением"""
        self.app = app
        
        # Регистрируем русский шрифт
        self._register_russian_font()
        
        # Создаем директории
        self.reports_dir = Path(app.config['REPORTS_FOLDER'])
        self.reports_dir.mkdir(exist_ok=True)
    
    def render_report_html(self, report):
        """Рендеринг HTML отчета (для предпросмотра)"""
        works = report.get_works()
        parts = report.get_parts()
        
        # Рассчитываем итоги
        works_total = sum(w.get('total', 0) for w in works)
        parts_total = sum(p.get('total', 0) for p in parts)
        total_amount = works_total + parts_total
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Акт №{report.order_number}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .table th, .table td {{ border: 1px solid #000; padding: 8px; }}
                .table th {{ background-color: #f0f0f0; }}
                .total {{ font-weight: bold; text-align: right; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>АКТ ВЫПОЛНЕННЫХ РАБОТ</h1>
                <p>к заказ-наряду № {report.order_number} от «{report.order_date}»</p>
            </div>
            
            <p><strong>Исполнитель:</strong> {report.executor_name}</p>
            <p><strong>Заказчик:</strong> {report.customer_name}</p>
            <p><strong>ТС:</strong> {report.vehicle_make} {report.vehicle_model}</p>
            
            <h3>Выполненные работы:</h3>
            <table class="table">
                <tr>
                    <th>№</th><th>Наименование</th><th>Время</th><th>Стоимость</th>
                </tr>
        """
        
        for i, work in enumerate(works, 1):
            html += f"""
                <tr>
                    <td>{i}</td>
                    <td>{work.get('name', '')}</td>
                    <td>{work.get('time', 0)} час.</td>
                    <td>{work.get('total', 0):.2f} руб.</td>
                </tr>
            """
        
        html += f"""
            </table>
            
            <h3>Запасные части:</h3>
            <table class="table">
                <tr>
                    <th>№</th><th>Наименование</th><th>Кол-во</th><th>Цена</th><th>Сумма</th>
                </tr>
        """
        
        for i, part in enumerate(parts, 1):
            html += f"""
                <tr>
                    <td>{i}</td>
                    <td>{part.get('name', '')}</td>
                    <td>{part.get('quantity', 0)} {part.get('unit', 'шт.')}</td>
                    <td>{part.get('price', 0):.2f} руб.</td>
                    <td>{part.get('total', 0):.2f} руб.</td>
                </tr>
            """
        
        html += f"""
            </table>
            
            <div class="total">
                <p>Общая сумма: {total_amount:.2f} руб.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    def _register_russian_font(self):
        """Регистрация шрифта с поддержкой кириллицы"""
        try:
            # Список путей к шрифтам с кириллицей
            font_paths = [
                # Windows
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/ARIAL.TTF',
                'C:/Windows/Fonts/tahoma.ttf',
                'C:/Windows/Fonts/times.ttf',
                # Linux (установите пакеты: fonts-liberation или ttf-mscorefonts-installer)
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                # macOS
                '/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Supplemental/Arial.ttf',
            ]
            
            # Пытаемся найти и зарегистрировать шрифт
            registered = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        # Регистрируем обычный и жирный шрифты
                        pdfmetrics.registerFont(TTFont('RussianFont', font_path))
                        
                        # Пробуем зарегистрировать жирный вариант
                        bold_path = font_path.replace('.ttf', 'bd.ttf').replace('.TTF', 'bd.TTF')
                        if os.path.exists(bold_path):
                            pdfmetrics.registerFont(TTFont('RussianFont-Bold', bold_path))
                        else:
                            # Если жирного нет, используем обычный для жирного текста
                            pdfmetrics.registerFont(TTFont('RussianFont-Bold', font_path))
                        
                        self.font_name = 'RussianFont'
                        print(f"✓ Русский шрифт зарегистрирован: {font_path}")
                        registered = True
                        break
                    except Exception as e:
                        print(f"Не удалось зарегистрировать шрифт {font_path}: {e}")
                        continue
            
            if not registered:
                print("⚠ Предупреждение: не найден шрифт с кириллицей. Используется стандартный Helvetica")
                print("Установите шрифт Arial или используйте reportlab-fonts-cyrillic:")
                print("pip install reportlab-fonts-cyrillic")
                
        except Exception as e:
            print(f"Ошибка при регистрации шрифта: {e}")
    
    def _get_styles(self):
        """Создание стилей с русским шрифтом"""
        styles = getSampleStyleSheet()
        
        # Основной стиль с русским шрифтом
        styles.add(ParagraphStyle(
            name='RussianNormal',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            encoding='UTF-8'
        ))

        styles.add(ParagraphStyle(
            name='RussianLittle',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=6,
            encoding='UTF-8'
        ))
        
        styles.add(ParagraphStyle(
            name='RussianTitle',
            parent=styles['Heading1'],
            fontName=self.font_name + '-Bold',
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        styles.add(ParagraphStyle(
            name='RussianBold',
            parent=styles['Normal'],
            fontName=self.font_name + '-Bold',
            fontSize=10,
            spaceAfter=6
        ))
        
        return styles
    
    def generate_pdf(self, report, output_filename=None):
        """Генерация PDF из отчета с использованием reportlab"""
        try:
            # Генерируем имя файла
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f"act_{report.order_number}_{timestamp}.pdf"
            
            output_path = self.reports_dir / output_filename
            
            # Создаем PDF документ
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=1*cm,
                leftMargin=2*cm,
                topMargin=1*cm,
                bottomMargin=1*cm
            )
            
            # Получаем стили с русским шрифтом
            styles = self._get_styles()
            
            # Собираем содержимое
            story = []
            
            # Заголовок - ВАЖНО: использовать Paragraph для русского текста!
            story.append(Paragraph("АКТ ВЫПОЛНЕННЫХ РАБОТ", styles['RussianTitle']))
            story.append(Paragraph(
                f"к заказ-наряду № {report.order_number} от {report.order_date}", 
                styles['RussianTitle']
            ))
            story.append(Spacer(1, 20))
            
            # Информация об исполнителе и заказчике
            party_data = [
                [Paragraph("<b>Исполнитель:</b>", styles['RussianBold']), 
                 Paragraph("<b>Заказчик:</b>", styles['RussianBold'])],
                [Paragraph(f"СТО {str(report.executor_name or '')}", styles['RussianNormal']), 
                 Paragraph(str(report.customer_name or ''), styles['RussianNormal'])],
                [Paragraph(str(report.executor_address or ''), styles['RussianNormal']), 
                 Paragraph(str(report.customer_address or ''), styles['RussianNormal'])],
                [Paragraph(f"Тел. {str(report.executor_phone or '')}", styles['RussianNormal']), 
                 Paragraph(f"Тел. {str(report.customer_phone or '')}", styles['RussianNormal'])]
            ]
            
            party_table = Table(party_data, colWidths=[9*cm, 9*cm])
            party_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(party_table)
            story.append(Spacer(1, 20))
            
            # Транспортное средство
            vehicle_data = [
                [Paragraph("<b>Транспортное средство</b>", styles['RussianBold']), "", "", "", "", ""],
                [Paragraph("Марка ТС", styles['RussianNormal']), 
                 Paragraph("Модель", styles['RussianNormal']), 
                 Paragraph("Рег. знак", styles['RussianNormal']), 
                 Paragraph("VIN", styles['RussianNormal']), 
                 Paragraph("Год", styles['RussianNormal']), 
                 Paragraph("Пробег", styles['RussianNormal'])],
                [
                    Paragraph(str(report.vehicle_make or ''), styles['RussianNormal']),
                    Paragraph(str(report.vehicle_model or ''), styles['RussianNormal']),
                    Paragraph(str(report.vehicle_registration or ''), styles['RussianNormal']),
                    Paragraph(str(report.vehicle_vin or ''), styles['RussianNormal']),
                    Paragraph(str(report.vehicle_year or ''), styles['RussianNormal']),
                    Paragraph((str(report.vehicle_mileage or '') + ' км' if report.vehicle_mileage else ''), styles['RussianNormal'])
                ]
            ]
            
            vehicle_table = Table(vehicle_data, colWidths=[3*cm, 3*cm, 3*cm, 4*cm, 2*cm, 3*cm])
            vehicle_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
                ('GRID', (0, 1), (-1, -1), 0.5, colors.black),
                ('SPAN', (0, 0), (-1, 0)),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ]))
            story.append(vehicle_table)
            story.append(Spacer(1, 20))
            
            # Причина обращения
            story.append(Paragraph("<b>Причина обращения:</b>", styles['RussianBold']))
            story.append(Paragraph(str(report.reason or ''), styles['RussianNormal']))
            story.append(Spacer(1, 20))
            
            # Выполненные работы
            works = report.get_works()
            if works:
                story.append(Paragraph("<b>Выполненные работы:</b>", styles['RussianBold']))
                work_data = [[
                    Paragraph("№", styles['RussianNormal']),
                    Paragraph("Наименование работ", styles['RussianNormal']),
                    Paragraph("Время, час", styles['RussianNormal']),
                    Paragraph("Скидка, %", styles['RussianNormal']),
                    Paragraph("Стоимость, руб.", styles['RussianNormal']),
                    Paragraph("Итого, руб.", styles['RussianNormal'])
                ]]
                
                for i, work in enumerate(works, 1):
                    work_data.append([
                        Paragraph(str(i), styles['RussianNormal']),
                        Paragraph(str(work.get('name', '')), styles['RussianNormal']),
                        Paragraph(str(work.get('time', 0)), styles['RussianNormal']),
                        Paragraph(str(work.get('discount', 0)) if work.get('discount', 0) != 0 else '-', styles['RussianNormal']),
                        Paragraph(str(work.get('rate', 0)), styles['RussianNormal']),
                        Paragraph(str(work.get('total', 0)), styles['RussianNormal'])
                    ])
                
                # Добавляем итог
                works_total = sum(w.get('total', 0) for w in works)
                work_data.append([
                    Paragraph("", styles['RussianNormal']),
                    Paragraph("", styles['RussianNormal']),
                    Paragraph("", styles['RussianNormal']),
                    Paragraph("", styles['RussianNormal']),
                    Paragraph("<b>Итого:</b>", styles['RussianNormal']),
                    Paragraph(f"<b>{works_total:.2f}</b>", styles['RussianNormal'])
                ])
                
                works_table = Table(work_data, colWidths=[1*cm, 8*cm, 2*cm, 2*cm, 3*cm, 3*cm])
                works_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -2), 0.5, colors.black),
                    ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
                    ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                ]))
                story.append(works_table)
                story.append(Spacer(1, 20))
            
            # Запасные части
            parts = report.get_parts()
            if parts:
                story.append(Paragraph("<b>Запасные части:</b>", styles['RussianBold']))
                part_data = [[
                    Paragraph("№", styles['RussianNormal']),
                    Paragraph("Наименование", styles['RussianNormal']),
                    Paragraph("Ед.", styles['RussianNormal']),
                    Paragraph("Кол-во", styles['RussianNormal']),
                    Paragraph("Цена, руб.", styles['RussianNormal']),
                    Paragraph("Сумма, руб.", styles['RussianNormal'])
                ]]
                
                for i, part in enumerate(parts, 1):
                    part_data.append([
                        Paragraph(str(i), styles['RussianNormal']),
                        Paragraph(str(part.get('name', '')), styles['RussianNormal']),
                        Paragraph(str(part.get('unit', 'шт.')), styles['RussianNormal']),
                        Paragraph(str(part.get('quantity', 0)), styles['RussianNormal']),
                        Paragraph(str(part.get('price', 0)), styles['RussianNormal']),
                        Paragraph(str(part.get('total', 0)), styles['RussianNormal'])
                    ])
                
                # Добавляем итог
                parts_total = sum(p.get('total', 0) for p in parts)
                part_data.append([
                    Paragraph("", styles['RussianNormal']),
                    Paragraph("", styles['RussianNormal']),
                    Paragraph("", styles['RussianNormal']),
                    Paragraph("", styles['RussianNormal']),
                    Paragraph("<b>Итого:</b>", styles['RussianNormal']),
                    Paragraph(f"<b>{parts_total:.2f}</b>", styles['RussianNormal'])
                ])
                
                parts_table = Table(part_data, colWidths=[1*cm, 8*cm, 1.5*cm, 2*cm, 3*cm, 3*cm])
                parts_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -2), 0.5, colors.black),
                    ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
                    ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                ]))
                story.append(parts_table)
                story.append(Spacer(1, 20))
            
            # Итоговая сумма
            total_amount = report.total_amount or 0
            rubles = int(total_amount)
            kopecks = int((total_amount - rubles) * 100)
            
            total_data = [
                [Paragraph("<b>Всего без НДС, руб.:</b>", styles['RussianNormal']),
                 Paragraph(f"<b>{total_amount * 0.78:.2f}</b>", styles['RussianNormal'])],
                [Paragraph("<b>Ставка НДС, %:</b>", styles['RussianNormal']),
                 Paragraph("<b>22</b>", styles['RussianNormal'])],
                [Paragraph("<b>Сумма НДС, руб.:</b>", styles['RussianNormal']),
                 Paragraph(f"<b>{total_amount * 0.22:.2f}</b>", styles['RussianNormal'])],
                [Paragraph("<b>Общая стоимость, руб.:</b>", styles['RussianNormal']),
                 Paragraph(f"<b>{total_amount:.2f}</b>", styles['RussianBold'])]
            ]
            
            total_table = Table(total_data, colWidths=[12*cm, 6*cm])
            total_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ]))
            story.append(total_table)
            story.append(Spacer(1, 10))
            
            story.append(Paragraph(
                f"<b>Общая сумма по Заказ-наряду: {rubles} руб. {kopecks:02d} копеек. Без НДС.</b>",
                styles['RussianNormal']
            ))
            story.append(Spacer(1, 20))
            
            # Гарантийные обязательства
            if report.warranty_info:
                story.append(Paragraph("<b>Гарантийные обязательства:</b>", styles['RussianBold']))
                story.append(Paragraph(str(report.warranty_info), styles['RussianNormal']))
                story.append(Spacer(1, 20))
            
            # Подписи
            signature_data = [
                [Paragraph("Исполнитель", styles['RussianNormal']), 
                 Paragraph("Заказчик", styles['RussianNormal'])],
                [Paragraph("_____________________", styles['RussianNormal']), 
                 Paragraph("_____________________", styles['RussianNormal'])],
                [Paragraph(str(report.executor_name or ''), styles['RussianLittle']), 
                 Paragraph(str(report.customer_name or ''), styles['RussianLittle'])]
            ]
            
            signature_table = Table(signature_data, colWidths=[9*cm, 9*cm])
            signature_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(signature_table)
            
            # Генерируем PDF
            doc.build(story)
            
            # Проверяем что файл создан
            if os.path.exists(output_path):
                # Обновляем отчет
                report.pdf_path = str(output_path)
                report.status = 'generated'
                report.generated_at = datetime.now()
                
                return True, output_path
            else:
                return False, "PDF файл не был создан"
                
        except Exception as e:
            current_app.logger.error(f"Ошибка при генерации PDF: {e}", exc_info=True)
            return False, str(e)

# Создаем экземпляр генератора
report_generator = ReportGenerator()