# coding=utf-8
from __future__ import unicode_literals

from collections import Counter, OrderedDict

from django.core.validators import RegexValidator
from django.db import models
from django.db.models.aggregates import Count
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.functional import cached_property


class Timestamped(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Grade(models.Model):
    """
    Класс
    """
    is_grade = True
    letter = models.CharField(max_length=1)
    graduation_year = models.PositiveSmallIntegerField()  # TODO: вылидировать год
    # TODO: добавить читаемый id

    class Meta:
        verbose_name = 'класс'
        verbose_name_plural = 'классы'
        unique_together = ('letter', 'graduation_year')
        ordering = ('-graduation_year', 'letter')

    def __unicode__(self):
        return '%s%s' % (self.graduation_year, self.letter)


class AuthCodeManager(models.Manager):
    def get_by_code(self, code):
        try:
            author_code = self.get(code=code)
        except ObjectDoesNotExist:
            # TODO: resolve code to real name and status
            author_code = self.create(
                code=code, status='active', owner_name='Anonymous'
            )
        return author_code


class AuthCode(models.Model):
    STATUS_VALID = 'valid'
    STATUS_NONEXISTENT = 'nonexistent'
    STATUS_REVOKED = 'revoked'
    STATUS_CHOICES = (
        (STATUS_VALID, 'валиден'),
        (STATUS_NONEXISTENT, 'несуществующий'),
        (STATUS_REVOKED, 'отозван'),
    )

    code = models.CharField(
        validators=[RegexValidator(r'^[^\s]+$')],
        max_length=100, primary_key=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    owner = models.ForeignKey('Student', null=True)
    updated_at = models.DateTimeField('Дата обновления данных', auto_now=True)
    revoked_at = models.DateTimeField('Дата отзыва', null=True, blank=True)
    trust_level = models.FloatField('Уровень доверия', default=1)

    class Meta:
        verbose_name = 'код авторизации'
        verbose_name_plural = 'коды авторизации'

    objects = AuthCodeManager()

    def __unicode__(self):
        return '%s (%s)' % (self.code, self.owner)


class Student(Timestamped):
    """
    Выпускник
    """
    name = models.CharField(max_length=200)
    main_grade = models.ForeignKey(Grade)
    creator_code = models.ForeignKey(AuthCode, blank=True, null=True)

    class Meta:
        verbose_name = 'выпускник'
        verbose_name_plural = 'выпускники'

    def __unicode__(self):
        return '%s %s' % (self.name, self.main_grade)

    def get_absolute_url(self):
        return reverse('student-detail', args=[str(self.id)])

    @cached_property
    def ordered_facts(self):
        result = OrderedDict()
        for name, text, _ in FieldValue.EDITABLE_FIELDS:
            result[name] = []
        order = [i[0] for i in FieldValue.STATUS_CHOICES]
        key = lambda x: (order.index(x.status), -x.votes)
        ms = sorted(self.modifications.all(), key=key)
        for m in ms:
            result[m.field_name].append(m)
        return result


class FieldValueManager(models.Manager):
    def visible(self):
        return self.exclude(status='hidden')


class FieldValue(Timestamped):
    """
    Каждая правка предлагает добавить значение поля
    """
    # Типы правок (field_name)
    FIELD_NAME = 'name'
    FIELD_EMAIL = 'email'
    FIELD_CITY = 'city'
    FIELD_COMPANY = 'company'
    FIELD_LINK = 'link'
    FIELD_SOCIAL_VK = 'social_vk'
    FIELD_SOCIAL_FB = 'social_fb'
    FIELD_GRADE = 'grade'
    EDITABLE_FIELDS = (
        (FIELD_NAME, 'Изменения фамилии / имени', ''),
        (FIELD_EMAIL, 'Email', 'Скрыт от просмотра, но на него можно написать'),
        (FIELD_CITY, 'Город', ''),
        (FIELD_COMPANY, 'Компания / ВУЗ', ''),
        (FIELD_LINK, 'Домашняя страница', ''),
        (FIELD_SOCIAL_FB, 'Facebook', ''),
        (FIELD_SOCIAL_VK, 'ВКонтакте', ''),
        (FIELD_GRADE, 'Учился также в классе', ''),
    )

    STATUS_TRUSTED = 'trusted'
    STATUS_UNTRUSTED = 'untrusted'
    STATUS_HIDDEN = 'hidden'
    STATUS_DELETED = 'deleted'
    STATUS_CHOICES = (
        (STATUS_TRUSTED, 'Уверенная'),
        (STATUS_UNTRUSTED, 'Неуверенная'),
        (STATUS_HIDDEN, 'Скрытая'),
        (STATUS_DELETED, 'Удаленная'),
    )

    target = models.ForeignKey(Student, related_name='modifications',
                               help_text='Выпускник')
    author_code = models.ForeignKey(
        AuthCode, related_name='modify_activity',
        verbose_name='Автор правки',
        blank=True, null=True)
    field_name = models.CharField(
        'Имя поля', max_length=20,
        choices=[(k, v) for k, v, h in EDITABLE_FIELDS])
    field_value = models.CharField('Значение поля', max_length=200)
    status = models.CharField('Статус правки', choices=STATUS_CHOICES,
                              default=STATUS_TRUSTED, max_length=20)
    status_update_date = models.DateTimeField(
        'Дата обновления статуса', null=True, blank=True)
    votes = models.IntegerField(default=0)

    objects = FieldValueManager()

    class Meta:
        verbose_name = 'правка'
        verbose_name_plural = 'правки'

    def save(self, *args, **kwargs):
        # Проверяем уникальность ('target', 'field_value', 'field_name')
        if not self.pk and FieldValue.objects.filter(
                target=self.target_id,
                field_value=self.field_value,
                field_name=self.field_name).exists():
            return  # Недобавляем повторящиеся значение
        super(FieldValue, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%s _ %s' % (self.target, self.get_field_name_display())

    @classmethod
    def update_status(cls, target_id, field_name):
        votes = Counter()
        values = {}  # Экземпляры FieldValue
        addts = {}  # timestamp последнего голоса
        upts = {}  # timestamp последнего голоса
        need_statuses = {}

        qs = Vote.objects.filter(
            field_value__target_id=target_id,
            field_value__field_name=field_name,
        ).select_related(
            'field_value',
            'author_code',
        ).exclude(
            field_value__status=cls.STATUS_DELETED,
        ).order_by('-timestamp')

        last = None
        for vote in qs.iterator():
            pk = vote.field_value_id
            author = vote.author_code

            values.setdefault(pk, vote.field_value)

            is_me = target_id == author.owner_id
            weight = 0.1  # вес голоса анонимуса
            if not author:
                pass  # Анонимный голос
            elif author.status == AuthCode.STATUS_REVOKED:
                if author.revoked_at and vote.timestamp < author.revoked_at:
                    weight = author.trust_level
                else:
                    is_me = False  # "анонимизация"
                    weight = 0.0  # Вес голоса невалидного кода
            elif author.status == AuthCode.STATUS_VALID:
                if is_me:
                    weight = 1  # вес собственной правки
                else:
                    weight = author.trust_level

            if last is not None and \
                    last.value == Vote.VOTE_TO_DEL and \
                    vote.value == Vote.VOTE_ADDED:
                need_statuses[pk] = FieldValue.STATUS_DELETED
            elif vote.value == Vote.VOTE_ADDED:
                addts.setdefault(pk, vote.timestamp)
                votes[pk] += weight
            elif vote.value == Vote.VOTE_UP:
                upts.setdefault(pk, vote.timestamp)
                votes[pk] += weight
            elif vote.value == Vote.VOTE_DOWN:
                votes[pk] -= weight
            last = vote

        def get_max(x):
            if x:
                x = sorted(x.items(), key=lambda v: v[1], reverse=True)
                return x[0]

        vote_max = get_max(votes)
        upts_max = get_max(upts)
        addts_max = get_max(addts)

        if not upts_max and not addts_max and vote_max:
            need_statuses[vote_max[0]] = FieldValue.STATUS_TRUSTED
        elif not upts_max:
            need_statuses[addts_max[0]] = FieldValue.STATUS_TRUSTED
        elif not addts_max and vote_max:
            need_statuses[vote_max[0]] = FieldValue.STATUS_TRUSTED
        elif addts_max[1] > upts_max[1] or addts_max[0] == upts_max[0]:
            need_statuses[addts_max[0]] = FieldValue.STATUS_TRUSTED
        elif vote_max:
            need_statuses[vote_max[0]] = FieldValue.STATUS_TRUSTED

        for pk, f in values.items():
            if votes[pk] < 0:
                need_status = FieldValue.STATUS_HIDDEN
            elif pk in need_statuses:
                need_status = need_statuses[pk]
            elif f.field_name == cls.FIELD_LINK:
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


class Vote(Timestamped):
    """
    а также может быть голосованием за правильность или наличие ошибки
    """
    field_value = models.ForeignKey(
        FieldValue, verbose_name='Поле')
    author_code = models.ForeignKey(
        AuthCode, verbose_name='Код автора голоса',
        related_name='votes', blank=True, null=True)

    VOTE_ADDED = 'added'
    VOTE_UP = 'upvoted'
    VOTE_DOWN = 'downvoted'
    VOTE_TO_DEL = 'to_delete'
    VOTE_CHOICES = (
        (VOTE_ADDED, 'добавлено'),
        (VOTE_UP, 'за'),
        (VOTE_DOWN, 'против'),
        (VOTE_TO_DEL, 'удалить'),
    )
    value = models.CharField('Тип голоса', choices=VOTE_CHOICES, max_length=16)

    class Meta:
        verbose_name = 'голос'
        verbose_name_plural = 'голоса'
        unique_together = ('field_value', 'author_code', 'value')

    def __unicode__(self):
        return self.field_value.field_value

    def save(self, *args, **kwargs):
        super(Vote, self).save(*args, **kwargs)
        self.field_value.update_status(
            self.field_value.target_id,
            self.field_value.field_name,
        )
