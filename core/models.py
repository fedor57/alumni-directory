# coding=utf-8
from __future__ import unicode_literals

from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist


class Timestamped(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Grade(models.Model):
    """
    Класс
    """
    letter = models.CharField(max_length=1)
    graduation_year = models.PositiveSmallIntegerField()  # TODO: вылидировать год
    # TODO: добавить читаемый id

    class Meta:
        verbose_name = 'класс'
        verbose_name_plural = 'классы'
        unique_together = ('letter', 'graduation_year')

    def __unicode__(self):
        return '%s "%s"' % (self.graduation_year, self.letter)


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
    updated_at = models.DateTimeField('Дата обновления данных')
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
    status_update_date = models.DateTimeField('Дата обновления статуса')

    objects = FieldValueManager()

    class Meta:
        verbose_name = 'правка'
        verbose_name_plural = 'правки'

    # TODO: при сохранении проверять unique_together('target', 'author', 'field_name')

    def __unicode__(self):
        return '%s _ %s' % (self.target, self.get_field_name_display())


class Vote(Timestamped):
    """
    а также может быть голосованием за правильность или наличие ошибки
    """
    field_value = models.ForeignKey(
        FieldValue, verbose_name='Поле', related_name='votes')
    author_code = models.ForeignKey(
        AuthCode, verbose_name='Код автора голоса', related_name='votes')

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

    # TODO: при добавлении голоса обновлять статус поля (self.field_name.status)

    def __unicode__(self):
        return self.field_value
