from django.test import TestCase

from core import rules
from core.models import *


class FieldValueStatusTestCase(TestCase):
    def setUp(self):
        super(FieldValueStatusTestCase, self).setUp()
        g = Grade(letter='U', graduation_year='2048')
        g.save()
        xu = Student(name='Xu Bo', main_grade=g)
        xu.save()
        nguen = Student(name='Nguen Zobra', main_grade=g)
        nguen.save()
        xu_code = AuthCode(status=AuthCode.STATUS_VALID, owner=xu, code='1')
        xu_code.save()
        nguen_code = AuthCode(status=AuthCode.STATUS_VALID, owner=nguen, code='2')
        nguen_code.save()

        self.f = FieldValue(target=xu, author_code=xu_code, field_name=FieldValue.FIELD_CITY, field_value='Lima')
        self.f.save()
        Vote.objects.create(field_value=self.f, author_code=xu_code, value=Vote.VOTE_ADDED)

    def test_trusted(self):
        rules.update_fields(self.f.target_id, self.f.field_name)
        self.f.refresh_from_db()
        self.assertEqual(self.f.status, FieldValue.STATUS_TRUSTED)
        self.assertEqual(self.f.votes, 10.0)

    def test_untrusted(self):
        c = AuthCode.objects.get(code='2')
        f = FieldValue(target=self.f.target, author_code=c, field_name=FieldValue.FIELD_CITY, field_value='Osaka')
        f.save()
        Vote.objects.create(field_value=f, author_code=c, value=Vote.VOTE_ADDED)

        rules.update_fields(self.f.target_id, self.f.field_name)
        f.refresh_from_db()
        self.assertEqual(f.status, FieldValue.STATUS_UNTRUSTED)
        self.assertEqual(f.votes, 1.0)

    def test_hidden(self):
        c = AuthCode.objects.get(code='2')
        vote = Vote.objects.all()[0]
        vote.author_code = c
        vote.save()
        self.f.author_code = c
        self.f.save()
        c = AuthCode.objects.get(code='1')
        Vote.objects.create(field_value=self.f, author_code=c, value=Vote.VOTE_DOWN)

        rules.update_fields(self.f.target_id, self.f.field_name)
        self.f.refresh_from_db()
        self.assertEqual(self.f.status, FieldValue.STATUS_HIDDEN)
        self.assertEqual(self.f.votes, -9.0)

    def test_deleted(self):
        c = AuthCode.objects.get(code='1')
        Vote.objects.create(field_value=self.f, author_code=c, value=Vote.VOTE_TO_DEL)

        rules.update_fields(self.f.target_id, self.f.field_name)
        self.f.refresh_from_db()
        self.assertEqual(self.f.status, FieldValue.STATUS_DELETED)
        self.assertEqual(self.f.votes, 0)

    def test_non_deleted(self):
        c = AuthCode.objects.get(code='1')
        Vote.objects.create(field_value=self.f, author_code=c, value=Vote.VOTE_TO_DEL)

        c = AuthCode.objects.get(code='2')
        Vote.objects.create(field_value=self.f, author_code=c, value=Vote.VOTE_UP)

        rules.update_fields(self.f.target_id, self.f.field_name)
        self.f.refresh_from_db()
        self.assertEqual(self.f.status, FieldValue.STATUS_TRUSTED)
        self.assertEqual(self.f.votes, 1.0)
