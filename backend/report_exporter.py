"""
Report Export Utilities
Generate professional presentation-quality reports in Word, Excel, and PDF formats
"""

import io
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from collections import defaultdict
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.platypus import Image as RLImage
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import PieChart, BarChart, Reference
from openpyxl.chart.label import DataLabelList
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml

logger = logging.getLogger(__name__)

# Intertech brand colors
BRAND_PRIMARY = '#E11D48'  # Rose/Red
BRAND_DARK = '#18181B'  # Dark background
BRAND_SECONDARY = '#27272A'  # Secondary dark
BRAND_SUCCESS = '#10B981'  # Green
BRAND_WARNING = '#F59E0B'  # Orange
BRAND_INFO = '#3B82F6'  # Blue

# Category colors
CATEGORY_COLORS = {
    'api-test': '#3B82F6',  # Blue
    'ui-test': '#10B981',  # Green
    'regression': '#F59E0B',  # Orange
    'bug-tracking': '#EF4444',  # Red
    'documentation': '#8B5CF6',  # Purple
}

# Status labels in Turkish
STATUS_LABELS = {
    'backlog': 'Backlog',
    'today_planned': 'Bugün Planlanan',
    'in_progress': 'Devam Ediyor',
    'blocked': 'Bloke',
    'completed': 'Tamamlandı'
}

# Priority labels in Turkish
PRIORITY_LABELS = {
    'low': 'Düşük',
    'medium': 'Orta',
    'high': 'Yüksek',
    'critical': 'Kritik'
}

# Category labels in Turkish
CATEGORY_LABELS = {
    'api-test': 'API Testi',
    'ui-test': 'UI Testi',
    'regression': 'Regresyon',
    'bug-tracking': 'Bug Tracking',
    'documentation': 'Test Dokümantasyonu'
}


class ReportExporter:
    """Generate professional presentation-quality reports in multiple formats"""
    
    @staticmethod
    def _calculate_monthly_stats(tasks: List[Dict]) -> Dict:
        """Calculate monthly task statistics"""
        monthly_data = defaultdict(lambda: {'created': 0, 'completed': 0})
        
        for task in tasks:
            created_at = task.get('created_at', '')
            completed_at = task.get('completed_at')
            
            if created_at:
                try:
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    month_key = created_date.strftime('%Y-%m')
                    monthly_data[month_key]['created'] += 1
                except:
                    pass
            
            if completed_at:
                try:
                    completed_date = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    month_key = completed_date.strftime('%Y-%m')
                    monthly_data[month_key]['completed'] += 1
                except:
                    pass
        
        return dict(monthly_data)
    
    @staticmethod
    def _calculate_category_stats(tasks: List[Dict]) -> Dict:
        """Calculate category-based statistics"""
        category_data = defaultdict(lambda: {'total': 0, 'completed': 0, 'in_progress': 0})
        
        for task in tasks:
            category = task.get('category_id', 'other')
            status = task.get('status', '')
            
            category_data[category]['total'] += 1
            
            if status == 'completed':
                category_data[category]['completed'] += 1
            elif status == 'in_progress':
                category_data[category]['in_progress'] += 1
        
        return dict(category_data)
    
    @staticmethod
    def _calculate_priority_stats(tasks: List[Dict]) -> Dict:
        """Calculate priority-based statistics"""
        priority_data = defaultdict(int)
        
        for task in tasks:
            priority = task.get('priority', 'medium')
            priority_data[priority] += 1
        
        return dict(priority_data)
    
    @staticmethod
    def generate_pdf_report(data: Dict[str, Any]) -> bytes:
        """Generate professional PDF report with charts and statistics"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            topMargin=1*cm,
            bottomMargin=1*cm,
            leftMargin=1.5*cm,
            rightMargin=1.5*cm
        )
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor(BRAND_PRIMARY),
            spaceAfter=20,
            alignment=1,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#71717A'),
            spaceAfter=30,
            alignment=1
        )
        
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor(BRAND_PRIMARY),
            spaceBefore=20,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        # Get user info
        user_name = data.get('user_name', 'Kullanıcı')
        
        # ===== COVER SECTION =====
        story.append(Spacer(1, 2*cm))
        story.append(Paragraph("QA Task Manager", title_style))
        story.append(Paragraph("Performans Raporu", subtitle_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Report info box
        report_info = f"""
        <para align="center">
        <b>Hazırlayan:</b> {user_name}<br/>
        <b>Rapor Tarihi:</b> {datetime.now().strftime('%d %B %Y')}<br/>
        <b>Dönem:</b> Son 30 Gün
        </para>
        """
        story.append(Paragraph(report_info, styles['Normal']))
        story.append(Spacer(1, 1*cm))
        
        # ===== EXECUTIVE SUMMARY =====
        stats = data.get('stats', {})
        tasks = data.get('tasks', [])
        
        if stats:
            story.append(Paragraph("Yönetici Özeti", section_title_style))
            
            # KPI Cards as table
            total = stats.get('total_tasks', 0)
            completed = stats.get('completed_tasks', 0)
            in_progress = stats.get('in_progress_tasks', 0)
            todo = stats.get('todo_tasks', 0)
            overdue = stats.get('overdue_tasks', 0)
            completion_rate = stats.get('completion_rate', 0)
            
            kpi_data = [
                ['TOPLAM GÖREV', 'TAMAMLANAN', 'DEVAM EDEN', 'BEKLEYEN', 'GECİKMİŞ'],
                [str(total), str(completed), str(in_progress), str(todo), str(overdue)]
            ]
            
            kpi_table = Table(kpi_data, colWidths=[3.2*cm]*5)
            kpi_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BRAND_DARK)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                # Data row
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F5F5F5')),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor(BRAND_DARK)),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, 1), 20),
                ('BOTTOMPADDING', (0, 1), (-1, 1), 15),
                ('TOPPADDING', (0, 1), (-1, 1), 15),
                # Grid
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(BRAND_DARK)),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5E5')),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 0.5*cm))
            
            # Completion Rate Progress Bar
            progress_text = f"Tamamlanma Oranı: %{completion_rate}"
            story.append(Paragraph(f"<b>{progress_text}</b>", styles['Normal']))
            
            # Simple progress bar using table
            filled_width = min(completion_rate / 100 * 16, 16)
            empty_width = 16 - filled_width
            
            progress_data = [['', '']]
            progress_table = Table(progress_data, colWidths=[filled_width*cm, empty_width*cm])
            progress_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor(BRAND_SUCCESS)),
                ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#E5E5E5')),
                ('LINEBELOW', (0, 0), (-1, 0), 0, colors.white),
                ('LINEABOVE', (0, 0), (-1, 0), 0, colors.white),
            ]))
            story.append(progress_table)
            story.append(Spacer(1, 1*cm))
        
        # ===== CATEGORY BREAKDOWN =====
        if tasks:
            story.append(Paragraph("Kategori Bazlı Analiz", section_title_style))
            
            category_stats = ReportExporter._calculate_category_stats(tasks)
            
            if category_stats:
                cat_data = [['Kategori', 'Toplam', 'Tamamlanan', 'Devam Eden', 'Tamamlanma %']]
                
                for cat_id, cat_stats in category_stats.items():
                    cat_name = CATEGORY_LABELS.get(cat_id, cat_id)
                    total = cat_stats['total']
                    completed = cat_stats['completed']
                    in_prog = cat_stats['in_progress']
                    rate = round(completed / total * 100, 1) if total > 0 else 0
                    
                    cat_data.append([cat_name, str(total), str(completed), str(in_prog), f'%{rate}'])
                
                cat_table = Table(cat_data, colWidths=[5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm])
                cat_table.setStyle(TableStyle([
                    # Header
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BRAND_PRIMARY)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 0), (-1, 0), 12),
                    # Data rows
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                    ('TOPPADDING', (0, 1), (-1, -1), 8),
                    # Alternating row colors
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
                    # Grid
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(BRAND_PRIMARY)),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5E5')),
                ]))
                story.append(cat_table)
                story.append(Spacer(1, 1*cm))
        
        # ===== PRIORITY BREAKDOWN =====
        if tasks:
            story.append(Paragraph("Öncelik Dağılımı", section_title_style))
            
            priority_stats = ReportExporter._calculate_priority_stats(tasks)
            
            if priority_stats:
                priority_colors = {
                    'critical': BRAND_PRIMARY,
                    'high': '#EF4444',
                    'medium': BRAND_WARNING,
                    'low': '#71717A'
                }
                
                priority_data = [['Öncelik', 'Görev Sayısı', 'Oran']]
                total_tasks = sum(priority_stats.values())
                
                for priority in ['critical', 'high', 'medium', 'low']:
                    if priority in priority_stats:
                        count = priority_stats[priority]
                        rate = round(count / total_tasks * 100, 1) if total_tasks > 0 else 0
                        priority_data.append([
                            PRIORITY_LABELS.get(priority, priority),
                            str(count),
                            f'%{rate}'
                        ])
                
                if len(priority_data) > 1:
                    priority_table = Table(priority_data, colWidths=[5*cm, 5*cm, 5*cm])
                    priority_table.setStyle(TableStyle([
                        # Header
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BRAND_DARK)),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('TOPPADDING', (0, 0), (-1, 0), 12),
                        # Data rows
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                        ('TOPPADDING', (0, 1), (-1, -1), 8),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
                        # Grid
                        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(BRAND_DARK)),
                        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5E5')),
                    ]))
                    story.append(priority_table)
                    story.append(Spacer(1, 1*cm))
        
        # ===== MONTHLY PERFORMANCE =====
        if tasks:
            monthly_stats = ReportExporter._calculate_monthly_stats(tasks)
            
            if monthly_stats:
                story.append(Paragraph("Aylık Performans", section_title_style))
                
                monthly_data = [['Ay', 'Oluşturulan', 'Tamamlanan', 'Performans']]
                
                sorted_months = sorted(monthly_stats.keys(), reverse=True)[:6]  # Son 6 ay
                
                for month in sorted_months:
                    stats = monthly_stats[month]
                    created = stats['created']
                    completed = stats['completed']
                    perf = round(completed / created * 100, 1) if created > 0 else 0
                    
                    # Format month name in Turkish
                    try:
                        month_date = datetime.strptime(month, '%Y-%m')
                        month_names = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                                      'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
                        month_name = f"{month_names[month_date.month - 1]} {month_date.year}"
                    except:
                        month_name = month
                    
                    monthly_data.append([month_name, str(created), str(completed), f'%{perf}'])
                
                if len(monthly_data) > 1:
                    monthly_table = Table(monthly_data, colWidths=[5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
                    monthly_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BRAND_INFO)),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('TOPPADDING', (0, 0), (-1, 0), 12),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                        ('TOPPADDING', (0, 1), (-1, -1), 8),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F9FF')]),
                        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(BRAND_INFO)),
                        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5E5')),
                    ]))
                    story.append(monthly_table)
                    story.append(Spacer(1, 1*cm))
        
        # ===== TASK LIST =====
        if tasks:
            story.append(PageBreak())
            story.append(Paragraph("Görev Detayları", section_title_style))
            
            task_data = [['Başlık', 'Kategori', 'Durum', 'Öncelik']]
            
            for task in tasks[:25]:  # Limit to 25 for PDF
                title = task.get('title', '')[:35]
                if len(task.get('title', '')) > 35:
                    title += '...'
                
                category = CATEGORY_LABELS.get(task.get('category_id', ''), task.get('category_id', ''))
                status = STATUS_LABELS.get(task.get('status', ''), task.get('status', ''))
                priority = PRIORITY_LABELS.get(task.get('priority', ''), task.get('priority', ''))
                
                task_data.append([title, category, status, priority])
            
            task_table = Table(task_data, colWidths=[7*cm, 3.5*cm, 3*cm, 2.5*cm])
            task_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BRAND_DARK)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(BRAND_DARK)),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5E5')),
            ]))
            story.append(task_table)
        
        # ===== FOOTER =====
        story.append(Spacer(1, 1*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#71717A'),
            alignment=1
        )
        story.append(Paragraph("Bu rapor QA Task Manager tarafından otomatik olarak oluşturulmuştur.", footer_style))
        story.append(Paragraph(f"Intertech QA Ekibi - {datetime.now().strftime('%Y')}", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def generate_excel_report(data: Dict[str, Any]) -> bytes:
        """Generate professional Excel report with charts"""
        wb = Workbook()
        
        # Styles
        title_font = Font(size=24, bold=True, color="E11D48")
        header_font = Font(size=12, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="18181B", end_color="18181B", fill_type="solid")
        accent_fill = PatternFill(start_color="E11D48", end_color="E11D48", fill_type="solid")
        light_fill = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin', color='E5E5E5'),
            right=Side(style='thin', color='E5E5E5'),
            top=Side(style='thin', color='E5E5E5'),
            bottom=Side(style='thin', color='E5E5E5')
        )
        
        user_name = data.get('user_name', 'Kullanıcı')
        stats = data.get('stats', {})
        tasks = data.get('tasks', [])
        
        # ===== DASHBOARD SHEET =====
        ws_dash = wb.active
        ws_dash.title = "Dashboard"
        
        # Title
        ws_dash.merge_cells('A1:G1')
        ws_dash['A1'] = "QA Task Manager - Performans Raporu"
        ws_dash['A1'].font = title_font
        ws_dash['A1'].alignment = Alignment(horizontal='center')
        
        ws_dash.merge_cells('A2:G2')
        ws_dash['A2'] = f"Hazırlayan: {user_name} | Tarih: {datetime.now().strftime('%d.%m.%Y')}"
        ws_dash['A2'].alignment = Alignment(horizontal='center')
        ws_dash['A2'].font = Font(color="71717A")
        
        # KPI Section
        ws_dash['A4'] = "PERFORMANS GÖSTERGELERİ"
        ws_dash['A4'].font = Font(size=14, bold=True, color="E11D48")
        ws_dash.merge_cells('A4:G4')
        
        if stats:
            kpi_headers = ['Toplam Görev', 'Tamamlanan', 'Devam Eden', 'Bekleyen', 'Gecikmiş', 'Tamamlanma %']
            kpi_values = [
                stats.get('total_tasks', 0),
                stats.get('completed_tasks', 0),
                stats.get('in_progress_tasks', 0),
                stats.get('todo_tasks', 0),
                stats.get('overdue_tasks', 0),
                f"%{stats.get('completion_rate', 0)}"
            ]
            
            for col, (header, value) in enumerate(zip(kpi_headers, kpi_values), 1):
                header_cell = ws_dash.cell(row=6, column=col, value=header)
                header_cell.font = header_font
                header_cell.fill = header_fill
                header_cell.alignment = Alignment(horizontal='center')
                header_cell.border = thin_border
                
                value_cell = ws_dash.cell(row=7, column=col, value=value)
                value_cell.font = Font(size=18, bold=True)
                value_cell.alignment = Alignment(horizontal='center')
                value_cell.border = thin_border
                
                ws_dash.column_dimensions[get_column_letter(col)].width = 15
        
        # Category Analysis Section
        if tasks:
            ws_dash['A10'] = "KATEGORİ ANALİZİ"
            ws_dash['A10'].font = Font(size=14, bold=True, color="E11D48")
            
            category_stats = ReportExporter._calculate_category_stats(tasks)
            
            cat_headers = ['Kategori', 'Toplam', 'Tamamlanan', 'Devam Eden', 'Tamamlanma %']
            for col, header in enumerate(cat_headers, 1):
                cell = ws_dash.cell(row=12, column=col, value=header)
                cell.font = header_font
                cell.fill = accent_fill
                cell.alignment = Alignment(horizontal='center')
                cell.border = thin_border
            
            row = 13
            for cat_id, cat_stats in category_stats.items():
                cat_name = CATEGORY_LABELS.get(cat_id, cat_id)
                total = cat_stats['total']
                completed = cat_stats['completed']
                in_prog = cat_stats['in_progress']
                rate = round(completed / total * 100, 1) if total > 0 else 0
                
                ws_dash.cell(row=row, column=1, value=cat_name).border = thin_border
                ws_dash.cell(row=row, column=2, value=total).border = thin_border
                ws_dash.cell(row=row, column=3, value=completed).border = thin_border
                ws_dash.cell(row=row, column=4, value=in_prog).border = thin_border
                ws_dash.cell(row=row, column=5, value=f"%{rate}").border = thin_border
                
                for col in range(1, 6):
                    ws_dash.cell(row=row, column=col).alignment = Alignment(horizontal='center')
                    if row % 2 == 0:
                        ws_dash.cell(row=row, column=col).fill = light_fill
                
                row += 1
            
            # Add pie chart for categories
            if len(category_stats) > 0:
                pie = PieChart()
                pie.title = "Kategori Dağılımı"
                labels = Reference(ws_dash, min_col=1, min_row=13, max_row=row-1)
                data_ref = Reference(ws_dash, min_col=2, min_row=12, max_row=row-1)
                pie.add_data(data_ref, titles_from_data=True)
                pie.set_categories(labels)
                pie.width = 12
                pie.height = 8
                ws_dash.add_chart(pie, "G10")
        
        # ===== TASKS SHEET =====
        ws_tasks = wb.create_sheet("Görevler")
        
        task_headers = ["#", "Başlık", "Kategori", "Durum", "Öncelik", "Oluşturulma", "Tamamlanma"]
        for col, header in enumerate(task_headers, 1):
            cell = ws_tasks.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        
        for row_num, task in enumerate(tasks, 2):
            ws_tasks.cell(row=row_num, column=1, value=row_num-1).border = thin_border
            ws_tasks.cell(row=row_num, column=2, value=task.get('title', '')).border = thin_border
            ws_tasks.cell(row=row_num, column=3, value=CATEGORY_LABELS.get(task.get('category_id', ''), task.get('category_id', ''))).border = thin_border
            ws_tasks.cell(row=row_num, column=4, value=STATUS_LABELS.get(task.get('status', ''), task.get('status', ''))).border = thin_border
            ws_tasks.cell(row=row_num, column=5, value=PRIORITY_LABELS.get(task.get('priority', ''), task.get('priority', ''))).border = thin_border
            
            created = task.get('created_at', '')
            if created:
                try:
                    created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    created = created_dt.strftime('%d.%m.%Y')
                except:
                    pass
            ws_tasks.cell(row=row_num, column=6, value=created).border = thin_border
            
            completed = task.get('completed_at', '')
            if completed:
                try:
                    completed_dt = datetime.fromisoformat(completed.replace('Z', '+00:00'))
                    completed = completed_dt.strftime('%d.%m.%Y')
                except:
                    pass
            ws_tasks.cell(row=row_num, column=7, value=completed or '-').border = thin_border
            
            for col in range(1, 8):
                ws_tasks.cell(row=row_num, column=col).alignment = Alignment(horizontal='center')
                if row_num % 2 == 0:
                    ws_tasks.cell(row=row_num, column=col).fill = light_fill
        
        # Column widths
        ws_tasks.column_dimensions['A'].width = 5
        ws_tasks.column_dimensions['B'].width = 40
        ws_tasks.column_dimensions['C'].width = 18
        ws_tasks.column_dimensions['D'].width = 15
        ws_tasks.column_dimensions['E'].width = 12
        ws_tasks.column_dimensions['F'].width = 15
        ws_tasks.column_dimensions['G'].width = 15
        
        # ===== MONTHLY STATS SHEET =====
        ws_monthly = wb.create_sheet("Aylık İstatistik")
        
        monthly_stats = ReportExporter._calculate_monthly_stats(tasks)
        
        monthly_headers = ['Ay', 'Oluşturulan', 'Tamamlanan', 'Performans %']
        for col, header in enumerate(monthly_headers, 1):
            cell = ws_monthly.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        
        row = 2
        for month in sorted(monthly_stats.keys(), reverse=True):
            stats = monthly_stats[month]
            created = stats['created']
            completed = stats['completed']
            perf = round(completed / created * 100, 1) if created > 0 else 0
            
            try:
                month_date = datetime.strptime(month, '%Y-%m')
                month_names = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                              'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
                month_name = f"{month_names[month_date.month - 1]} {month_date.year}"
            except:
                month_name = month
            
            ws_monthly.cell(row=row, column=1, value=month_name).border = thin_border
            ws_monthly.cell(row=row, column=2, value=created).border = thin_border
            ws_monthly.cell(row=row, column=3, value=completed).border = thin_border
            ws_monthly.cell(row=row, column=4, value=f"%{perf}").border = thin_border
            
            for col in range(1, 5):
                ws_monthly.cell(row=row, column=col).alignment = Alignment(horizontal='center')
                if row % 2 == 0:
                    ws_monthly.cell(row=row, column=col).fill = light_fill
            
            row += 1
        
        # Column widths
        for col in range(1, 5):
            ws_monthly.column_dimensions[get_column_letter(col)].width = 18
        
        # Add bar chart
        if row > 2:
            chart = BarChart()
            chart.title = "Aylık Performans"
            chart.x_axis.title = "Ay"
            chart.y_axis.title = "Görev Sayısı"
            
            data_ref = Reference(ws_monthly, min_col=2, max_col=3, min_row=1, max_row=row-1)
            cats = Reference(ws_monthly, min_col=1, min_row=2, max_row=row-1)
            
            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats)
            chart.shape = 4
            chart.width = 15
            chart.height = 10
            
            ws_monthly.add_chart(chart, "F1")
        
        # Save
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def generate_word_report(data: Dict[str, Any]) -> bytes:
        """Generate professional Word document report"""
        doc = Document()
        
        user_name = data.get('user_name', 'Kullanıcı')
        stats = data.get('stats', {})
        tasks = data.get('tasks', [])
        
        # ===== TITLE PAGE =====
        title = doc.add_heading('QA Task Manager', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in title.runs:
            run.font.color.rgb = RGBColor(225, 29, 72)  # Brand primary
        
        subtitle = doc.add_paragraph('Performans Raporu')
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in subtitle.runs:
            run.font.size = Pt(18)
            run.font.color.rgb = RGBColor(113, 113, 122)
        
        doc.add_paragraph()
        
        # Report info
        info_para = doc.add_paragraph()
        info_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        info_para.add_run(f"Hazırlayan: {user_name}\n").bold = True
        info_para.add_run(f"Rapor Tarihi: {datetime.now().strftime('%d %B %Y')}\n")
        info_para.add_run("Dönem: Son 30 Gün")
        
        doc.add_page_break()
        
        # ===== EXECUTIVE SUMMARY =====
        summary_heading = doc.add_heading('Yönetici Özeti', level=1)
        for run in summary_heading.runs:
            run.font.color.rgb = RGBColor(225, 29, 72)
        
        if stats:
            # KPI Table
            kpi_table = doc.add_table(rows=2, cols=5)
            kpi_table.style = 'Table Grid'
            kpi_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            headers = ['Toplam Görev', 'Tamamlanan', 'Devam Eden', 'Bekleyen', 'Gecikmiş']
            values = [
                str(stats.get('total_tasks', 0)),
                str(stats.get('completed_tasks', 0)),
                str(stats.get('in_progress_tasks', 0)),
                str(stats.get('todo_tasks', 0)),
                str(stats.get('overdue_tasks', 0))
            ]
            
            # Header row
            header_row = kpi_table.rows[0]
            for i, header in enumerate(headers):
                cell = header_row.cells[i]
                cell.text = header
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in cell.paragraphs[0].runs:
                    run.font.bold = True
                    run.font.size = Pt(10)
                    run.font.color.rgb = RGBColor(255, 255, 255)
                # Set background color
                shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="18181B"/>')
                cell._tc.get_or_add_tcPr().append(shading)
            
            # Value row
            value_row = kpi_table.rows[1]
            for i, value in enumerate(values):
                cell = value_row.cells[i]
                cell.text = value
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in cell.paragraphs[0].runs:
                    run.font.bold = True
                    run.font.size = Pt(20)
            
            doc.add_paragraph()
            
            # Completion rate
            rate = stats.get('completion_rate', 0)
            rate_para = doc.add_paragraph()
            rate_para.add_run(f"Tamamlanma Oranı: ").bold = True
            rate_run = rate_para.add_run(f"%{rate}")
            rate_run.font.size = Pt(24)
            rate_run.font.bold = True
            rate_run.font.color.rgb = RGBColor(16, 185, 129)  # Green
        
        doc.add_paragraph()
        
        # ===== CATEGORY ANALYSIS =====
        if tasks:
            cat_heading = doc.add_heading('Kategori Bazlı Analiz', level=1)
            for run in cat_heading.runs:
                run.font.color.rgb = RGBColor(225, 29, 72)
            
            category_stats = ReportExporter._calculate_category_stats(tasks)
            
            if category_stats:
                cat_table = doc.add_table(rows=len(category_stats) + 1, cols=5)
                cat_table.style = 'Table Grid'
                
                # Header
                headers = ['Kategori', 'Toplam', 'Tamamlanan', 'Devam Eden', 'Tamamlanma %']
                header_row = cat_table.rows[0]
                for i, header in enumerate(headers):
                    cell = header_row.cells[i]
                    cell.text = header
                    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in cell.paragraphs[0].runs:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="E11D48"/>')
                    cell._tc.get_or_add_tcPr().append(shading)
                
                # Data rows
                for row_idx, (cat_id, cat_stats) in enumerate(category_stats.items(), 1):
                    row = cat_table.rows[row_idx]
                    cat_name = CATEGORY_LABELS.get(cat_id, cat_id)
                    total = cat_stats['total']
                    completed = cat_stats['completed']
                    in_prog = cat_stats['in_progress']
                    rate = round(completed / total * 100, 1) if total > 0 else 0
                    
                    values = [cat_name, str(total), str(completed), str(in_prog), f'%{rate}']
                    for i, value in enumerate(values):
                        cell = row.cells[i]
                        cell.text = value
                        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()
        
        # ===== MONTHLY PERFORMANCE =====
        if tasks:
            monthly_stats = ReportExporter._calculate_monthly_stats(tasks)
            
            if monthly_stats:
                monthly_heading = doc.add_heading('Aylık Performans', level=1)
                for run in monthly_heading.runs:
                    run.font.color.rgb = RGBColor(225, 29, 72)
                
                sorted_months = sorted(monthly_stats.keys(), reverse=True)[:6]
                
                monthly_table = doc.add_table(rows=len(sorted_months) + 1, cols=4)
                monthly_table.style = 'Table Grid'
                
                # Header
                headers = ['Ay', 'Oluşturulan', 'Tamamlanan', 'Performans']
                header_row = monthly_table.rows[0]
                for i, header in enumerate(headers):
                    cell = header_row.cells[i]
                    cell.text = header
                    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in cell.paragraphs[0].runs:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="3B82F6"/>')
                    cell._tc.get_or_add_tcPr().append(shading)
                
                # Data rows
                for row_idx, month in enumerate(sorted_months, 1):
                    row = monthly_table.rows[row_idx]
                    stats_m = monthly_stats[month]
                    created = stats_m['created']
                    completed = stats_m['completed']
                    perf = round(completed / created * 100, 1) if created > 0 else 0
                    
                    try:
                        month_date = datetime.strptime(month, '%Y-%m')
                        month_names = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                                      'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
                        month_name = f"{month_names[month_date.month - 1]} {month_date.year}"
                    except:
                        month_name = month
                    
                    values = [month_name, str(created), str(completed), f'%{perf}']
                    for i, value in enumerate(values):
                        cell = row.cells[i]
                        cell.text = value
                        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_page_break()
        
        # ===== TASK DETAILS =====
        if tasks:
            task_heading = doc.add_heading('Görev Detayları', level=1)
            for run in task_heading.runs:
                run.font.color.rgb = RGBColor(225, 29, 72)
            
            task_table = doc.add_table(rows=min(len(tasks), 20) + 1, cols=4)
            task_table.style = 'Table Grid'
            
            # Header
            headers = ['Başlık', 'Kategori', 'Durum', 'Öncelik']
            header_row = task_table.rows[0]
            for i, header in enumerate(headers):
                cell = header_row.cells[i]
                cell.text = header
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in cell.paragraphs[0].runs:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
                shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="18181B"/>')
                cell._tc.get_or_add_tcPr().append(shading)
            
            # Task rows
            for row_idx, task in enumerate(tasks[:20], 1):
                row = task_table.rows[row_idx]
                
                title = task.get('title', '')[:40]
                if len(task.get('title', '')) > 40:
                    title += '...'
                
                values = [
                    title,
                    CATEGORY_LABELS.get(task.get('category_id', ''), task.get('category_id', '')),
                    STATUS_LABELS.get(task.get('status', ''), task.get('status', '')),
                    PRIORITY_LABELS.get(task.get('priority', ''), task.get('priority', ''))
                ]
                
                for i, value in enumerate(values):
                    cell = row.cells[i]
                    cell.text = value
                    if i > 0:
                        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # ===== FOOTER =====
        doc.add_paragraph()
        footer = doc.add_paragraph()
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer_run = footer.add_run("Bu rapor QA Task Manager tarafından otomatik olarak oluşturulmuştur.\nIntertech QA Ekibi")
        footer_run.font.size = Pt(9)
        footer_run.font.color.rgb = RGBColor(113, 113, 122)
        
        # Save
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()


# Global exporter instance
report_exporter = ReportExporter()
