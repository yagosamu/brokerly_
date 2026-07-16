import csv
from io import StringIO

from reports.generators.common import filename, report_table


def _build_csv(report_type, brokerage, params):
    metadata, headers, rows = report_table(report_type, brokerage, params)
    buffer = StringIO()
    buffer.write('\ufeff')
    writer = csv.writer(buffer, delimiter=';', lineterminator='\n')
    writer.writerow([metadata['title']])
    writer.writerow(['Corretora', metadata['brokerage_name']])
    writer.writerow(['CNPJ', metadata['brokerage_cnpj']])
    writer.writerow([])
    writer.writerow(headers)
    writer.writerows(rows)
    return filename(report_type, 'csv'), buffer.getvalue().encode('utf-8')


def build_carteira_csv(brokerage, params):
    return _build_csv('carteira', brokerage, params)


def build_propostas_csv(brokerage, params):
    return _build_csv('propostas', brokerage, params)


def build_apolices_csv(brokerage, params):
    return _build_csv('apolices', brokerage, params)


def build_sinistros_csv(brokerage, params):
    return _build_csv('sinistros', brokerage, params)


def build_renovacoes_csv(brokerage, params):
    return _build_csv('renovacoes', brokerage, params)


def build_comissoes_csv(brokerage, params):
    return _build_csv('comissoes', brokerage, params)


def build_seguradoras_csv(brokerage, params):
    return _build_csv('seguradoras', brokerage, params)


def build_produtividade_csv(brokerage, params):
    return _build_csv('produtividade', brokerage, params)
