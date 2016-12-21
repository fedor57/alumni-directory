from django.conf.urls import url
from views import (
    GradeListView,
    GradeStudentListView,
    StudentDetailView,
)


urlpatterns = [
    url(r'^$', GradeListView.as_view(), name='grade-list'),
    url(r'^(?P<grade_id>[0-9]+)/', GradeStudentListView.as_view(),
        name='student-list'),
    url(r'^students/(?P<pk>[0-9]+)/', StudentDetailView.as_view(),
        name='student-detail'),
]