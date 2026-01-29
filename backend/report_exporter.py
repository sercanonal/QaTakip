"""
Report Export Utilities
Generate professional reports in Word, Excel, and PDF formats
"""

import io
import logging
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)

class ReportExporter:
    """Generate reports in multiple formats"""
    
    @staticmethod
    def generate_pdf_report(data: Dict[str, Any]) -> bytes:
        """Generate PDF report with professional formatting"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        story.append(Paragraph("QA Task Manager - Rapor", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Report date
        date_style = styles['Normal']
        story.append(Paragraph(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Statistics Summary
        stats = data.get('stats', {})
        if stats:
            story.append(Paragraph("📊 Genel İstatistikler", styles['Heading2']))
            stats_data = [
                ["Toplam Görev", str(stats.get('total_tasks', 0))],
                ["Tamamlanan", str(stats.get('completed_tasks', 0))],
                ["Devam Eden", str(stats.get('in_progress_tasks', 0))],
                ["Bekleyen", str(stats.get('todo_tasks', 0))],
                ["Gecikmiş", str(stats.get('overdue_tasks', 0))],
                ["Tamamlanma Oranı", f"%{stats.get('completion_rate', 0)}"],
            ]
            
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 0.4*inch))
        
        # Tasks List
        tasks = data.get('tasks', [])
        if tasks:
            story.append(Paragraph("📝 Görevler Listesi", styles['Heading2']))
            story.append(Spacer(1, 0.2*inch))
            
            task_data = [["Başlık", "Durum", "Öncelik", "Kategori"]]
            for task in tasks[:20]:  # Limit to 20 for PDF
                task_data.append([
                    task.get('title', '')[:40],
                    task.get('status', ''),
                    task.get('priority', ''),
                    task.get('category_id', '')[:20],
                ])
            
            task_table = Table(task_data, colWidths=[3*inch, 1.2*inch, 1*inch, 1.3*inch])
            task_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            story.append(task_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def generate_excel_report(data: Dict[str, Any]) -> bytes:
        """Generate Excel report with formatting"""
        wb = Workbook()
        
        # Summary Sheet
        ws_summary = wb.active
        ws_summary.title = "Özet"
        
        # Header styling
        header_fill = PatternFill(start_color="1a237e", end_color="1a237e", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=14)
        
        # Title
        ws_summary['A1'] = "QA Task Manager - Rapor"
        ws_summary['A1'].font = Font(size=18, bold=True, color="1a237e")
        ws_summary['A2'] = f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        # Statistics
        stats = data.get('stats', {})
        if stats:
            ws_summary['A4'] = "İstatistikler"
            ws_summary['A4'].font = header_font
            ws_summary['A4'].fill = header_fill
            
            row = 5
            for key, value in [
                ("Toplam Görev", stats.get('total_tasks', 0)),
                ("Tamamlanan", stats.get('completed_tasks', 0)),
                ("Devam Eden", stats.get('in_progress_tasks', 0)),
                ("Bekleyen", stats.get('todo_tasks', 0)),
                ("Gecikmiş", stats.get('overdue_tasks', 0)),
                ("Tamamlanma Oranı", f"%{stats.get('completion_rate', 0)}"),
            ]:
                ws_summary[f'A{row}'] = key
                ws_summary[f'B{row}'] = value
                ws_summary[f'A{row}'].font = Font(bold=True)
                row += 1
        
        # Tasks Sheet
        tasks = data.get('tasks', [])
        if tasks:
            ws_tasks = wb.create_sheet("Görevler")
            
            # Headers
            headers = ["ID", "Başlık", "Açıklama", "Durum", "Öncelik", "Kategori", "Oluşturulma", "Tamamlanma"]
            for col_num, header in enumerate(headers, 1):
                cell = ws_tasks.cell(row=1, column=col_num)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
            
            # Data
            for row_num, task in enumerate(tasks, 2):
                ws_tasks.cell(row=row_num, column=1, value=task.get('id', ''))
                ws_tasks.cell(row=row_num, column=2, value=task.get('title', ''))
                ws_tasks.cell(row=row_num, column=3, value=task.get('description', ''))
                ws_tasks.cell(row=row_num, column=4, value=task.get('status', ''))
                ws_tasks.cell(row=row_num, column=5, value=task.get('priority', ''))
                ws_tasks.cell(row=row_num, column=6, value=task.get('category_id', ''))
                ws_tasks.cell(row=row_num, column=7, value=task.get('created_at', ''))
                ws_tasks.cell(row=row_num, column=8, value=task.get('completed_at', '') or 'Devam ediyor')
            
            # Auto-adjust column widths
            for column in ws_tasks.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)
                for cell in column:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                adjusted_width = min(max_length + 2, 50)
                ws_tasks.column_dimensions[column_letter].width = adjusted_width
        
        # Save to buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def generate_word_report(data: Dict[str, Any]) -> bytes:
        """Generate Word document report"""
        doc = Document()
        
        # Title
        title = doc.add_heading('QA Task Manager - Rapor', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Date
        date_para = doc.add_paragraph(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()  # Spacer
        
        # Statistics
        stats = data.get('stats', {})
        if stats:
            doc.add_heading('Genel İstatistikler', level=1)
            
            table = doc.add_table(rows=7, cols=2)
            table.style = 'Light Grid Accent 1'
            
            stats_data = [
                ("İstatistik", "Değer"),
                ("Toplam Görev", str(stats.get('total_tasks', 0))),
                ("Tamamlanan", str(stats.get('completed_tasks', 0))),
                ("Devam Eden", str(stats.get('in_progress_tasks', 0))),
                ("Bekleyen", str(stats.get('todo_tasks', 0))),
                ("Gecikmiş", str(stats.get('overdue_tasks', 0))),
                ("Tamamlanma Oranı", f"%{stats.get('completion_rate', 0)}"),
            ]
            
            for row_idx, (key, value) in enumerate(stats_data):
                table.rows[row_idx].cells[0].text = key
                table.rows[row_idx].cells[1].text = value
                if row_idx == 0:
                    for cell in table.rows[row_idx].cells:
                        cell.paragraphs[0].runs[0].font.bold = True
            
            doc.add_paragraph()
        
        # Tasks
        tasks = data.get('tasks', [])
        if tasks:
            doc.add_heading('Görevler Listesi', level=1)
            
            for task in tasks[:30]:  # Limit to 30 for Word
                doc.add_heading(f"{task.get('title', 'Başlıksız')}", level=2)
                doc.add_paragraph(f"Durum: {task.get('status', '')}")
                doc.add_paragraph(f"Öncelik: {task.get('priority', '')}")
                doc.add_paragraph(f"Kategori: {task.get('category_id', '')}")
                if task.get('description'):
                    doc.add_paragraph(f"Açıklama: {task.get('description', '')}")
                doc.add_paragraph()
        
        # Save to buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()


# Global exporter instance
report_exporter = ReportExporter()
