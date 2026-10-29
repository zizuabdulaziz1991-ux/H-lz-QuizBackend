import json
import random

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.quiz.models import Category, Choice, Question


class Command(BaseCommand):
    help = (
        "JSON dosyasından soru içe aktarır. Biçim: "
        '{"<kategori-slug>": [["Soru", "Doğru şık", "Yanlış 1", "Yanlış 2", "Yanlış 3"], ...]}. '
        "Aynı metne sahip sorular atlanır."
    )

    def add_arguments(self, parser):
        parser.add_argument("path", nargs="?", default="data/questions.json")

    @transaction.atomic
    def handle(self, *args, **opts):
        try:
            with open(opts["path"], encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as exc:
            raise CommandError(f"Dosya okunamadı: {exc}")

        created = skipped = 0
        for slug, rows in data.items():
            try:
                category = Category.objects.get(slug=slug)
            except Category.DoesNotExist:
                raise CommandError(f"Kategori yok: {slug}")
            for row in rows:
                if len(row) != 5:
                    raise CommandError(f"Her satır 5 elemanlı olmalı (soru + 4 şık): {row}")
                text, *choices = row
                if Question.objects.filter(category=category, text=text).exists():
                    skipped += 1
                    continue
                q = Question.objects.create(category=category, text=text)
                order = list(enumerate(choices))
                random.shuffle(order)
                Choice.objects.bulk_create(
                    Choice(question=q, text=c, is_correct=(i == 0), position=pos)
                    for pos, (i, c) in enumerate(order)
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f"{created} soru eklendi, {skipped} atlandı."))
