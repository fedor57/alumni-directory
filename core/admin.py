from django.contrib import admin

from .models import (
    Grade,
    AuthCode,
    Teachers,
    Student,
    FieldValue,
    Vote,
)

admin.site.register(Grade)
admin.site.register(AuthCode)
admin.site.register(Student)
admin.site.register(Teachers)


@admin.register(FieldValue)
class AdminFieldValue(admin.ModelAdmin):
    list_display = ('target', 'field_name', 'field_value', 'status', 'votes')


@admin.register(Vote)
class AdminVote(admin.ModelAdmin):
    def field_value(self):
        return self.field_value.field_value

    def field_target(self):
        return self.field_value.target

    list_display = (field_target, field_value, 'author_code', 'value')
