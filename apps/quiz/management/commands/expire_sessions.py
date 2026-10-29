from django.core.management.base import BaseCommand

from apps.quiz.services import expire_stale_sessions


class Command(BaseCommand):
    help = "N saatten eski tamamlanmamış oturumları 'expired' yapar."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=24)

    def handle(self, *args, **opts):
        n = expire_stale_sessions(opts["hours"])
        self.stdout.write(f"{n} oturum süresi doldu olarak işaretlendi.")
