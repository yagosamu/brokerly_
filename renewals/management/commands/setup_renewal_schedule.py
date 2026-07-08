import json

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = 'Setup daily Beat schedules for renewal tasks.'

    def handle(self, *args, **options):
        renewal_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='6',
            day_of_month='*',
            month_of_year='*',
            day_of_week='*',
            timezone='America/Sao_Paulo',
        )
        renewal_task, renewal_created = PeriodicTask.objects.update_or_create(
            name='Check upcoming renewals (daily 06:00)',
            defaults={
                'crontab': renewal_schedule,
                'task': 'renewals.check_upcoming_renewals',
                'kwargs': json.dumps({}),
                'enabled': True,
            },
        )

        expiration_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='30',
            hour='0',
            day_of_month='*',
            month_of_year='*',
            day_of_week='*',
            timezone='America/Sao_Paulo',
        )
        expiration_task, expiration_created = (
            PeriodicTask.objects.update_or_create(
                name='Expire policies (daily 00:30)',
                defaults={
                    'crontab': expiration_schedule,
                    'task': 'renewals.expire_policies',
                    'kwargs': json.dumps({}),
                    'enabled': True,
                },
            )
        )

        renewal_status = 'created' if renewal_created else 'updated'
        expiration_status = 'created' if expiration_created else 'updated'
        self.stdout.write(
            self.style.SUCCESS(
                f'PeriodicTask {renewal_status}: {renewal_task.name}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'PeriodicTask {expiration_status}: {expiration_task.name}'
            )
        )
