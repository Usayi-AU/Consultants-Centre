from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create a default admin account with username admin and password 30'

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('Admin user already exists.'))
            return
        User.objects.create_superuser('admin', 'admin@example.com', '30')
        self.stdout.write(self.style.SUCCESS('Admin user created with username admin and password 30'))
