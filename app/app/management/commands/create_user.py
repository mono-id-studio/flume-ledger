from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Create a superuser with email, password, first and last name from CLI"

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

        if not User.objects.filter(email=email).exists():
            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            group, _ = Group.objects.get_or_create(name="operator")
            user.groups.add(group)

            self.stdout.write(
                self.style.SUCCESS(
                    f"User {email} created and added to group 'operator'"
                )
            )
        else:
            self.stdout.write(f"User with email {email} already exists")
