# coding=utf-8
from __future__ import unicode_literals

from collections import Counter


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
