# coding=utf-8
from __future__ import unicode_literals

from collections import Counter

from django.utils import timezone

from core.models import Vote, AuthCode, FieldValue


def update_status(target_id, field_name):
    values = {}  # Экземпляры FieldValue
    need_statuses = {}
    l = []

    qs = Vote.objects.filter(
        field_value__target_id=target_id,
        field_value__field_name=field_name,
    ).select_related(
        'field_value',
        'author_code',
    ).exclude(
        field_value__status=FieldValue.STATUS_DELETED,
    ).order_by('-timestamp')

    for vote in qs.iterator():
        pk = vote.field_value_id
        author = vote.author_code
        values.setdefault(pk, vote.field_value)
        if not author or author.status == AuthCode.STATUS_NONEXISTENT:
            valid = False
            trust_level = None
            is_me = False
        elif author.status == AuthCode.STATUS_VALID:
            valid = True
            trust_level = author.trust_level
            is_me = target_id == author.owner_id
        elif author.revoked_at and vote.timestamp < author.revoked_at:
            valid = True
            trust_level = author.trust_level
            is_me = target_id == author.owner_id
        else:
            valid = False
            trust_level = None
            is_me = False

        if vote.value in (Vote.VOTE_ADDED, Vote.VOTE_UP):
            l.append((pk, +1, valid, trust_level, is_me))
        else:
            l.append((pk, -1, valid, trust_level, is_me))

    if not l:
        return

    statuses = {}
    votes = {}
    for pk, status, vote in get_statuses(l):
        votes[pk] = vote
        statuses[pk] = status

    for pk, f in values.items():
        if statuses[pk] is None:
            need_status = FieldValue.STATUS_HIDDEN
        elif pk in need_statuses:
            need_status = need_statuses[pk]
        elif f.field_name == FieldValue.FIELD_LINK:
            need_status = FieldValue.STATUS_TRUSTED
        elif statuses[pk] is True:
            need_status = FieldValue.STATUS_TRUSTED
        else:
            need_status = FieldValue.STATUS_UNTRUSTED

        update_fields = []
        if f.status != need_status:
            f.status = need_status
            f.status_update_date = timezone.now()
            update_fields.extend(['status', 'status_update_date'])
        if f.votes != votes[pk]:
            f.votes = votes[pk]
            update_fields.append('votes')
        if update_fields:
            f.save(update_fields=update_fields)


def get_statuses(votes):
    vs = Counter()

    for value, vote, valid, trust_level, is_me in votes:
        if is_me:  # Своим правкам доверяем чуть больше
            vs[value] += vote * trust_level * 10
        elif valid:
            vs[value] += vote * trust_level
        else:  # Анонимус
            vs[value] += vote * 0.1

    result = []
    vs = sorted(vs.items(), key=lambda x: x[1], reverse=True)
    result.append((vs[0][0], True, vs[0][1]))
    for value, vote in vs[1:]:
        if vote < 0:
            need_status = None
        else:
            need_status = False
        result.append((value, need_status, vote))

    return result
