from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from crm.models import ActionItem

User = get_user_model()

class Command(BaseCommand):
    help = 'Create user accounts for all action item owners'

    def handle(self, *args, **options):
        owners = ActionItem.objects.values_list('owner', flat=True).distinct()
        owners = [o.strip() for o in owners if o and o.strip()]
        created = 0
        for owner in owners:
            if not User.objects.filter(username=owner).exists():
                User.objects.create_user(username=owner, email=f'{owner.lower().replace(" ", "_")}@intellego.local', password='30')
                created += 1
                self.stdout.write(f'Created user: {owner}')
        self.stdout.write(self.style.SUCCESS(f'Total created: {created} users. All users have password: 30'))
