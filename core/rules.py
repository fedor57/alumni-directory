# coding=utf-8
from __future__ import unicode_literals

from itertools import groupby

from django.utils import timezone

from core.models import Vote, AuthCode, FieldValue


def update_fields(target_id, field_name, timestamp=None):
    all_votes = list(Vote.objects.filter(
        field_value__target_id=target_id,
        field_value__field_name=field_name,
    ).select_related(
        'field_value',
        'author_code',
    ).order_by('field_value_id', 'id'))

    computed_statuses = {}
    old_votes = {}
    edits = []
    if not timestamp:
        timestamp = timezone.now()

    for edit, votes in groupby(all_votes, key=lambda x: x.field_value):
        edits.append(edit)
        old_votes[edit] = edit.votes
        edit.votes = 0
        deleted_met = False
        votes = list(votes)
        for vote in votes:
            if vote.value == Vote.VOTE_TO_DEL:
                deleted_met = True
            change = vote.value in (Vote.VOTE_ADDED, Vote.VOTE_UP) and 1 or -1
            is_own_edit = False
            trust_level = 0.1
            if vote.author_code:
                is_own_edit = vote.author_code.owner_id == edit.target_id
                trust_level = vote.author_code.trust_level
            factor = is_own_edit and 10 or 1

            edit.votes += change * trust_level * factor

        if deleted_met and len(votes) == 2:
            computed_statuses[edit] = FieldValue.STATUS_DELETED

    edits = sorted(edits, key=lambda e: e.votes, reverse=True)

    first = True
    for edit in edits:
        if edit not in computed_statuses:
            if edit.votes > 0:
                if first:
                    computed_statuses[edit] = FieldValue.STATUS_TRUSTED
                else:
                    computed_statuses[edit] = FieldValue.STATUS_UNTRUSTED
            else:
                computed_statuses[edit] = FieldValue.STATUS_HIDDEN
        first = False

        fields_to_update = []
        if edit.status != computed_statuses[edit]:
            edit.status = computed_statuses[edit]
            edit.status_update_date = timestamp
            fields_to_update.extend(['status', 'status_update_date'])
        if edit.votes != old_votes[edit]:
            fields_to_update.append('votes')
        if fields_to_update:
            edit.save(update_fields=fields_to_update)
