from django.conf.urls import url
from .views import (
    GradeListView,
    GradeStudentListView,
    SearchStudentListView,
    StudentDetailView,
    StudentCreateView,
    FieldValueCreateView,
    handle_vote,
    SendMailView,
    auth_code_login,
)


urlpatterns = [
    url(r'^$', GradeListView.as_view(), name='grade-list'),
    url(r'^api/login$', auth_code_login, name='api-login'),
    url(r'^search/$', SearchStudentListView.as_view(),
        name='search-list'),
    url(r'^(?P<grade_id>[0-9]+)/$', GradeStudentListView.as_view(),
        name='student-list'),
    url(r'^students/(?P<pk>[0-9]+)/$', StudentDetailView.as_view(),
        name='student-detail'),
    url(r'^students/add/$', StudentCreateView.as_view(),
        name='student-create'),
    url(r'^(?P<grade_id>[0-9]+)/students/add/$', StudentCreateView.as_view(),
        name='grade-student-create'),
    url(r'^students/(?P<pk>[0-9]+)/add_value/$', FieldValueCreateView.as_view(),
        name='student-value-create'),
    url(r'^fields/(?P<pk>[0-9]+)/(?P<vote_type>\w+)/$', handle_vote,
        name='field-vote'),
    url(r'^sendmail/(?P<pk>[0-9]+)/$', SendMailView.as_view(),
        name='field-sendmail'),
]
