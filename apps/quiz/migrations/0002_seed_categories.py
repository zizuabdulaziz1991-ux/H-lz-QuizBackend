from django.db import migrations

CATEGORIES = [
    ("tarih", "Tarih", "landmark", "#FF8A3D"),
    ("muzik", "Müzik", "music", "#FF5CA8"),
    ("cografya", "Coğrafya", "globe", "#2ED8A7"),
    ("genel-kultur", "Genel Kültür", "lightbulb", "#FFC93C"),
    ("fizik", "Fizik", "atom", "#3DA5FF"),
]


def seed(apps, schema_editor):
    Category = apps.get_model("quiz", "Category")
    for slug, name, icon, color in CATEGORIES:
        Category.objects.get_or_create(slug=slug, defaults={"name": name, "icon": icon, "color": color})


class Migration(migrations.Migration):
    dependencies = [("quiz", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
