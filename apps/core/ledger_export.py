from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _ledger_rows(entries, total_in, total_out, net_balance, current_balance, title):
    rows = [['التاريخ', 'المرجع', 'البيان', 'وارد', 'صادر']]
    for e in entries:
        rows.append([
            str(e['date']),
            e['ref'] or '',
            e['desc'] or '',
            str(e['in']) if e['in'] else '',
            str(e['out']) if e['out'] else '',
        ])
    rows.append(['', '', 'إجمالي الفترة', str(total_in), str(total_out)])
    rows.append(['', '', 'صافي الفترة', str(net_balance), ''])
    rows.append(['', '', 'الرصيد الحالي', str(current_balance), ''])
    return rows


def export_ledger_excel(entries, total_in, total_out, net_balance, current_balance, title, filename):
    wb = Workbook()
    ws = wb.active
    ws.title = 'كشف حساب'
    ws.append([title])
    ws.append([])
    for row in _ledger_rows(entries, total_in, total_out, net_balance, current_balance, title)[1:]:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    response = HttpResponse(
        buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_ledger_pdf(entries, total_in, total_out, net_balance, current_balance, title, filename):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=24, leftMargin=24)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles['Title']), Spacer(1, 12)]
    data = _ledger_rows(entries, total_in, total_out, net_balance, current_balance, title)
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3d6a99')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor('#f1f5f9')),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(table)
    doc.build(story)
    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
