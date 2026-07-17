import random
import time
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from faker import Faker

from ai_agents.models import ChatMessage, ChatSession
from claims.models import Claim
from clients.models import Client
from commissions.models import Commission, CommissionSplit
from crm.models import Deal, DealStageHistory, Pipeline, Stage
from documents.models import Document
from insurance.models import CoveredItem, Endorsement, Policy, Proposal
from insurers.models import Insurer, LineOfBusiness
from notifications.models import Notification
from partners.models import Agent, EntityType, Producer
from renewals.models import Renewal
from reports.models import ReportJob
from tenants.models import Brokerage, Plan, Subscription


PASSWORD = 'Brokerly@2026'
LOB_NAMES = (
    ('Automóvel', '0531', LineOfBusiness.Category.AUTO),
    ('Vida', '0993', LineOfBusiness.Category.LIFE),
    ('Saúde', '0746', LineOfBusiness.Category.HEALTH),
    ('Residencial', '0114', LineOfBusiness.Category.PROPERTY),
    ('Empresarial', '0167', LineOfBusiness.Category.BUSINESS),
    ('Frota', '0553', LineOfBusiness.Category.AUTO),
    ('Náutico', '0622', LineOfBusiness.Category.OTHER),
    ('Rural', '1101', LineOfBusiness.Category.OTHER),
)
STAGE_DEFINITIONS = (
    ('Novo lead', '#6b7885', False, False),
    ('Em contato', '#3454d1', False, False),
    ('Cotação', '#ffa21d', False, False),
    ('Proposta enviada', '#3dc7be', False, False),
    ('Ganho', '#17c666', True, False),
    ('Perdido', '#ea4d4d', False, True),
)


class Command(BaseCommand):
    help = 'Seed a deterministic multi-tenant demo database.'

    def add_arguments(self, parser):
        parser.add_argument('--brokerages', type=int, default=3)
        parser.add_argument('--flush', action='store_true')
        parser.add_argument('--seed', type=int, default=42)
        parser.add_argument('--with-files', action='store_true')
        parser.add_argument('--force', action='store_true')

    def handle(self, *args, **options):
        if not settings.DEBUG and not options['force']:
            raise CommandError(
                'DEBUG=False detectado. Passe --force explicitamente para '
                'semear em ambiente não-dev.'
            )
        if options['brokerages'] < 1:
            raise CommandError('--brokerages deve ser maior que zero.')

        started = time.perf_counter()
        random.seed(options['seed'])
        Faker.seed(options['seed'])
        self.fake = Faker('pt_BR')
        self.stats = {
            'brokerages': 0,
            'users': 0,
            'clients': 0,
            'proposals': 0,
            'policies': 0,
            'premium': Decimal('0'),
            'claims': 0,
            'renewals': 0,
            'deals': 0,
            'notifications': 0,
            'chat_sessions': 0,
            'chat_messages': 0,
            'documents': 0,
        }

        with transaction.atomic():
            if options['flush']:
                self._flush_domain()
            plan = self._free_plan()
            for index in range(1, options['brokerages'] + 1):
                self.stdout.write('.', ending='')
                self.stdout.flush()
                self._seed_brokerage(index, plan, options['with_files'])

        elapsed = time.perf_counter() - started
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ Semeado ambiente demo'))
        self.stdout.write(f'  - {self.stats["brokerages"]} corretoras')
        self.stdout.write(f'  - {self.stats["users"]} usuários')
        self.stdout.write(f'  - {self.stats["clients"]} clientes')
        self.stdout.write(
            f'  - {self.stats["policies"]} apólices, '
            f'R$ {self.stats["premium"]:.2f} em prêmio'
        )
        self.stdout.write(f'  - {self.stats["claims"]} sinistros')
        self.stdout.write(f'  - {self.stats["renewals"]} renovações')
        self.stdout.write(f'  - {self.stats["deals"]} deals CRM')
        self.stdout.write(f'  - {self.stats["notifications"]} notificações')
        self.stdout.write(
            f'  - {self.stats["chat_sessions"]} sessões de chat, '
            f'{self.stats["chat_messages"]} mensagens'
        )
        self.stdout.write(f'  Semente: {options["seed"]}')
        self.stdout.write(f'  Tempo: {elapsed:.2f}s')

    def _flush_domain(self):
        Document.objects.all().delete()
        ReportJob.objects.all().delete()
        ChatMessage.objects.all().delete()
        ChatSession.objects.all().delete()
        Notification.objects.all().delete()
        DealStageHistory.objects.all().delete()
        Deal.objects.all().delete()
        Stage.objects.all().delete()
        Pipeline.objects.all().delete()
        Renewal.objects.all().delete()
        CommissionSplit.objects.all().delete()
        Commission.objects.all().delete()
        Claim.objects.all().delete()
        CoveredItem.objects.all().delete()
        Endorsement.objects.all().delete()
        Policy.objects.all().delete()
        Proposal.objects.all().delete()
        Producer.objects.all().delete()
        Agent.objects.all().delete()
        Insurer.objects.all().delete()
        LineOfBusiness.objects.all().delete()
        Client.objects.all().delete()
        Subscription.objects.all().delete()
        Brokerage.objects.all().delete()
        get_user_model().objects.filter(is_superuser=False).delete()

    def _free_plan(self):
        plan, _ = Plan.objects.get_or_create(
            slug='free',
            defaults={
                'name': 'Free',
                'price': Decimal('0'),
                'max_users': 100,
                'max_clients': 1000,
                'max_policies': 2000,
                'features': ['Demo completa', 'CRM', 'Relatórios', 'IA fake'],
                'is_available': True,
            },
        )
        return plan

    def _seed_brokerage(self, index, plan, with_files):
        users = self._create_users(index)
        owner = users['owners'][0]
        brokerage = Brokerage.objects.create(
            legal_name=f'Corretora {self.fake.last_name()} Ltda',
            trade_name=f'Corretora {self.fake.last_name()}',
            cnpj=self._cnpj(index),
            susep_code=f'SUSEP-{index:04d}',
            email=f'contato@corretora-{index}.local',
            phone=self.fake.phone_number()[:20],
            address_line=self.fake.street_name(),
            address_number=str(random.randint(10, 9999)),
            address_complement='Sala demo',
            district=self.fake.bairro(),
            city=self.fake.city(),
            state=self.fake.estado_sigla(),
            zip_code=self.fake.postcode()[:10],
            owner=owner,
            plan=plan,
        )
        Subscription.objects.create(brokerage=brokerage, plan=plan)
        for user in users['all']:
            user.brokerage = brokerage
            user.save(update_fields=['brokerage', 'updated_at'])

        lobs = self._create_lines_of_business(brokerage)
        insurers = self._create_insurers(brokerage, index)
        agents, producers = self._create_partners(brokerage, users)
        clients = self._create_clients(brokerage, index)
        proposals = self._create_proposals(brokerage, clients, insurers, lobs, users)
        policies = self._create_policies(
            brokerage,
            clients,
            insurers,
            lobs,
            proposals,
            users,
        )
        self._create_commission_splits(brokerage, policies, agents, producers)
        claims = self._create_claims(brokerage, policies, users)
        self._create_endorsements(brokerage, policies, users)
        self._create_renewals(brokerage, policies, users)
        deals = self._create_crm(brokerage, clients, insurers, lobs, producers, proposals, users)
        self._create_notifications(brokerage, users, policies, claims, deals)
        self._create_chat(brokerage, owner)
        self._apply_ai_summaries(clients, proposals, policies, claims, deals)
        if with_files:
            self._create_documents(brokerage, policies, claims, owner)
        self._spread_timestamps(brokerage)

        self.stats['brokerages'] += 1

    def _create_users(self, index):
        user_model = get_user_model()
        roles = (
            ('owners', UserRole('owner', 'owner', 1)),
            ('managers', UserRole('manager', 'manager', 1)),
            ('brokers', UserRole('broker', 'broker', 2)),
            ('agents', UserRole('agent', 'agent', 3)),
            ('producers', UserRole('producer', 'producer', 4)),
            ('operationals', UserRole('operational', 'operational', 1)),
        )
        result = {'all': []}
        for key, role_group in roles:
            result[key] = []
            for number in range(1, role_group.count + 1):
                prefix = role_group.email_prefix
                email_prefix = prefix if role_group.count == 1 else f'{prefix}{number}'
                email = f'{email_prefix}@corretora-{index}.local'
                user = user_model.objects.create_user(
                    email=email,
                    password=PASSWORD,
                    first_name=self.fake.first_name(),
                    last_name=self.fake.last_name(),
                    role=role_group.role,
                )
                result[key].append(user)
                result['all'].append(user)
        self.stats['users'] += len(result['all'])
        return result

    def _create_lines_of_business(self, brokerage):
        LineOfBusiness.objects.filter(brokerage=brokerage).delete()
        lobs = [
            LineOfBusiness(
                brokerage=brokerage,
                name=name,
                code=code,
                category=category,
            )
            for name, code, category in LOB_NAMES
        ]
        return LineOfBusiness.objects.bulk_create(lobs)

    def _create_insurers(self, brokerage, index):
        insurers = []
        for number in range(1, 7):
            insurers.append(
                Insurer(
                    brokerage=brokerage,
                    name=f'{self.fake.company()} Seguros {index}-{number}',
                    cnpj=self._cnpj(index * 100 + number),
                    susep_code=f'SEG-{index:02d}{number:02d}',
                    email=f'seguradora{number}@corretora-{index}.local',
                    phone=self.fake.phone_number()[:20],
                )
            )
        return Insurer.objects.bulk_create(insurers)

    def _create_partners(self, brokerage, users):
        agents = []
        for number in range(6):
            entity_type = self._cycle(EntityType.values, number)
            agents.append(
                Agent(
                    brokerage=brokerage,
                    entity_type=entity_type,
                    name=self._person_or_company_name(entity_type),
                    document=self._document(entity_type, number + 10),
                    email=f'agente{number + 1}@{brokerage.id}.demo.local',
                    phone=self.fake.phone_number()[:20],
                    susep_code=f'AG-{brokerage.id:03d}-{number + 1:02d}',
                    user=users['agents'][number % len(users['agents'])],
                    default_commission_rate=self._money_rate('0.05', '0.18'),
                )
            )
        agents = Agent.objects.bulk_create(agents)
        producers = []
        for number in range(12):
            entity_type = self._cycle(EntityType.values, number + 1)
            producers.append(
                Producer(
                    brokerage=brokerage,
                    agent=agents[number % len(agents)] if number % 2 == 0 else None,
                    entity_type=entity_type,
                    name=self._person_or_company_name(entity_type),
                    document=self._document(entity_type, number + 50),
                    email=f'produtor{number + 1}@{brokerage.id}.demo.local',
                    phone=self.fake.phone_number()[:20],
                    user=users['producers'][number % len(users['producers'])],
                    default_commission_rate=self._money_rate('0.04', '0.16'),
                )
            )
        producers = Producer.objects.bulk_create(producers)
        return agents, producers

    def _create_clients(self, brokerage, index):
        clients = []
        total = 35
        for number in range(total):
            person_type = (
                Client.PersonType.NATURAL
                if number < int(total * 0.6) else Client.PersonType.LEGAL
            )
            created_at = self._past_datetime(days=365)
            clients.append(
                Client(
                    brokerage=brokerage,
                    person_type=person_type,
                    name=(
                        self.fake.name()
                        if person_type == Client.PersonType.NATURAL
                        else self.fake.company()
                    ),
                    trade_name=(
                        ''
                        if person_type == Client.PersonType.NATURAL
                        else self.fake.company()
                    ),
                    document=self._client_document(person_type, index, number),
                    email=f'cliente{number + 1}@corretora-{index}.local',
                    phone=self.fake.phone_number()[:20],
                    birth_date=self.fake.date_of_birth(minimum_age=18, maximum_age=75),
                    address_line=self.fake.street_name(),
                    address_number=str(random.randint(1, 9999)),
                    district=self.fake.bairro(),
                    city=self.fake.city(),
                    state=self.fake.estado_sigla(),
                    zip_code=self.fake.postcode()[:10],
                    notes='Cliente criado pelo seed demo.',
                    is_active=random.random() > 0.08,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )
        clients = Client.objects.bulk_create(clients)
        self.stats['clients'] += len(clients)
        return clients

    def _create_proposals(self, brokerage, clients, insurers, lobs, users):
        proposals = []
        selected_clients = clients[:15]
        statuses = list(Proposal.Status.values)
        for client_index, client in enumerate(selected_clients):
            for offset in range(1 + client_index % 3):
                premium = self._money('800', '15000')
                start_date = timezone.now().date() + timedelta(days=random.randint(-60, 90))
                proposals.append(
                    Proposal(
                        brokerage=brokerage,
                        number=f'PROP-{brokerage.id:03d}-{client_index:03d}-{offset}',
                        client=client,
                        insurer=random.choice(insurers),
                        line_of_business=random.choice(lobs),
                        status=self._cycle(statuses, len(proposals)),
                        net_premium=premium,
                        total_premium=(premium * Decimal('1.0738')).quantize(Decimal('0.01')),
                        iof=(premium * Decimal('0.0738')).quantize(Decimal('0.01')),
                        proposed_start_date=start_date,
                        proposed_end_date=start_date + timedelta(days=365),
                        payment_terms=f'{random.choice([1, 4, 6, 10, 12])} parcelas',
                        notes='Proposta fake para demonstração.',
                        created_by=random.choice(users['brokers']),
                    )
                )
        proposals = Proposal.objects.bulk_create(proposals)
        self.stats['proposals'] += len(proposals)
        self._create_covered_items_for_proposals(brokerage, proposals)
        return proposals

    def _create_covered_items_for_proposals(self, brokerage, proposals):
        items = []
        item_types = list(CoveredItem.ItemType.values)
        for proposal_index, proposal in enumerate(proposals):
            for offset in range(1 + proposal_index % 3):
                item_type = self._cycle(item_types, proposal_index + offset)
                items.append(self._covered_item(brokerage, item_type, proposal=proposal))
        CoveredItem.objects.bulk_create(items)

    def _create_policies(self, brokerage, clients, insurers, lobs, proposals, users):
        policies = []
        converted = [
            proposal for proposal in proposals
            if proposal.status in (Proposal.Status.APPROVED, Proposal.Status.CONVERTED)
        ][:18]
        for index, proposal in enumerate(converted):
            policy = self._create_policy(
                brokerage,
                index,
                proposal.client,
                proposal.insurer,
                proposal.line_of_business,
                users,
                proposal=proposal,
                status=Policy.Status.ACTIVE if index % 2 == 0 else Policy.Status.RENEWED,
            )
            self._clone_proposal_items_to_policy(brokerage, proposal, policy)
            policies.append(policy)

        statuses = (
            [Policy.Status.ACTIVE] * 42
            + [Policy.Status.EXPIRED] * 9
            + [Policy.Status.RENEWED] * 6
            + [Policy.Status.CANCELED] * 3
        )
        for index, status in enumerate(statuses):
            policy = self._create_policy(
                brokerage,
                index + 100,
                random.choice(clients),
                random.choice(insurers),
                random.choice(lobs),
                users,
                status=status,
            )
            self._create_covered_items_for_policy(brokerage, policy, index)
            policies.append(policy)
        return policies

    def _create_policy(
        self,
        brokerage,
        index,
        client,
        insurer,
        lob,
        users,
        status,
        proposal=None,
    ):
        premium = self._money('800', '15000')
        start_date, end_date = self._policy_dates(status, index)
        policy = Policy.objects.create(
            brokerage=brokerage,
            policy_number=f'POL-{brokerage.id:03d}-{index:05d}',
            proposal=proposal,
            client=client,
            insurer=insurer,
            line_of_business=lob,
            status=status,
            net_premium=premium,
            total_premium=(premium * Decimal('1.0738')).quantize(Decimal('0.01')),
            iof=(premium * Decimal('0.0738')).quantize(Decimal('0.01')),
            commission_rate=self._money_rate('0.05', '0.25'),
            start_date=start_date,
            end_date=end_date,
            payment_info=f'{random.choice([1, 4, 6, 10, 12])} parcelas',
            created_by=random.choice(users['brokers']),
        )
        self.stats['policies'] += 1
        self.stats['premium'] += policy.total_premium
        return policy

    def _clone_proposal_items_to_policy(self, brokerage, proposal, policy):
        items = [
            CoveredItem(
                brokerage=brokerage,
                policy=policy,
                item_type=item.item_type,
                description=item.description,
                identifier=item.identifier,
                insured_amount=item.insured_amount,
                attributes=item.attributes,
                coverages=item.coverages,
            )
            for item in proposal.covered_items.all()
        ]
        if items:
            CoveredItem.objects.bulk_create(items)

    def _create_covered_items_for_policy(self, brokerage, policy, index):
        item_types = list(CoveredItem.ItemType.values)
        items = [
            self._covered_item(
                brokerage,
                self._cycle(item_types, index + offset),
                policy=policy,
            )
            for offset in range(1 + index % 3)
        ]
        CoveredItem.objects.bulk_create(items)

    def _create_commission_splits(self, brokerage, policies, agents, producers):
        commissions = list(
            Commission.objects.filter(
                brokerage=brokerage,
                policy__in=policies,
            ).select_related('policy')
        )
        statuses = list(Commission.Status.values)
        for index, commission in enumerate(commissions):
            commission.status = self._cycle(statuses, index)
            if commission.status == Commission.Status.RECEIVED:
                commission.received_at = commission.reference_date + timedelta(days=15)
            if commission.status == Commission.Status.PAID:
                commission.received_at = commission.reference_date + timedelta(days=15)
                commission.paid_at = commission.reference_date + timedelta(days=30)
            commission.save(update_fields=['status', 'received_at', 'paid_at', 'updated_at'])

        pending = [
            commission for commission in commissions
            if commission.status == Commission.Status.PENDING
        ]
        splits = []
        for index, commission in enumerate(pending[: max(1, int(len(pending) * 0.3))]):
            beneficiaries = 1 + index % 2
            for offset in range(beneficiaries):
                if (index + offset) % 2 == 0:
                    rate = producers[(index + offset) % len(producers)].default_commission_rate
                    splits.append(
                        CommissionSplit(
                            brokerage=brokerage,
                            commission=commission,
                            beneficiary_type=CommissionSplit.BeneficiaryType.PRODUCER,
                            producer=producers[(index + offset) % len(producers)],
                            rate=rate,
                            amount=(commission.insurer_amount * rate).quantize(Decimal('0.01')),
                            status=self._cycle(CommissionSplit.Status.values, index + offset),
                        )
                    )
                else:
                    rate = agents[(index + offset) % len(agents)].default_commission_rate
                    splits.append(
                        CommissionSplit(
                            brokerage=brokerage,
                            commission=commission,
                            beneficiary_type=CommissionSplit.BeneficiaryType.AGENT,
                            agent=agents[(index + offset) % len(agents)],
                            rate=rate,
                            amount=(commission.insurer_amount * rate).quantize(Decimal('0.01')),
                            status=self._cycle(CommissionSplit.Status.values, index + offset),
                        )
                    )
        CommissionSplit.objects.bulk_create(splits)

    def _create_claims(self, brokerage, policies, users):
        active_policies = [
            policy for policy in policies
            if policy.status == Policy.Status.ACTIVE and policy.covered_items.exists()
        ]
        statuses = list(Claim.Status.values)
        claims = []
        for index, policy in enumerate(active_policies[:24]):
            for offset in range(1 + index % 2):
                occurrence = timezone.now().date() - timedelta(days=random.randint(1, 240))
                claimed = self._money('1000', '60000')
                status = self._cycle(statuses, len(claims))
                approved = (
                    claimed
                    if status in (Claim.Status.APPROVED, Claim.Status.PAID)
                    else Decimal('0')
                )
                claims.append(
                    Claim(
                        brokerage=brokerage,
                        claim_number=f'SIN-{brokerage.id:03d}-{len(claims):05d}',
                        policy=policy,
                        covered_item=policy.covered_items.first(),
                        occurrence_date=occurrence,
                        notice_date=occurrence + timedelta(days=random.randint(0, 12)),
                        status=status,
                        description='Sinistro fake para demonstração operacional.',
                        claimed_amount=claimed,
                        approved_amount=approved,
                        created_by=random.choice(users['brokers']),
                    )
                )
        claims = Claim.objects.bulk_create(claims)
        self.stats['claims'] += len(claims)
        return claims

    def _create_endorsements(self, brokerage, policies, users):
        endorsements = []
        types = list(Endorsement.Type.values)
        statuses = list(Endorsement.Status.values)
        for index, policy in enumerate(policies[: max(12, int(len(policies) * 0.15))]):
            for offset in range(1 + index % 2):
                endorsement_type = self._cycle(types, index + offset)
                premium_change = Decimal('0')
                if endorsement_type == Endorsement.Type.INCREASE:
                    premium_change = self._money('100', '1200')
                elif endorsement_type == Endorsement.Type.DECREASE:
                    premium_change = -self._money('100', '900')
                endorsements.append(
                    Endorsement(
                        brokerage=brokerage,
                        endorsement_number=f'END-{brokerage.id:03d}-{len(endorsements):05d}',
                        policy=policy,
                        type=endorsement_type,
                        status=self._cycle(statuses, len(endorsements)),
                        description='Endosso fake para demonstração.',
                        premium_change=premium_change,
                        effective_date=policy.start_date + timedelta(days=random.randint(20, 240)),
                        created_by=random.choice(users['brokers']),
                    )
                )
        Endorsement.objects.bulk_create(endorsements)

    def _create_renewals(self, brokerage, policies, users):
        candidates = [
            policy for policy in policies
            if policy.status in (Policy.Status.EXPIRED, Policy.Status.RENEWED)
            or (
                policy.status == Policy.Status.ACTIVE
                and policy.end_date
                and policy.end_date <= timezone.now().date() + timedelta(days=90)
            )
        ]
        statuses = list(Renewal.Status.values)
        renewals = []
        for index, policy in enumerate(candidates):
            renewals.append(
                Renewal(
                    brokerage=brokerage,
                    policy=policy,
                    status=self._cycle(statuses, index),
                    due_date=policy.end_date,
                    notes='Renovação criada pelo seed demo.',
                    created_by=random.choice(users['brokers']),
                )
            )
        renewals = Renewal.objects.bulk_create(renewals, ignore_conflicts=True)
        self.stats['renewals'] += len(renewals)

    def _create_crm(self, brokerage, clients, insurers, lobs, producers, proposals, users):
        pipeline = self._pipeline(brokerage)
        stages = list(pipeline.stages.order_by('order', 'id'))
        deals = []
        histories = []
        statuses = [Deal.Status.OPEN] * 15 + [Deal.Status.WON] * 6 + [Deal.Status.LOST] * 4
        for index, status in enumerate(statuses):
            stage = self._stage_for_status(stages, status, index)
            producer = random.choice(producers)
            deal = Deal.objects.create(
                brokerage=brokerage,
                pipeline=pipeline,
                stage=stage,
                client=random.choice(clients),
                producer=producer,
                agent=producer.agent,
                line_of_business=random.choice(lobs),
                insurer=random.choice(insurers),
                proposal=random.choice(proposals) if proposals and index % 3 == 0 else None,
                title=f'Oportunidade {index + 1} · {self.fake.catch_phrase()}',
                description='Negociação fake para visual do CRM.',
                estimated_value=self._money('800', '20000'),
                status=status,
                expected_close_date=(
                    timezone.now().date()
                    + timedelta(days=random.randint(-45, 120))
                ),
                created_by=random.choice(users['brokers']),
            )
            previous = None
            for step in stages[: stages.index(stage) + 1][-4:]:
                histories.append(
                    DealStageHistory(
                        brokerage=brokerage,
                        deal=deal,
                        from_stage=previous,
                        to_stage=step,
                        changed_by=random.choice(users['brokers']),
                        note='Movimentação simulada pelo seed.',
                    )
                )
                previous = step
            deals.append(deal)
        DealStageHistory.objects.bulk_create(histories)
        self.stats['deals'] += len(deals)
        return deals

    def _create_notifications(self, brokerage, users, policies, claims, deals):
        all_users = users['all']
        types = list(Notification.Type.values)
        notifications = []
        for index in range(24):
            is_read = index % 2 == 0
            notifications.append(
                Notification(
                    brokerage=brokerage,
                    user=random.choice(all_users),
                    type=self._cycle(types, index),
                    title=self._notification_title(index),
                    message='Notificação fake para exercitar polling e listagem.',
                    url=self._notification_url(index, policies, claims, deals),
                    is_read=is_read,
                    read_at=timezone.now() - timedelta(days=index) if is_read else None,
                )
            )
        Notification.objects.bulk_create(notifications)
        self.stats['notifications'] += len(notifications)

    def _create_chat(self, brokerage, owner):
        sessions = []
        messages = []
        for index in range(3):
            session = ChatSession.objects.create(
                brokerage=brokerage,
                user=owner,
                title=f'Análise da carteira {index + 1}',
                last_message_at=timezone.now() - timedelta(hours=index),
            )
            sessions.append(session)
            for message_index in range(6):
                role = (
                    ChatMessage.Role.USER
                    if message_index % 2 == 0 else ChatMessage.Role.ASSISTANT
                )
                messages.append(
                    ChatMessage(
                        session=session,
                        role=role,
                        content=self._chat_content(role, message_index),
                        token_count=random.randint(30, 180),
                    )
                )
        ChatMessage.objects.bulk_create(messages)
        self.stats['chat_sessions'] += len(sessions)
        self.stats['chat_messages'] += len(messages)

    def _apply_ai_summaries(self, *groups):
        now = timezone.now()
        for group in groups:
            for index, entity in enumerate(group):
                if index % 3 != 0:
                    continue
                entity.ai_summary = self._ai_summary(entity)
                entity.ai_summary_status = 'done'
                entity.ai_summary_updated_at = now
                entity.save(
                    update_fields=[
                        'ai_summary',
                        'ai_summary_status',
                        'ai_summary_updated_at',
                        'updated_at',
                    ]
                )

    def _create_documents(self, brokerage, policies, claims, user):
        policy_type = ContentType.objects.get_for_model(Policy)
        claim_type = ContentType.objects.get_for_model(Claim)
        pdf_bytes = (
            b'%PDF-1.4\n'
            b'1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
            b'2 0 obj<</Type/Pages/Count 0>>endobj\n'
            b'This is a test PDF placeholder for Brokerly seed demo.\n'
            b'%%EOF\n'
        )
        targets = [(policy_type, policy) for policy in policies[::8]]
        targets += [(claim_type, claim) for claim in claims[::5]]
        for index, (content_type, obj) in enumerate(targets):
            document = Document(
                brokerage=brokerage,
                content_type=content_type,
                object_id=obj.id,
                original_name=f'demo_{index}.pdf',
                mime_type='application/pdf',
                size_bytes=len(pdf_bytes),
                description='PDF placeholder do seed demo.',
                uploaded_by=user,
            )
            document.file.save(
                f'demo_{index}.pdf',
                ContentFile(pdf_bytes),
                save=True,
            )
            self.stats['documents'] += 1

    def _spread_timestamps(self, brokerage):
        models = (
            Client,
            Insurer,
            LineOfBusiness,
            Agent,
            Producer,
            Proposal,
            Policy,
            CoveredItem,
            Claim,
            Endorsement,
            Commission,
            CommissionSplit,
            Renewal,
            Pipeline,
            Stage,
            Deal,
            DealStageHistory,
            Notification,
            ChatSession,
            Document,
        )
        for model in models:
            for obj in model.objects.filter(brokerage=brokerage).only('id'):
                created_at = self._past_datetime(days=730)
                model.objects.filter(pk=obj.pk).update(
                    created_at=created_at,
                    updated_at=created_at,
                )
        for session in ChatSession.objects.filter(brokerage=brokerage):
            for message in session.messages.only('id'):
                created_at = self._past_datetime(days=180)
                ChatMessage.objects.filter(pk=message.pk).update(
                    created_at=created_at,
                    updated_at=created_at,
                )

    def _pipeline(self, brokerage):
        pipeline = Pipeline.objects.filter(brokerage=brokerage, is_default=True).first()
        if pipeline is None:
            pipeline = Pipeline.objects.filter(brokerage=brokerage).first()
        if pipeline is None:
            pipeline = Pipeline.objects.create(
                brokerage=brokerage,
                name='Vendas',
                is_default=True,
            )
        if pipeline.stages.count() < 6:
            pipeline.stages.all().delete()
            for order, (name, color, is_won, is_lost) in enumerate(STAGE_DEFINITIONS, start=1):
                Stage.objects.create(
                    brokerage=brokerage,
                    pipeline=pipeline,
                    name=name,
                    color=color,
                    order=order,
                    is_won=is_won,
                    is_lost=is_lost,
                )
        return pipeline

    def _covered_item(self, brokerage, item_type, proposal=None, policy=None):
        return CoveredItem(
            brokerage=brokerage,
            proposal=proposal,
            policy=policy,
            item_type=item_type,
            description=self._item_description(item_type),
            identifier=self._item_identifier(item_type),
            insured_amount=self._money('15000', '250000'),
            attributes=self._item_attributes(item_type),
            coverages=random.sample(
                CoveredItem.COVERAGE_PRESETS.get(item_type, []) or ['Cobertura básica'],
                k=min(2, len(CoveredItem.COVERAGE_PRESETS.get(item_type, [])) or 1),
            ),
        )

    def _policy_dates(self, status, index):
        today = timezone.now().date()
        if status == Policy.Status.EXPIRED:
            end_date = today - timedelta(days=random.randint(5, 180))
            return end_date - timedelta(days=365), end_date
        if status == Policy.Status.RENEWED:
            end_date = today - timedelta(days=random.randint(1, 120))
            return end_date - timedelta(days=365), end_date
        if status == Policy.Status.CANCELED:
            start_date = today - timedelta(days=random.randint(30, 240))
            return start_date, start_date + timedelta(days=random.randint(60, 250))
        if index % 4 == 0:
            end_date = today + timedelta(days=random.choice([7, 30, 60, 90]))
            return end_date - timedelta(days=365), end_date
        start_date = today - timedelta(days=random.randint(1, 240))
        return start_date, start_date + timedelta(days=365)

    def _stage_for_status(self, stages, status, index):
        if status == Deal.Status.WON:
            return next(stage for stage in stages if stage.is_won)
        if status == Deal.Status.LOST:
            return next(stage for stage in stages if stage.is_lost)
        open_stages = [stage for stage in stages if not stage.is_won and not stage.is_lost]
        return self._cycle(open_stages, index)

    def _item_description(self, item_type):
        if item_type == CoveredItem.ItemType.AUTO:
            brand = random.choice(['Honda', 'Toyota', 'Jeep', 'Fiat'])
            return f'{brand} {self.fake.word().title()}'
        if item_type == CoveredItem.ItemType.PROPERTY:
            return f'Imóvel em {self.fake.city()}'
        if item_type == CoveredItem.ItemType.FLEET:
            return f'Frota comercial com {random.randint(3, 25)} veículos'
        if item_type == CoveredItem.ItemType.TRAVEL:
            return f'Viagem para {self.fake.city()}'
        if item_type == CoveredItem.ItemType.LIFE:
            return f'Vida individual · {self.fake.name()}'
        if item_type == CoveredItem.ItemType.EQUIPMENT:
            return f'Equipamento {self.fake.word().title()}'
        return 'Item segurado diverso'

    def _item_identifier(self, item_type):
        if item_type == CoveredItem.ItemType.AUTO:
            return f'{self.fake.bothify(text="???-####").upper()}'
        if item_type == CoveredItem.ItemType.LIFE:
            return self._cpf(random.randint(1, 9999))
        if item_type == CoveredItem.ItemType.EQUIPMENT:
            return self.fake.bothify(text='SN-####-????').upper()
        return self.fake.postcode()

    def _item_attributes(self, item_type):
        today = timezone.now().date()
        if item_type == CoveredItem.ItemType.AUTO:
            return {
                'marca': random.choice(['Honda', 'Toyota', 'Jeep', 'Fiat']),
                'modelo': self.fake.word().title(),
                'ano': random.randint(2017, 2026),
                'placa': self.fake.bothify(text='???-####').upper(),
                'combustivel': random.choice(['Flex', 'Diesel', 'Híbrido']),
            }
        if item_type == CoveredItem.ItemType.PROPERTY:
            return {
                'tipo_imovel': random.choice(['Casa', 'Apartamento', 'Comercial']),
                'endereco_completo': self.fake.address(),
                'area_m2': random.randint(45, 420),
            }
        if item_type == CoveredItem.ItemType.TRAVEL:
            return {
                'destino': self.fake.city(),
                'data_ida': str(today + timedelta(days=30)),
                'data_volta': str(today + timedelta(days=45)),
            }
        return {'origem': 'seed_demo'}

    def _ai_summary(self, entity):
        return (
            f'### Resumo automático de {entity}\n\n'
            '- Carteira com bom potencial de retenção.\n'
            '- Próxima ação sugerida: revisar cobertura e oportunidade de cross-sell.\n\n'
            'Este conteúdo é fake e foi gerado offline pelo comando `seed_demo`.'
        )

    def _chat_content(self, role, index):
        if role == ChatMessage.Role.USER:
            return 'Quais oportunidades merecem atenção nesta semana?'
        return (
            'Encontrei **apólices ativas**, renovações próximas e deals em cotação.\n\n'
            f'- Prioridade {index + 1}: falar com clientes de maior prêmio.\n'
            '- Sugestão: revisar comissões pendentes antes do fechamento.'
        )

    def _notification_title(self, index):
        return self._cycle(
            [
                'Renovação próxima',
                'Sinistro atualizado',
                'Relatório pronto',
                'Deal ganho',
                'Resumo de IA concluído',
            ],
            index,
        )

    def _notification_url(self, index, policies, claims, deals):
        if index % 3 == 0 and policies:
            return f'/apolices/{policies[index % len(policies)].id}/'
        if index % 3 == 1 and claims:
            return f'/sinistros/{claims[index % len(claims)].id}/'
        if deals:
            return f'/crm/negociacoes/{deals[index % len(deals)].id}/'
        return '/'

    def _person_or_company_name(self, entity_type):
        if entity_type == EntityType.COMPANY:
            return self.fake.company()
        return self.fake.name()

    def _client_document(self, person_type, index, number):
        if person_type == Client.PersonType.NATURAL:
            return self._cpf(index * 1000 + number)
        return self._cnpj(index * 1000 + number)

    def _document(self, entity_type, number):
        if entity_type == EntityType.COMPANY:
            return self._cnpj(number)
        return self._cpf(number)

    def _cpf(self, number):
        base = f'{number % 1000000000:09d}'
        return f'{base[:3]}.{base[3:6]}.{base[6:]}-{self._cpf_digits(base)}'

    def _cpf_digits(self, base):
        digits = [int(digit) for digit in base]
        first = sum(digit * weight for digit, weight in zip(digits, range(10, 1, -1)))
        first = 11 - (first % 11)
        first = 0 if first >= 10 else first
        digits.append(first)
        second = sum(digit * weight for digit, weight in zip(digits, range(11, 1, -1)))
        second = 11 - (second % 11)
        second = 0 if second >= 10 else second
        return f'{first}{second}'

    def _cnpj(self, number):
        base = f'{number % 1000000000000:012d}'
        digits = self._cnpj_digits(base)
        return (
            f'{base[:2]}.{base[2:5]}.{base[5:8]}/'
            f'{base[8:12]}-{digits}'
        )

    def _cnpj_digits(self, base):
        numbers = [int(digit) for digit in base]
        first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        first = sum(digit * weight for digit, weight in zip(numbers, first_weights))
        first = 11 - (first % 11)
        first = 0 if first >= 10 else first
        numbers.append(first)
        second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        second = sum(digit * weight for digit, weight in zip(numbers, second_weights))
        second = 11 - (second % 11)
        second = 0 if second >= 10 else second
        return f'{first}{second}'

    def _money(self, minimum, maximum):
        cents = random.randint(int(Decimal(minimum) * 100), int(Decimal(maximum) * 100))
        return (Decimal(cents) / Decimal('100')).quantize(Decimal('0.01'))

    def _money_rate(self, minimum, maximum):
        return Decimal(str(round(random.uniform(float(minimum), float(maximum)), 4)))

    def _past_datetime(self, days):
        return timezone.now() - timedelta(days=random.randint(0, days))

    def _cycle(self, values, index):
        return list(values)[index % len(values)]


class UserRole:
    def __init__(self, email_prefix, role, count):
        self.email_prefix = email_prefix
        self.role = role
        self.count = count
