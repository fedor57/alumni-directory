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


@admin.register(Student)
class AdminStudent(admin.ModelAdmin):
    ordering = ('name',)
    search_fields = ('name', 'main_grade__graduation_year', 'main_grade__letter')
    readonly_fields = ('timestamp',)


@admin.register(Grade)
class AdminGrade(admin.ModelAdmin):
    list_display = ('graduation_year', 'letter')
    inlines = [InlineTeacher, InlineStudent]


@admin.register(FieldValue)
class AdminFieldValue(admin.ModelAdmin):
    ordering = ('target__name',)
    list_display = ('target', 'field_name', 'field_value', 'status', 'votes')
    search_fields = ('target__name', 'target__main_grade__graduation_year', 'field_name', 'field_value')
    readonly_fields = ('timestamp',)


@admin.register(Vote)
class AdminVote(admin.ModelAdmin):
    def field_name(self):
        return self.field_value.field_name

    def field_value(self):
        return self.field_value.field_value

    def field_target(self):
        return self.field_value.target

    ordering = ('field_value__target__name',)
    list_display = (field_target, field_name, field_value, 'author_code', 'value')
    search_fields = ('field_value__target__name', 'field_value__field_name', 'field_value__field_value')
    list_filter = ('value',)
    readonly_fields = ('timestamp',)
