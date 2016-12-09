# coding=utf-8

from django.contrib import admin

from feedback.models import Person, Veranstaltung, Semester, Einstellung, \
    Mailvorlage, Kommentar, Tutor, BarcodeScanner, BarcodeScannEvent, BarcodeAllowedState
from feedback.models.base import Log


def status_angelegt(modeladmin, request, queryset):
    queryset.update(status=100)
    for veranstaltung in queryset:
        veranstaltung.log(True, False)
status_angelegt.short_description = 'Status: angelegt'


def status_gedruckt(modeladmin, request, queryset):
    queryset.update(status=600)
    for veranstaltung in queryset:
        veranstaltung.log(True, False)
status_gedruckt.short_description = 'Status: gedruckt'


def status_versandt(modeladmin, request, queryset):
    queryset.update(status=700)
    for veranstaltung in queryset:
        veranstaltung.log(True, False)
status_versandt.short_description = 'Status: versandt'


def status_boegen_eingegangen(modeladmin, request, queryset):
    queryset.update(status=800)
    for veranstaltung in queryset:
        veranstaltung.log(True, False)
status_boegen_eingegangen.short_description = 'Status: eingegangen'


def status_boegen_gescannt(modeladmin, request, queryset):
    queryset.update(status=900)
    for veranstaltung in queryset:
        veranstaltung.log(True, False)
status_boegen_gescannt.short_description = 'Status: gescannt'


class PersonAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'email')
    search_fields = ['vorname', 'nachname', 'email', ]


class VeranstaltungAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Stammdaten', {'fields':
                            ['typ', 'name', 'semester', 'status', 'lv_nr', 'grundstudium', 'evaluieren',
                             'veranstalter', 'link_veranstalter',
                             ]}),
        ('Bestellung', {'fields': ['sprache', 'anzahl', 'verantwortlich', 'ergebnis_empfaenger', 'auswertungstermin',
                                   'freiefrage1', 'freiefrage2', 'kleingruppen', ]}),
    ]
    list_display = ('typ', 'name', 'semester', 'grundstudium', 'evaluieren', 'anzahl',
                    'sprache', 'status', 'veranstalter_list')
    list_display_links = ['name']
    list_filter = ('typ', 'semester', 'grundstudium', 'evaluieren', 'sprache')
    search_fields = ['name']
    filter_horizontal = ('veranstalter', 'ergebnis_empfaenger')  # @see http://stackoverflow.com/a/5386871
    readonly_fields = ('link_veranstalter',)


class VeranstaltungStatus(Veranstaltung):
    class Meta:
        verbose_name = 'Status der Veranstaltung'
        verbose_name_plural = 'Status der Veranstaltungen'
        proxy = True


class VeranstaltungStatusAdmin(admin.ModelAdmin):
    list_display = ('lv_nr', 'name', 'status')
    list_display_links = ['name']
    list_filter = ('lv_nr', 'name', 'status')
    search_fields = ['name']
    actions = [
        status_angelegt, status_gedruckt, status_versandt, status_boegen_eingegangen, status_boegen_gescannt
    ]


class LogAdmin(admin.ModelAdmin):
    list_display = ('veranstaltung', 'timestamp', 'status', 'verursacher', 'interface')
    list_filter = ('veranstaltung',)
    ordering = ('timestamp',)


class SemesterAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'sichtbarkeit', 'fragebogen')
    list_filter = ('sichtbarkeit', 'fragebogen')
    ordering = ('-semester',)


class EinstellungAdmin(admin.ModelAdmin):
    list_display = ('name', 'wert')
    list_editable = ('wert',)


class MailvorlageAdmin(admin.ModelAdmin):
    list_display = ('subject',)


class KommentarAdmin(admin.ModelAdmin):
    list_display = ('typ', 'name', 'semester', 'autor')
    list_display_links = ('name',)


class TutorAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Stammdaten', {'fields':
                            ['vorname', 'nachname', 'email',
                             ]}),
        ('Lehrveranstaltung', {'fields':
                                   ['veranstaltung', 'nummer', 'anmerkung'
                                    ]}),
    ]
    list_display = ('vorname', 'nachname', 'nummer', 'veranstaltung')
    search_fields = ('vorname', 'nachname')
    ordering = ('veranstaltung', 'nummer')

    def render_change_form(self, request, context, *args, **kwargs):
        # Limit Auswahl zum aktuellen Semester
        context['adminform'].form.fields['veranstaltung'].queryset = Veranstaltung.objects.filter(
            semester=Semester.current())
        return super(TutorAdmin, self).render_change_form(request, context, args, kwargs)


class BarcodeScannEventAdmin(admin.ModelAdmin):
    list_display = ('veranstaltung', 'timestamp',)
    readonly_fields = ('veranstaltung', 'timestamp',)


class BarcodeAllowedStateInline(admin.TabularInline):
    model = BarcodeAllowedState


class BarcodeScannerAdmin(admin.ModelAdmin):
    inlines = [
        BarcodeAllowedStateInline,
    ]
    list_display = ('token', 'description')


admin.site.register(Person, PersonAdmin)
admin.site.register(Veranstaltung, VeranstaltungAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Einstellung, EinstellungAdmin)
admin.site.register(Mailvorlage, MailvorlageAdmin)
admin.site.register(Kommentar, KommentarAdmin)
admin.site.register(Tutor, TutorAdmin)
admin.site.register(BarcodeScannEvent, BarcodeScannEventAdmin)
admin.site.register(BarcodeScanner, BarcodeScannerAdmin)
admin.site.register(VeranstaltungStatus, VeranstaltungStatusAdmin)
admin.site.register(Log, LogAdmin)
