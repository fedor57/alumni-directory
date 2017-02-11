import json

from django.core.management.base import BaseCommand
from django.utils.encoding import force_str, force_text


class Command(BaseCommand):
    help = 'Import students'

    def add_arguments(self, parser):
        parser.add_argument('file_json')
        parser.add_argument('--db')
        parser.add_argument('--teachers')

    def handle(self, *args, **options):
        with open(options['file_json']) as f:
            data = json.load(f)

        teachers = open(options['teachers'], 'w')
        db = open(options['db'], 'w')

        for kla, d in data.items():
            year = str(d['year'])
            letter = force_text(d['name'].split()[1])[1]
            for i, teacher in enumerate(d['teachers']):
                teachers.write(year)
                teachers.write('\t')
                teachers.write(force_str(letter))
                teachers.write('\t')
                teachers.write(str(i))
                teachers.write('\t')
                teachers.write(force_str(teacher['role']))
                teachers.write('\t')
                teachers.write(force_str(teacher['text']))
                teachers.write('\n')
            for student in d['pupils']:
                db.write(force_str(student))
                db.write('\t')
                db.write(year)
                db.write('\t')
                db.write(force_str(letter))
                db.write('\n')

        teachers.close()
        db.close()

        self.stdout.write(
            self.style.SUCCESS('Successfully import'))
