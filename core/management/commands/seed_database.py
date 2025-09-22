from django.core.management.base import BaseCommand
from scripts.seed import main as seed_main


class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset the database before seeding (WARNING: This will delete all data)',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(
                self.style.WARNING('WARNING: This will delete all existing data!')
            )
            confirm = input('Are you sure you want to continue? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        try:
            seed_main()
            self.stdout.write(
                self.style.SUCCESS('Database seeding completed successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during seeding: {e}')
            )
            raise
