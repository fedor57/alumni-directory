from django.core.management.base import BaseCommand, CommandError
from core.models import Grade, Student


class Command(BaseCommand):
    help = 'Import students'

    def add_arguments(self, parser):
        parser.add_argument('file_tsv')

    def handle(self, *args, **options):
        with open(options['file_tsv']) as f:
            for line in f:
                name, year, grade = line.rstrip('\r\n').split('\t')
                g, g_created = Grade.objects.get_or_create(
                    graduation_year=year, letter=grade)
                Student.objects.get_or_create(name=name, main_grade=g)

        self.stdout.write(
            self.style.SUCCESS('Successfully import'))
