# coding=utf-8
from __future__ import unicode_literals
import itertools
import operator

from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.http import \
    Http404, HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.urls import reverse

from .models import Grade, Student, FieldValue, AuthCode, Vote
from .forms import StudentCreateForm, FieldValueForm, SendMailForm


def auth_code_login(request):
    if request.method == 'POST':
        request.session['auth_code'] = request.POST.get('auth_code', '')
        return HttpResponse(request.POST.get('auth_code', ''))
    if 'auth_code' in request.session:
        return HttpResponse()
    return HttpResponse(status=403)


class AlphabetView(TemplateView):
    template_name = 'core/alphabet.jade'

    def get_context_data(self, **kwargs):
        data = super(AlphabetView, self).get_context_data(**kwargs)
        data['characters'] = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЫЭЮЯ'
        return data


class GradeListView(ListView):
    model = Grade
    template_name = 'core/grade_list.jade'

    def get_context_data(self, **kwargs):
        data = super(GradeListView, self).get_context_data(**kwargs)
        qs = data['object_list']
        result = []
        for g, i in itertools.groupby(qs, key=lambda x: x.graduation_year):
            result.append((g, list(i)))
        data['grades'] = result
        return data


class BaseStudentListView(ListView):
    model = Student

    def get_queryset(self):
        qs = super(BaseStudentListView, self).get_queryset()
        qs = qs.prefetch_related('modifications')
        return qs


class StudentListView(BaseStudentListView):
    template_name = 'core/student_list.jade'
    paginate_by = 100

    def get_paginate_by(self, queryset):
        if self.year:
            return None
        elif self.grade_id:
            return None
        elif self.char:
            return None
        return super(StudentListView, self).get_paginate_by(queryset)

    def get(self, request, *args, **kwargs):
        self.grade_id = self.request.GET.get('grade_id')
        if self.grade_id and not Grade.objects.filter(id=self.grade_id).exists():
            raise Http404()
        self.year = self.request.GET.get('year')
        self.char = self.request.GET.get('char')
        return super(StudentListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(StudentListView, self).get_queryset()
        query = self.request.GET.get('query')
        if query:
            q = Q(modifications__field_value__icontains=query)
            q &= ~Q(modifications__status=FieldValue.STATUS_DELETED)
            q |= Q(name__icontains=query)
            qs = qs.filter(q).distinct()
        elif self.char:
            qs = qs.filter(name__startswith=self.char)
        elif self.grade_id:
            qs = qs.filter(main_grade_id=self.grade_id)
        elif self.year:
            qs = qs.filter(main_grade__graduation_year=self.year)
        if query or self.year:
            qs = qs.order_by('-main_grade__graduation_year', 'main_grade__letter', 'name')
        return qs.prefetch_related('main_grade')

    def get_context_data(self, **kwargs):
        context_data = super(StudentListView, self).get_context_data(**kwargs)
        if self.grade_id:
            context_data['grade'] = Grade.objects.get(id=self.grade_id)
        context_data['year'] = self.year
        context_data['char'] = self.char
        res = []
        qs = context_data['object_list']
        if self.char:
            for g, i in itertools.groupby(qs, key=lambda x: x.name[0]):
                l = list(i)
                res.append(('Буква ' + g.upper(), l))
            context_data['show_grade'] = True
        else:
            for g, i in itertools.groupby(qs, key=lambda s: s.main_grade.pk):
                l = list(i)
                g = l[0].main_grade
                res.append((g, l))
        context_data['object_list'] = res
        return context_data


class SuggestListView(ListView):
    model = FieldValue

    def get_queryset(self):
        query = self.request.GET.get('query', '')
        self.query = query.split()

        qs = super(SuggestListView, self).get_queryset()

        if self.query:
            qu = [
                ~Q(status=FieldValue.STATUS_DELETED),
                ~Q(field_name=FieldValue.FIELD_EMAIL),
                ~Q(field_name=FieldValue.FIELD_SOCIAL_FB),
                ~Q(field_name=FieldValue.FIELD_SOCIAL_VK),
            ]

            for q in self.query:
                qu.append(Q(field_value__icontains=q))

            qu = reduce(operator.and_, qu)

            qs = qs.filter(qu) \
                .values_list('field_value', flat=True) \
                .distinct()
        else:
            qs = qs.none()

        return qs

    def render_to_response(self, context, **response_kwargs):
        if self.query:
            data = list(context['object_list'])
        else:
            data = []

        if self.query and self.request.GET.get('students') in ('1', 'true'):
            qu = []

            for q in self.query:
                qu.append(Q(name__icontains=q))

            qu = reduce(operator.and_, qu)

            qs = Student.objects.filter(qu) \
                .values_list('name', flat=True) \
                .distinct()[:30]

            data = list(qs) + data
        return JsonResponse({
            'data': data,
        })


class StudentDetailView(DetailView):
    template_name = 'core/student_detail.jade'
    model = Student

    def get_context_data(self, **kwargs):
        context_data = super(StudentDetailView, self).get_context_data(**kwargs)

        grouped_modifications_iterator = itertools.groupby(
            self.object.modifications.order_by('field_name'),
            lambda modification: modification.field_name
        )
        order = [i[0] for i in FieldValue.STATUS_CHOICES]
        key = lambda x: (order.index(x.status), -x.votes)
        modifications = dict(
            (field_name, sorted(field_values, key=key))
            for field_name, field_values
            in grouped_modifications_iterator
        )
        context_data['grouped_modifications'] = modifications
        context_data['grade'] = self.object.main_grade
        context_data['field_types'] = FieldValue.EDITABLE_FIELDS
        return context_data


class StudentCreateView(CreateView):
    template_name = 'core/student_form.jade'
    model = Student
    form_class = StudentCreateForm

    def get_initial(self):
        """
        Если id класса есть в url, добавляем год и букву в initial
        """
        initial = super(StudentCreateView, self).get_initial()
        if 'grade_id' in self.kwargs:
            try:
                grade = Grade.objects.get(id=self.kwargs.get('grade_id'))
            except Grade.objects.DoesNotExist:
                pass
            else:
                initial['graduation_year'] = grade.graduation_year
                initial['grade_letter'] = grade.letter
        return initial

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # Привязываем код авторизации и создаем для него запись в таблице кодов
        auth_code = self.request.session.get('auth_code')
        if auth_code:
            author_code = AuthCode.objects.get_by_code(auth_code)
            self.object.author_code = author_code

        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class FieldValueCreateView(CreateView):
    template_name = 'core/fieldvalue_form.jade'
    model = FieldValue
    form_class = FieldValueForm

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # Привязываем правку к выпускнику по id из урла
        student_id = self.kwargs.get('pk')
        exists = FieldValue.objects.filter(
            target_id=student_id,
            field_name=self.object.field_name,
            field_value__iexact=self.object.field_value,
        ).exists()
        if exists:
            return HttpResponseRedirect(self.get_success_url())
        try:
            self.object.target = Student.objects.get(id=student_id)
        except Student.objects.DoesNotExist:
            return Http404()

        # Привязываем код авторизации и создаем для него запись в таблице кодов
        auth_code = self.request.session.get('auth_code')
        if auth_code:
            auth_code = AuthCode.objects.get_by_code(auth_code)
            self.object.author_code = auth_code

        self.object.save()
        vote = Vote(field_value=self.object,
                    value=Vote.VOTE_ADDED)
        if auth_code:
            vote.author_code = auth_code
        vote.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('student-detail', args=[self.kwargs['pk']])


def handle_vote(request, pk, vote_type):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    obj = Vote()
    
    # Идентификатор значения FieldValue
    try:
        obj.field_value = FieldValue.objects.get(id=pk)
    except FieldValue.objects.DoesNotExist:
        return Http404()

    # Тип голоса FieldValue
    if vote_type in (Vote.VOTE_UP, Vote.VOTE_DOWN, Vote.VOTE_TO_DEL):
        obj.value = vote_type
    else:
        return HttpResponseBadRequest()

    # Привязываем код авторизации и создаем для него запись в таблице кодов
    auth_code = request.session.get('auth_code')
    if auth_code:
        author_code = AuthCode.objects.get_by_code(auth_code)
        obj.author_code = author_code

    obj.save()
    return HttpResponseRedirect(
        reverse('student-detail', kwargs={
            'pk': str(obj.field_value.target_id)}))


class SendMailView(CreateView):
    template_name = 'core/sendmail_form.jade'
    model = FieldValue
    form_class = SendMailForm

    def form_valid(self, form):
        # Идентификатор FieldValue c email
        try:
            email = self.get_object().field_value
        except FieldValue.objects.DoesNotExist:
            return Http404()

        send_mail(
            form.cleaned_data['subject'],
            form.cleaned_data['message'],
            None,
            [email],
        )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('student-detail', kwargs={
            'pk': str(self.get_object().target_id)
        })
