# coding=utf-8
import sys

from itertools import groupby

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max

from core import rules
from core.models import FieldValue, Vote


class Command(BaseCommand):
    help = 'Manage votes'
    CMD_CHECK = 'check'
    CMD_CONVERT = 'convert'
    CMD_UPDATE = 'update'
    COMMANDS = (CMD_CHECK, CMD_CONVERT, CMD_UPDATE)

    def add_arguments(self, parser):
        parser.add_argument(
            'subcommand',
            help="""`check' to check if votes are allright,
            `convert' to try to convert bad votes,
            `update' to recalculate fields scores and statuses 
            """
        )

    def handle(self, *args, **options):
        subcommand = options.get('subcommand')
        if subcommand not in self.COMMANDS:
            raise CommandError('Unknown subcommand {}. Use check|convert|update'.format(subcommand))

        self.__getattribute__('run_' + subcommand)()

    def run_check(self):
        total_fields = 0
        total_errors = 0
        no_error_fields = 0
        for field in FieldValue.objects.all():
            total_fields += 1
            errors = self._check_field(field)
            total_errors += len(errors)
            if not errors:
                no_error_fields += 1
            [self._err(msg) for msg in errors]
        self.stdout.write("Total errors: {}".format(total_errors))
        self.stdout.write("Fields without errors: {}/{}".format(no_error_fields, total_fields))

    def run_convert(self):
        self.stdout.write("Have you created a backup? [y/N] ", ending='')
        confirmation = sys.stdin.readline().strip()
        if confirmation != 'y':
            self.stdout.write("Create it then!")
            sys.exit(1)
        total_actions = 0
        for field in FieldValue.objects.all():
            msgs = self._convert_field(field)
            total_actions += len(msgs)
            [self.stdout.write(msg) for msg in msgs]
        self.stdout.write("Total actions taken: {}".format(total_actions))

    def run_update(self):
        for item in FieldValue.objects \
                .values('target_id', 'field_name') \
                .annotate(last_vote=Max('vote__timestamp')) \
                .order_by('last_vote'):
            rules.update_fields(item['target_id'], item['field_name'])

    def _err(self, msg):
        self.stdout.write(self.style.ERROR(msg))

    def _check_field(self, field):
        """

        :param field: FieldValue to check
        :type field: FieldValue
        :return:
        """
        errs = []
        author_id = field.author_code_id
        author_met = False
        votes = field.vote_set.order_by('author_code_id', 'id').all()
        for k, v in groupby(votes, key=lambda x: x.author_code_id):
            is_author = False
            up_met = False
            down_met = False
            for vote in v:
                if vote.value == Vote.VOTE_ADDED:
                    if author_met:
                        errs.append("Additional author for field #{}: {}".format(field.id, vote.author_code_id))
                    if vote.author_code_id != author_id:
                        errs.append("Mismatched author for field #{}: {} ≠ {}".format(
                            field.id, author_id, vote.author_code_id
                        ))
                    author_met = True
                    is_author = True
                elif is_author and vote.value in (Vote.VOTE_UP, Vote.VOTE_DOWN):
                    errs.append("Up/down vote by author for field #{}".format(field.id))
                elif not is_author and vote.value == Vote.VOTE_TO_DEL:
                    errs.append("Delete vote not by author for field #{}".format(field.id))
                elif up_met and vote.value == Vote.VOTE_DOWN:
                    errs.append("Down after up for field #{}".format(field.id))
                elif down_met and vote.value == Vote.VOTE_UP:
                    errs.append("Up after down for field #{}".format(field.id))
                if vote.value == Vote.VOTE_UP:
                    up_met = True
                if vote.value == Vote.VOTE_DOWN:
                    down_met = True
        if not author_met:
            errs.append("No author for field #{}".format(field.id))
        return errs

    def _convert_field(self, field):
        """

        :param field: FieldValue to convert
        :type field: FieldValue
        :return:
        """
        errs = []
        votes = field.vote_set.order_by('author_code_id', 'id').all()
        for k, v in groupby(votes, key=lambda x: x.author_code_id):
            is_author = False
            up_downs = []
            for vote in v:
                if vote.value == Vote.VOTE_ADDED:
                    is_author = True
                elif is_author and vote.value in (Vote.VOTE_UP, Vote.VOTE_DOWN):
                    vote.delete()
                    errs.append("Removed up/down vote by author for field #{}".format(field.id))
                    continue
                elif not is_author and vote.value == Vote.VOTE_TO_DEL:
                    vote.value = Vote.VOTE_DOWN
                    vote.save()
                    errs.append("Rewrote delete vote not by author to down for field #{}".format(field.id))
                if vote.value in (Vote.VOTE_UP, Vote.VOTE_DOWN):
                    up_downs.append(vote)
            if len(up_downs) > 1:
                for vote in up_downs[:-1]:
                    vote.delete()
                    errs.append("Removed additional up/down vote for field #{}".format(field.id))
        return errs
