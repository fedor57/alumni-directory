from django.contrib import admin

from models import (
    Grade,
    Student,
    FieldValue,
    Vote,
)

admin.site.register(Grade)
admin.site.register(Student)
admin.site.register(FieldValue)
admin.site.register(Vote)
