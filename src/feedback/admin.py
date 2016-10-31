# coding=utf-8

from django.contrib import admin

from feedback.models import Person, Veranstaltung, Semester, Einstellung, Mailvorlage, Kommentar, Tutor, BarcodeScanner, BarcodeScannEvent

from django import forms

class PersonAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'email')
    search_fields = ['vorname', 'nachname', 'email', ]

class VeranstaltungAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Stammdaten', {'fields': 
            ['typ', 'name', 'semester', 'lv_nr', 'grundstudium', 'evaluieren',
             'veranstalter', 'link_veranstalter', 
             ]}),
        ('Bestellung', {'fields': ['sprache', 'anzahl', 'verantwortlich', 'ergebnis_empfaenger', 'auswertungstermin',
                                   'freiefrage1', 'freiefrage2', 'kleingruppen', ]}),
    ]
    list_display = ('typ', 'name', 'semester', 'grundstudium', 'evaluieren', 'anzahl', 'sprache', 'veranstalter_list')
    list_display_links = ['name']
    list_filter = ('typ', 'semester', 'grundstudium', 'evaluieren', 'sprache')
    search_fields = ['name']
    filter_horizontal = ('veranstalter', 'ergebnis_empfaenger') #@see http://stackoverflow.com/a/5386871
    readonly_fields = ('link_veranstalter',)

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
                                 ['vorname','nachname','email',
                                  ]}),
                 ('Lehrveranstaltung', {'fields':
                                        ['veranstaltung','nummer','anmerkung'
                                         ]}),
                 ]
    list_display = ('vorname', 'nachname', 'nummer', 'veranstaltung')
    search_fields = ('vorname', 'nachname')
    ordering = ('veranstaltung','nummer')
    
    def render_change_form(self, request, context, *args, **kwargs):
        # Limit Auswahl zum aktuellen Semester
         context['adminform'].form.fields['veranstaltung'].queryset = Veranstaltung.objects.filter(semester=Semester.current())
         return super(TutorAdmin, self).render_change_form(request, context, args, kwargs)  
    
class BarcodeScannEventAdmin(admin.ModelAdmin):
    list_display = ('veranstaltung', 'timestamp', )
    readonly_fields = ('veranstaltung', 'timestamp', )
    
admin.site.register(Person, PersonAdmin)
admin.site.register(Veranstaltung, VeranstaltungAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Einstellung, EinstellungAdmin)
admin.site.register(Mailvorlage, MailvorlageAdmin)
admin.site.register(Kommentar, KommentarAdmin)
admin.site.register(Tutor,TutorAdmin)
admin.site.register(BarcodeScannEvent, BarcodeScannEventAdmin)
admin.site.register(BarcodeScanner)
