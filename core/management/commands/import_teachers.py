from django.core.management.base import BaseCommand, CommandError
from core.models import Grade, Teachers


class Command(BaseCommand):
    help = 'Import teachers'

    def add_arguments(self, parser):
        parser.add_argument('file_tsv')

    def handle(self, *args, **options):
        cleared_grades = set()
        with open(options['file_tsv']) as f:
            for line in f:
                year, letter, torder, role, name = line.rstrip('\r\n').split('\t')
                g, g_created = Grade.objects.get_or_create(
                    graduation_year=year, letter=letter)
                if g.pk not in cleared_grades:
                    Teachers.objects.filter(grade_id=g.pk).delete()
                    cleared_grades.add(g.pk)
                g.teachers.create(role=role, content=name, torder=torder)

        self.stdout.write(
            self.style.SUCCESS('Successfully import'))
