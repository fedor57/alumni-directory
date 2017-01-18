# coding=utf-8
from __future__ import unicode_literals

from django import forms
from .models import Grade, Student, FieldValue, Vote


class StudentCreateForm(forms.ModelForm):
    name = forms.CharField(label='Фамилия Имя')
    graduation_year = forms.IntegerField(label='Год выпуска')
    grade_letter = forms.CharField(label='Буква класса')
    auth_code = forms.CharField(label='Код авторизации', required=False)

    class Meta:
        model = Student
        fields = ('name', 'graduation_year', 'grade_letter', 'auth_code')

    # TODO: add validation

    def save(self, **kwargs):
        instance = super(StudentCreateForm, self).save(commit=False)

        instance.main_grade, grade_created = Grade.objects.get_or_create(
            graduation_year=self.cleaned_data['graduation_year'],
            letter=self.cleaned_data['grade_letter'],
        )
        instance.save()
        return instance


class FieldValueForm(forms.ModelForm):
    field_name = forms.ChoiceField(label='Тип правки',
                                   choices=FieldValue.EDITABLE_FIELDS)
    field_value = forms.CharField(label='Значение правки')
    auth_code = forms.CharField(label='Код авторизации', required=False)

    class Meta:
        model = FieldValue
        fields = ('field_name', 'field_value', 'auth_code')

    # def clean_author_code(self):
    #     TODO: validate
        # return self.cleaned_data['author_code']


class VoteForm(forms.ModelForm):
    auth_code = forms.CharField(label='Код авторизации', required=False)

    class Meta:
        model = Vote
        fields = ('auth_code',)
