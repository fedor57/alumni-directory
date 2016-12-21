# coding=utf-8

from django.db import models


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
        unique_together = ('letter', 'graduation_year')

    def __unicode__(self):
        return u'%s "%s"' % (self.graduation_year, self.letter)


class Student(Timestamped):
    """
    Выпускник
    """
    name = models.CharField(max_length=200)
    main_grade = models.ForeignKey(Grade)
    # TODO: заменить auth_code моделью со статусом кода
    auth_code = models.CharField(max_length=100, blank=True)
    creator = models.ForeignKey('self', related_name='students_created',
                                blank=True, null=True)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.main_grade)


class FieldValueManager(models.Manager):
    def visible(self):
        return self.exclude(status='hidden')


class FieldValue(Timestamped):
    """
    Каждая правка предлагает добавить значение поля
    """
    # Типы правок (field_name)
    EDITABLE_FIELDS = (
        ('name', u'Информация об изменении имени/фамилии'),
        ('email', u'Email, который не отображается, '
                  u'но на который можно написать через форму'),
        ('city', u'Город'),
        ('company', u'Компания'),
        ('link', u'Ссылка'),
        ('extra_grade', u'Класс'),
    )
    STATUS_CHOICES = (
        ('trusted', u'Уверенное значение'),
        ('untrusted', u'Под сомнением'),
        ('suspicious', u'Подозрительное'),
        ('hidden', u'Скрытое'),
    )

    target = models.ForeignKey(Student, related_name='modifications',
                               help_text='Student to modify')
    author = models.ForeignKey(Student, related_name='modify_activity',
                               blank=True, null=True)
    field_name = models.CharField(choices=EDITABLE_FIELDS, max_length=20,
                                  help_text='Name of field in student data')
    field_value = models.CharField(max_length=200)
    status = models.CharField(choices=STATUS_CHOICES, default='trusted', max_length=20)

    objects = FieldValueManager()

    # TODO: при сохранении проверять unique_together('target', 'author', 'field_name')

    def __unicode__(self):
        return u'%s _ %s' % (self.target, self.get_field_name_display())


class Vote(Timestamped):
    """
    а также может быть голосованием за правильность или наличие ошибки
    """
    field_value = models.ForeignKey(FieldValue, related_name='votes')
    author = models.ForeignKey(Student, related_name='votes')
    value = models.BooleanField(help_text='True is upvote, False is downvote')

    class Meta:
        unique_together = ('field_value', 'author')

    # TODO: при добавлении голоса обновлять статус поля (self.field_name.status)

    def __unicode__(self):
        return self.field_value
