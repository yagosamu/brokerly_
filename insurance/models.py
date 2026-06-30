from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from base.models import TenantAwareModel


class Proposal(TenantAwareModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Rascunho')
        SENT = 'sent', _('Enviada')
        UNDER_ANALYSIS = 'under_analysis', _('Em análise')
        APPROVED = 'approved', _('Aprovada')
        REJECTED = 'rejected', _('Recusada')
        CONVERTED = 'converted', _('Convertida em apólice')

    class AISummaryStatus(models.TextChoices):
        IDLE = 'idle', _('Pendente')
        PROCESSING = 'processing', _('Processando')
        DONE = 'done', _('Concluído')
        ERROR = 'error', _('Erro')

    number = models.CharField(max_length=40)
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.PROTECT,
        related_name='proposals',
    )
    insurer = models.ForeignKey(
        'insurers.Insurer',
        on_delete=models.PROTECT,
        related_name='proposals',
    )
    line_of_business = models.ForeignKey(
        'insurers.LineOfBusiness',
        on_delete=models.PROTECT,
        related_name='proposals',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    net_premium = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    total_premium = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    iof = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    proposed_start_date = models.DateField(null=True, blank=True)
    proposed_end_date = models.DateField(null=True, blank=True)
    payment_terms = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    ai_summary = models.TextField(blank=True)
    ai_summary_status = models.CharField(
        max_length=12,
        choices=AISummaryStatus.choices,
        default=AISummaryStatus.IDLE,
    )
    ai_summary_updated_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposals_created',
    )

    class Meta:
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'number'],
                name='proposal_unique_number_per_brokerage',
            ),
        ]
        indexes = [
            models.Index(fields=['brokerage', 'status']),
            models.Index(fields=['brokerage', '-created_at']),
        ]

    def __str__(self):
        return f'Proposta {self.number}'


class Policy(TenantAwareModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Ativa')
        CANCELED = 'canceled', _('Cancelada')
        EXPIRED = 'expired', _('Expirada')
        RENEWED = 'renewed', _('Renovada')

    class AISummaryStatus(models.TextChoices):
        IDLE = 'idle', _('Pendente')
        PROCESSING = 'processing', _('Processando')
        DONE = 'done', _('Concluído')
        ERROR = 'error', _('Erro')

    policy_number = models.CharField(max_length=40)
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_policies',
    )
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.PROTECT,
        related_name='policies',
    )
    insurer = models.ForeignKey(
        'insurers.Insurer',
        on_delete=models.PROTECT,
        related_name='policies',
    )
    line_of_business = models.ForeignKey(
        'insurers.LineOfBusiness',
        on_delete=models.PROTECT,
        related_name='policies',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    net_premium = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_premium = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    iof = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    commission_rate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0,
        help_text='Percentual da comissão paga pela seguradora à corretora.',
    )

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    payment_info = models.CharField(max_length=255, blank=True)

    ai_summary = models.TextField(blank=True)
    ai_summary_status = models.CharField(
        max_length=12,
        choices=AISummaryStatus.choices,
        default=AISummaryStatus.IDLE,
    )
    ai_summary_updated_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='policies_created',
    )

    class Meta:
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['brokerage', 'policy_number'],
                name='policy_unique_number_per_brokerage',
            ),
        ]
        indexes = [
            models.Index(fields=['brokerage', 'status']),
            models.Index(fields=['brokerage', '-created_at']),
        ]

    def __str__(self):
        return f'Apólice {self.policy_number}'


class CoveredItem(TenantAwareModel):
    class ItemType(models.TextChoices):
        AUTO = 'auto', _('Automóvel')
        PROPERTY = 'property', _('Imóvel')
        FLEET = 'fleet', _('Frota')
        TRAVEL = 'travel', _('Viagem')
        LIFE = 'life', _('Vida')
        EQUIPMENT = 'equipment', _('Equipamento')
        OTHER = 'other', _('Outro')

    ATTRIBUTE_SCHEMAS = {
        'auto': [
            {'key': 'marca', 'label': 'Marca', 'type': 'text'},
            {'key': 'modelo', 'label': 'Modelo', 'type': 'text'},
            {'key': 'ano', 'label': 'Ano', 'type': 'number'},
            {'key': 'placa', 'label': 'Placa', 'type': 'text'},
            {'key': 'chassi', 'label': 'Chassi', 'type': 'text'},
            {
                'key': 'combustivel',
                'label': 'Combustível',
                'type': 'select',
                'choices': [
                    'Gasolina',
                    'Etanol',
                    'Flex',
                    'Diesel',
                    'Elétrico',
                    'Híbrido',
                ],
            },
        ],
        'property': [
            {
                'key': 'tipo_imovel',
                'label': 'Tipo',
                'type': 'select',
                'choices': [
                    'Casa',
                    'Apartamento',
                    'Comercial',
                    'Condomínio',
                ],
            },
            {
                'key': 'endereco_completo',
                'label': 'Endereço completo',
                'type': 'text',
            },
            {'key': 'area_m2', 'label': 'Área (m²)', 'type': 'number'},
            {
                'key': 'ano_construcao',
                'label': 'Ano de construção',
                'type': 'number',
            },
        ],
        'fleet': [
            {
                'key': 'quantidade_veiculos',
                'label': 'Qtd veículos',
                'type': 'number',
            },
            {
                'key': 'descricao_frota',
                'label': 'Descrição da frota',
                'type': 'text',
            },
        ],
        'travel': [
            {'key': 'destino', 'label': 'Destino', 'type': 'text'},
            {'key': 'data_ida', 'label': 'Data de ida', 'type': 'date'},
            {'key': 'data_volta', 'label': 'Data de volta', 'type': 'date'},
            {
                'key': 'qtd_viajantes',
                'label': 'Quantidade de viajantes',
                'type': 'number',
            },
        ],
        'life': [
            {
                'key': 'nome_segurado',
                'label': 'Nome do segurado',
                'type': 'text',
            },
            {'key': 'cpf', 'label': 'CPF', 'type': 'text'},
            {
                'key': 'data_nascimento',
                'label': 'Data de nascimento',
                'type': 'date',
            },
            {'key': 'profissao', 'label': 'Profissão', 'type': 'text'},
        ],
        'equipment': [
            {'key': 'fabricante', 'label': 'Fabricante', 'type': 'text'},
            {'key': 'modelo', 'label': 'Modelo', 'type': 'text'},
            {
                'key': 'numero_serie',
                'label': 'Número de série',
                'type': 'text',
            },
            {
                'key': 'ano_fabricacao',
                'label': 'Ano de fabricação',
                'type': 'number',
            },
        ],
        'other': [],
    }

    COVERAGE_PRESETS = {
        'auto': [
            'Casco',
            'Roubo e furto',
            'Colisão',
            'Incêndio',
            'Danos a terceiros (RCF)',
            'APP (Acidentes Pessoais)',
            'Vidros',
        ],
        'property': [
            'Incêndio',
            'Roubo',
            'Vendaval',
            'Alagamento',
            'Danos elétricos',
            'Responsabilidade Civil',
        ],
        'fleet': [
            'Casco da frota',
            'Roubo / Furto',
            'RCF Frota',
            'APP coletivo',
        ],
        'travel': [
            'Despesas médicas',
            'Bagagem extraviada',
            'Cancelamento de viagem',
            'Repatriação',
        ],
        'life': [
            'Morte natural',
            'Morte acidental',
            'Invalidez permanente',
            'Doenças graves',
            'Diária por internação',
        ],
        'equipment': [
            'Roubo',
            'Danos acidentais',
            'Quebra eletrônica',
            'Incêndio',
        ],
        'other': [],
    }

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='covered_items',
    )
    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='covered_items',
    )

    item_type = models.CharField(
        max_length=12,
        choices=ItemType.choices,
        default=ItemType.OTHER,
    )
    description = models.CharField(max_length=255)
    identifier = models.CharField(
        max_length=120,
        blank=True,
        help_text='Placa, endereço, CPF/CNPJ etc.',
    )
    insured_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    attributes = models.JSONField(default=dict, blank=True)
    coverages = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ('id',)
        constraints = [
            models.CheckConstraint(
                name='covered_item_exactly_one_parent',
                condition=(
                    Q(proposal__isnull=False, policy__isnull=True)
                    | Q(proposal__isnull=True, policy__isnull=False)
                ),
            ),
        ]

    def __str__(self):
        return self.description

    def get_attribute_schema(self):
        return self.ATTRIBUTE_SCHEMAS.get(self.item_type, [])

    def get_coverage_presets(self):
        return self.COVERAGE_PRESETS.get(self.item_type, [])
