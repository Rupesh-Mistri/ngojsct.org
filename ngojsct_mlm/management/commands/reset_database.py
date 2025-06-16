from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import logging
from django.conf import settings
from .import_state_data import import_data_csv  # Your custom import function

class Command(BaseCommand):
    help = 'Reset database and import state data'

    def handle(self, *args, **kwargs):
        # Configure logging
        log_file_path = os.path.join(settings.BASE_DIR, "protected_data", 'logfile1.log')
        logging.basicConfig(
            filename=log_file_path,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        try:
            self.stdout.write("Flushing the database...")
            call_command('flush', '--noinput')  # Removes all data but keeps schema

            self.stdout.write("Running migrations...")
            call_command('migrate')

            self.stdout.write("Importing state data...")
            import_data_csv()

            logging.info("Database reset and data import completed successfully.")
            self.stdout.write(self.style.SUCCESS("✅ Done: Database reset and state data imported."))

        except Exception as e:
            logging.error(f"Error during reset: {str(e)}")
            self.stderr.write(self.style.ERROR(f"❌ Error: {str(e)}"))
