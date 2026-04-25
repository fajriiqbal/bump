from django.core.management.base import BaseCommand
from django.core.management import call_command
from pathlib import Path
from django.conf import settings


class Command(BaseCommand):
    help = "Buat backup database berbasis dumpdata untuk development."

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / "media" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / "backup.json"
        with target.open("w", encoding="utf-8") as fh:
            call_command("dumpdata", indent=2, stdout=fh)
        self.stdout.write(self.style.SUCCESS(f"Backup tersimpan di {target}"))
