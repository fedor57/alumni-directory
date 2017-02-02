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
    owner_name = models.CharField(max_length=200)
    updated_at = models.DateTimeField('Дата обновления данных', auto_now=True)
    revoked_at = models.DateTimeField('Дата отзыва', null=True, blank=True)

    class Meta:
        verbose_name = 'код авторизации'
        verbose_name_plural = 'коды авторизации'

    objects = AuthCodeManager()

    def __unicode__(self):
        return '%s (%s)' % (self.code, self.owner_name)


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
        return '%s (%s)' % (self.name, self.main_grade)

    def get_absolute_url(self):
        return reverse('student-detail', args=[str(self.id)])

    @cached_property
    def ordered_facts(self):
        result = OrderedDict()
        for name, text in FieldValue.EDITABLE_FIELDS:
            result[name] = []
        ms = self.modifications.all()
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
        (FIELD_NAME, 'Информация об изменении имени/фамилии'),
        (FIELD_EMAIL, 'Email, который не отображается, '
                      'но на который можно написать через форму'),
        (FIELD_CITY, 'Город'),
        (FIELD_COMPANY, 'Компания/ВУЗ'),
        (FIELD_LINK, 'Ссылка'),
        (FIELD_SOCIAL_FB, 'Facebook'),
        (FIELD_SOCIAL_VK, 'ВКонтакте'),
        (FIELD_GRADE, 'Класс'),
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
        'Имя поля', choices=EDITABLE_FIELDS, max_length=20)
    field_value = models.CharField('Значение поля', max_length=200)
    status = models.CharField('Статус правки', choices=STATUS_CHOICES,
                              default=STATUS_TRUSTED, max_length=20)
    status_update_date = models.DateTimeField(
        'Дата обновления статуса', null=True, blank=True)

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
        values = {}
        qs = cls.objects.filter(
            target_id=target_id,
            field_name=field_name
        ).exclude(status=cls.STATUS_DELETED)

        fresh = qs.order_by('-timestamp').first()

        for i in qs.filter(votes__value__in=
                           (Vote.VOTE_ADDED, Vote.VOTE_UP)) \
                .annotate(cv=Count('votes')) \
                .defer('id', 'status'):
            values[i.pk] = i
            votes[i.pk] += i.cv
        for i in qs.filter(votes__value=Vote.VOTE_DOWN) \
                .annotate(cv=Count('votes')) \
                .defer('id', 'status'):
            values[i.pk] = i
            votes[i.pk] -= i.cv

        votes = sorted(votes.items(), key=lambda v: v[1], reverse=True)
        if len(votes) == 0:
            return
        is_first = True
        for pk, c in votes:
            f = values[pk]
            if c < 0:
                need_status = FieldValue.STATUS_HIDDEN
            elif is_first or fresh.pk == pk or \
                    fresh.field_name == cls.FIELD_LINK:
                need_status = FieldValue.STATUS_TRUSTED
            else:
                need_status = FieldValue.STATUS_UNTRUSTED

            if f.status != need_status:
                f.status = need_status
                f.status_update_date = timezone.now()
                f.save(update_fields=['status', 'status_update_date'])
            is_first = False


class Vote(Timestamped):
    """
    а также может быть голосованием за правильность или наличие ошибки
    """
    field_value = models.ForeignKey(
        FieldValue, verbose_name='Поле', related_name='votes')
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
        unique_together = ('field_value', 'author_code')

    def __unicode__(self):
        return self.field_value.field_value

    def save(self, *args, **kwargs):
        super(Vote, self).save(*args, **kwargs)
        self.field_value.update_status(
            self.field_value.target_id,
            self.field_value.field_name,
        )
