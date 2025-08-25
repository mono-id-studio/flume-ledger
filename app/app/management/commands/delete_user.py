from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Delete a user with email from CLI"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email", type=str, required=True, help="Email of the user"
        )
        parser.add_argument(
            "--password", type=str, required=True, help="Password of the user"
        )

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"]
        password = options["password"]

        User.objects.filter(email=email, password=password).delete()
        self.stdout.write(self.style.SUCCESS(f"User {email} deleted"))
