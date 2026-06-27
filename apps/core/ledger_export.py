from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_ARABIC_FONT = None


def _reshape_arabic(text):
    if not text:
        return ''
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)


def _arabic_font_name():
    global _ARABIC_FONT
    if _ARABIC_FONT:
        return _ARABIC_FONT

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = [
        Path(settings.BASE_DIR) / 'static' / 'fonts' / 'Amiri-Regular.ttf',
        Path('/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf'),
        Path('/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'),
        Path('/usr/share/fonts/opentype/noto/NotoSansArabic-Regular.ttf'),
        Path('C:/Windows/Fonts/arial.ttf'),
        Path('C:/Windows/Fonts/tahoma.ttf'),
    ]
    for path in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont('AppArabic', str(path)))
            _ARABIC_FONT = 'AppArabic'
            return _ARABIC_FONT

    _ARABIC_FONT = 'Helvetica'
    return _ARABIC_FONT


def _pdf_cell(text, style):
    return Paragraph(_reshape_arabic(text).replace('\n', '<br/>'), style)


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
    font = _arabic_font_name()
    cell_style = ParagraphStyle(
        name='LedgerCell',
        fontName=font,
        fontSize=9,
        alignment=TA_CENTER,
        leading=12,
    )
    title_style = ParagraphStyle(
        name='LedgerTitle',
        fontName=font,
        fontSize=14,
        alignment=TA_CENTER,
        leading=18,
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=24, leftMargin=24)
    story = [_pdf_cell(title, title_style), Spacer(1, 12)]

    raw = _ledger_rows(entries, total_in, total_out, net_balance, current_balance, title)
    data = [[_pdf_cell(cell, cell_style) for cell in row] for row in raw]

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3d6a99')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor('#f1f5f9')),
    ]))
    story.append(table)
    doc.build(story)
    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
