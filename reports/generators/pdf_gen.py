from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from reports.generators.common import date_br, filename, report_table


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(190 * mm, 12 * mm, f'Página {doc.page}')
    canvas.restoreState()


def _build_pdf(report_type, brokerage, params, user=None):
    metadata, headers, rows = report_table(report_type, brokerage, params)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(metadata['title'], styles['Title']),
        Paragraph(f'Corretora: {metadata["brokerage_name"]}', styles['Normal']),
        Paragraph(f'CNPJ: {metadata["brokerage_cnpj"]}', styles['Normal']),
        Paragraph(
            f'Gerado em: {metadata["generated_at"]:%d/%m/%Y %H:%M}',
            styles['Normal'],
        ),
    ]
    if user:
        elements.append(Paragraph(f'Solicitado por: {user}', styles['Normal']))
    if metadata['params']:
        filter_text = '; '.join(
            f'{key}: {value}'
            for key, value in metadata['params'].items()
        )
        elements.append(Paragraph(f'Filtros: {filter_text}', styles['Normal']))
    elements.append(Spacer(1, 8 * mm))

    table_rows = [headers] + [[_cell(value) for value in row] for row in rows]
    if len(table_rows) == 1:
        table_rows.append(['Sem dados'] + [''] * (len(headers) - 1))
    table = Table(table_rows, repeatRows=1)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#dee2e6')),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ])
    for index in range(1, len(table_rows)):
        if index % 2 == 0:
            style.add('BACKGROUND', (0, index), (-1, index), colors.HexColor('#f8f9fa'))
    table.setStyle(style)
    elements.append(table)
    doc.build(elements, onFirstPage=_footer, onLaterPages=_footer)
    return filename(report_type, 'pdf'), buffer.getvalue()


def _cell(value):
    if hasattr(value, 'strftime'):
        return date_br(value)
    return '' if value is None else str(value)


def build_carteira_pdf(brokerage, params, user=None):
    return _build_pdf('carteira', brokerage, params, user=user)


def build_propostas_pdf(brokerage, params, user=None):
    return _build_pdf('propostas', brokerage, params, user=user)


def build_apolices_pdf(brokerage, params, user=None):
    return _build_pdf('apolices', brokerage, params, user=user)


def build_sinistros_pdf(brokerage, params, user=None):
    return _build_pdf('sinistros', brokerage, params, user=user)


def build_renovacoes_pdf(brokerage, params, user=None):
    return _build_pdf('renovacoes', brokerage, params, user=user)


def build_comissoes_pdf(brokerage, params, user=None):
    return _build_pdf('comissoes', brokerage, params, user=user)


def build_seguradoras_pdf(brokerage, params, user=None):
    return _build_pdf('seguradoras', brokerage, params, user=user)


def build_produtividade_pdf(brokerage, params, user=None):
    return _build_pdf('produtividade', brokerage, params, user=user)
