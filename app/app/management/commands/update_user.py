from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Update a user with email, password, first and last name from CLI"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email", type=str, required=True, help="Email of the user"
        )
        parser.add_argument(
            "--password", type=str, required=True, help="Password of the user"
        )
        parser.add_argument(
            "--first_name", type=str, default="Admin", help="First name of the user"
        )
        parser.add_argument(
            "--last_name", type=str, default="User", help="Last name of the user"
        )

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"]
        password = options["password"]
        first_name = options["first_name"]
        last_name = options["last_name"]

        User.objects.filter(email=email).update(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        self.stdout.write(self.style.SUCCESS(f"User {email} updated"))
