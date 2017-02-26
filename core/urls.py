from django.conf.urls import url
from .views import (
    AlphabetView,
    GradeListView,
    StudentListView,
    SuggestListView,
    StudentDetailView,
    StudentCreateView,
    FieldValueCreateView,
    handle_vote,
    SendMailView,
    auth_code_login,
    QAView,
    FeedView,
)


urlpatterns = [
    url(r'^$', GradeListView.as_view(), name='grade-list'),
    url(r'^alphabet/$', AlphabetView.as_view(), name='alphabet-list'),
    url(r'^api/login$', auth_code_login, name='api-login'),
    url(r'^suggest/$', SuggestListView.as_view(), name='suggest-list'),
    url(r'^students/$', StudentListView.as_view(), name='student-list'),
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
    url(r'^qa/$', QAView.as_view(), name='qa'),
    url(r'^feed/$', FeedView.as_view(), name='feed'),
]
