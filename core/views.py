import itertools
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.http import Http404
from models import Grade, Student


class GradeListView(ListView):
    model = Grade


class GradeStudentListView(ListView):
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


class StudentDetailView(DetailView):
    model = Student

    def get_context_data(self, **kwargs):
        context_data = super(StudentDetailView, self).get_context_data(**kwargs)

        grouped_modifications_iterator = itertools.groupby(
            self.object.modifications.order_by('field_name'),
            lambda modification: modification.field_name
        )
        context_data['grouped_modifications'] = {
            field_name: list(field_values)
            for field_name, field_values
            in grouped_modifications_iterator
        }

        return context_data





