# coding=utf-8
from __future__ import unicode_literals

from collections import OrderedDict

from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
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
    profile = models.CharField('Тип класса', max_length=50, blank=True, null=True)
    letter = models.CharField('Буква выпускного класса', max_length=1)
    graduation_year = models.PositiveSmallIntegerField('Год выпуска')

    class Meta:
        verbose_name = 'класс'
        verbose_name_plural = 'классы'
        unique_together = ('letter', 'graduation_year')
        ordering = ('-graduation_year', 'letter')

    def __unicode__(self):
        return '%s%s' % (self.graduation_year, self.letter)


class Student(Timestamped):
    """
    Выпускник
    """
    name = models.CharField(max_length=200)
    main_grade = models.ForeignKey(Grade)
    creator_code = models.ForeignKey('AuthCode', blank=True, null=True)
    import_date = models.DateTimeField(null=True, blank=True)

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
        max_length=100
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    owner = models.ForeignKey(Student, null=True)
    cross_name = models.CharField(max_length=200)
    updated_at = models.DateTimeField('Дата обновления данных', auto_now=True)
    revoked_at = models.DateTimeField('Дата отзыва', null=True, blank=True)
    trust_level = models.FloatField('Уровень доверия', default=1)

    class Meta:
        verbose_name = 'код авторизации'
        verbose_name_plural = 'коды авторизации'

    objects = AuthCodeManager()

    def __unicode__(self):
        return '%s (%s)' % (self.code, self.owner)


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
    FIELD_PROFESSION = 'profession'
    FIELD_DEGREE = 'degree'
    FIELD_COMPANY = 'company'
    FIELD_LINK = 'link'
    FIELD_SOCIAL_VK = 'social_vk'
    FIELD_SOCIAL_FB = 'social_fb'
    FIELD_SOCIAL_LI = 'social_li'
    FIELD_GRADE = 'grade'
    FIELD_DEATH_YEAR = 'death_year'
    EDITABLE_FIELDS = (
        (FIELD_NAME, 'Изменения фамилии / имени',
         'Если изменилась фамилия или имя после окончания школы, добавьте только измененную часть, она будет '
         'отображаться в скобках'),
        (FIELD_EMAIL, 'Email',
         'Адрес e-mail можно добавлять только для себя или с согласия владельца. E-Mail не будет показан, но на него '
         'можно будет отправить сообщение через форму с просьбой связаться'),
        (FIELD_CITY, 'Город',
         'Укажите город, в котором сейчас живет выпускник большую часть времени. Используйте русский язык, с большой '
         'буквы. Если это, по-прежнему, Москва, то указывать город не обязательно. Если город не известен широкой '
         'публике, напишите страну через запятую'),
        (FIELD_PROFESSION, 'Профессия / должность',
         'Укажите основную профессию или род занятий выпускника'),
        (FIELD_DEGREE, 'Учёная степень', 'Укажите учёную степень выпускника'),
        (FIELD_COMPANY, 'Компания / ВУЗ',
         'Укажите основное место работы или учебы выпусника, одновременно указывать не нужно'),
        (FIELD_LINK, 'Домашняя страница',
         'Если у выпускника есть личная страница с информацией о нем, биографией, контактами, укажите ее здесь'),
        (FIELD_SOCIAL_FB, 'Facebook', 'Укажите адрес профиля в Facebook, если выпусник им пользуется'),
        (FIELD_SOCIAL_VK, 'ВКонтакте', 'Укажите адрес профиля ВКонтакте, если выпусник им пользуется'),
        (FIELD_SOCIAL_LI, 'LinkedIn', 'Укажите адрес профиля LinkedIn, если выпусник им пользуется'),
        (FIELD_GRADE, 'Учился также в классе',
         'Выпускники, в первую очередь, приписываются к классу, с которым они закончили школу или из которого из нее '
         'ушли. Если они успели поучиться в другом классе, это можно указать дополнительно. Для указания класса '
         'используйте год выпуска класса, а не год, когда выпускник там учился'),
        (FIELD_DEATH_YEAR, 'Год смерти', ''),
    )
    URL_FIELDS = (
        FIELD_LINK,
        FIELD_SOCIAL_FB,
        FIELD_SOCIAL_VK,
        FIELD_SOCIAL_LI,
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
        'Дата обновления статуса', auto_now_add=True)
    votes = models.FloatField(default=0)

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
        ordering = ('-timestamp',)
        # Плохо работает для анонимусов
        # unique_together = ('field_value', 'author_code', 'value')

    def __unicode__(self):
        return self.field_value.field_value


class Teachers(models.Model):
    grade = models.ForeignKey(Grade, related_name='teachers')
    role = models.CharField(max_length=512)
    content = models.TextField()
    torder = models.SmallIntegerField()

    class Meta:
        verbose_name = 'учителя'
        verbose_name_plural = 'учителя'
        ordering = ('torder',)

    def __unicode__(self):
        return ' '.join([self.role, self.content])
