from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Add a user to a group from CLI"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email", type=str, required=True, help="Email of the user"
        )
        parser.add_argument(
            "--group_name", type=str, required=True, help="Name of the group"
        )

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"]
        group_name = options["group_name"]

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            group = Group.objects.get(name=group_name)
            user.groups.add(group)

            self.stdout.write(
                self.style.SUCCESS(f"User {email} added to group '{group_name}'")
            )
        else:
            self.stdout.write(f"User with email {email} not exists")
