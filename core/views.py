# coding=utf-8
import itertools

from django.core.mail import send_mail
from django.db.models import Q
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.http import \
    Http404, HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.urls import reverse

from models import Grade, Student, FieldValue, AuthCode, Vote
from forms import StudentCreateForm, FieldValueForm, SendMailForm


def auth_code_login(request):
    if request.method == 'POST':
        request.session['auth_code'] = request.POST.get('auth_code', '')
        return HttpResponse(request.POST.get('auth_code', ''))
    if 'auth_code' in request.session:
        return HttpResponse()
    return HttpResponse(status=403)


class GradeListView(ListView):
    model = Grade
    template_name = 'core/grade_list.jade'


class GradeStudentListView(ListView):
    template_name = 'core/student_list.jade'
    model = Student

    def get(self, request, *args, **kwargs):
        if not Grade.objects.filter(id=self.kwargs.get('grade_id')).exists():
            raise Http404()
        return super(GradeStudentListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(GradeStudentListView, self).get_queryset()
        return qs.filter(main_grade_id=self.kwargs.get('grade_id'))

    def get_context_data(self, **kwargs):
        context_data = super(GradeStudentListView, self).get_context_data(**kwargs)
        context_data['grade'] = Grade.objects.get(id=self.kwargs.get('grade_id'))
        return context_data


class SearchStudentListView(ListView):
    template_name = 'core/search_list.jade'
    model = Student

    def get_queryset(self):
        query = self.request.GET.get('query')
        qs = super(SearchStudentListView, self).get_queryset()
        if query:
            q = Q(modifications__field_value__icontains=query)
            q &= ~Q(modifications__status=FieldValue.STATUS_DELETED)
            q |= Q(name__icontains=query)
            qs = qs.filter(q).distinct()[:100]
        else:
            qs = qs.none()
        return qs


class StudentDetailView(DetailView):
    template_name = 'core/student_detail.jade'
    model = Student

    def get_context_data(self, **kwargs):
        context_data = super(StudentDetailView, self).get_context_data(**kwargs)

        grouped_modifications_iterator = itertools.groupby(
            self.object.modifications.order_by('field_name'),
            lambda modification: modification.field_name
        )
        modifications = dict(
            (field_name, list(field_values))
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
        return reverse('student-detail', args=[str(self.kwargs['pk'])])


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
        fv_id = self.kwargs.get('pk')
        try:
            email = FieldValue.objects.get(id=fv_id).field_value
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
            'pk': str(self.object.field_value.target_id)
        })
