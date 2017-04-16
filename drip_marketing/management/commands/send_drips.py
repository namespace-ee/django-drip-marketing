from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def handle(self, *args, **options):
        from drip_marketing.models import SentDrip

        for drip in SentDrip.objects.filter(state=SentDrip.STATE_QUEUED):
            drip.send()
