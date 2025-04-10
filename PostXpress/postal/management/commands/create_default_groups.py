from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Create default user groups'

    def handle(self, *args, **kwargs):
        roles = ['customer', 'postal_staff', 'admin']
        for role in roles:
            group, created = Group.objects.get_or_create(name=role)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Successfully created group: {role}"))
            else:
                self.stdout.write(self.style.WARNING(f"Group already exists: {role}"))
