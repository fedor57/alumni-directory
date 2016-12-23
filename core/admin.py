from django.contrib import admin

from models import (
    Grade,
    AuthCode,
    Student,
    FieldValue,
    Vote,
)

admin.site.register(Grade)
admin.site.register(AuthCode)
admin.site.register(Student)
admin.site.register(FieldValue)
admin.site.register(Vote)
