from django.db.models.signals import post_save
from django.dispatch import receiver

from tenants.models import Brokerage


DEFAULT_LOBS = [
    ('Automóvel', '0531', 'auto'),
    ('Frota', '0553', 'auto'),
    ('Residencial', '0114', 'property'),
    ('Patrimonial', '0118', 'property'),
    ('Empresarial', '0167', 'business'),
    ('Responsabilidade Civil', '0313', 'business'),
    ('Transporte', '0621', 'business'),
    ('Garantia', '0775', 'business'),
    ('Vida Individual', '0980', 'life'),
    ('Vida em Grupo', '0993', 'life'),
    ('Saúde', '0746', 'health'),
    ('Viagem', '0746', 'travel'),
    ('Equipamentos Eletrônicos', '0746', 'other'),
]


@receiver(post_save, sender=Brokerage)
def seed_default_lobs(sender, instance, created, **kwargs):
    """Seed default lines of business when a brokerage is first created."""

    if not created:
        return
    from insurers.models import LineOfBusiness

    LineOfBusiness.objects.bulk_create(
        [
            LineOfBusiness(
                brokerage=instance,
                name=name,
                code=code,
                category=category,
                is_active=True,
            )
            for name, code, category in DEFAULT_LOBS
        ],
        ignore_conflicts=True,
    )
