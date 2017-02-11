from django.contrib import admin

from .models import (
    Grade,
    AuthCode,
    Teachers,
    Student,
    FieldValue,
    Vote,
)

admin.site.register(AuthCode)


class InlineTeacher(admin.TabularInline):
    model = Teachers


class InlineStudent(admin.TabularInline):
    model = Student
    exclude = ('creator_code', )
    readonly_fields = ('import_date', )


@admin.register(Grade)
class AdminGrade(admin.ModelAdmin):
    list_display = ('graduation_year', 'letter')
    inlines = [InlineTeacher, InlineStudent]


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
