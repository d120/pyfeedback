# coding=utf-8

from django.contrib import admin
from django import forms
from django.http.response import HttpResponseRedirect
from django.shortcuts import render

from feedback.models import Person, Veranstaltung, Semester, Einstellung, \
    Mailvorlage, Kommentar, Tutor, BarcodeScanner, BarcodeScannEvent, BarcodeAllowedState
from feedback.models.base import Log, Fachgebiet, FachgebietEmail


class PersonAdmin(admin.ModelAdmin):
    """Admin View für Personen"""
    list_display = ('__str__', 'email', 'fachgebiet')
    search_fields = ['vorname', 'nachname', 'email', ]
    list_filter = ('fachgebiet',)

    class FachgebietZuweisenForm(forms.Form):
        """Form für die Zuweisung von einem Fachgebiet für eine Person."""
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)

    def assign_fachgebiet_action(self, request, queryset):
        """Definiert eine Admin-Action für die Fachgebietzuweisung."""
        form = None
        suggestion_list = []

        for p in queryset:
            proposed_fachgebiet = FachgebietEmail.get_fachgebiet_from_email(p.email)
            suggestion_list.append((p, proposed_fachgebiet))

        if any(s in request.POST for s in ('apply', 'save')):
            form = self.FachgebietZuweisenForm(request.POST)

            if form.is_valid():
                selected_persons = request.POST.getlist("selectedPerson")
                for person in queryset:
                    person_id_str = str(person.id)
                    if person_id_str in selected_persons:
                        proposed_fachgebiet_id = request.POST.get("fachgebiet_" + person_id_str, 0)
                        if int(proposed_fachgebiet_id) > 0:
                            proposed_fachgebiet = Fachgebiet.objects.get(id=proposed_fachgebiet_id)
                            person.fachgebiet = proposed_fachgebiet
                            person.save()
                            suggestion_list = [(x, y) for x, y in suggestion_list if x is not person]

                self.message_user(request, "Fachgebiete erfolgreich zugewiesen.")

                if ('save' in request.POST) or not suggestion_list:
                    return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = self.FachgebietZuweisenForm(initial={
                '_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
            })

        return render(request, 'admin/fachgebiet.html', {'data': suggestion_list, 'fachgebiet': form, })

    assign_fachgebiet_action.short_description = "Einem Fachgebiet zuweisen"
    actions = [assign_fachgebiet_action]


class LogInline(admin.TabularInline):
    """Admin View für Log"""
    model = Log
    readonly_fields = ('veranstaltung', 'user', 'scanner', 'timestamp', 'status', 'interface')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class VeranstaltungAdmin(admin.ModelAdmin):
    """Admin View für Veranstaltung"""
    fieldsets = [
        ('Stammdaten', {'fields':
                            ['typ', 'name', 'semester', 'status', 'lv_nr', 'grundstudium', 'evaluieren',
                             'veranstalter', 'link_veranstalter',
                             ]}),
        ('Bestellung', {'fields': ['sprache', 'anzahl', 'verantwortlich', 'ergebnis_empfaenger', 'primaerdozent',
                                   'auswertungstermin', 'freiefrage1', 'freiefrage2', 'kleingruppen', ]}),
    ]
    list_display = ('typ', 'name', 'semester', 'grundstudium', 'evaluieren', 'anzahl',
                    'sprache', 'status', 'veranstalter_list')
    list_display_links = ['name']
    list_filter = ('typ', 'semester', 'status', 'grundstudium', 'evaluieren', 'sprache')
    search_fields = ['name']
    filter_horizontal = ('veranstalter', 'ergebnis_empfaenger')  # @see http://stackoverflow.com/a/5386871
    readonly_fields = ('link_veranstalter',)
    inlines = [LogInline, ]

    def save_model(self, request, obj, form, change):
        """Definiert eine Post-Save Operation."""
        super(VeranstaltungAdmin, self).save_model(request, obj, form, change)
        for changed_att in form.changed_data:
            # Wenn sich der Status ändert, wird es geloggt.
            if changed_att == "status":
                obj.log(request.user)

    class StatusAendernForm(forms.Form):
        """Definiert eine Form für Änderung einen Status'."""
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        status = forms.ChoiceField(choices=Veranstaltung.STATUS_CHOICES)

    def status_aendern_action(self, request, queryset):
        """Beschreibt eine Admin-Action für die Statusänderung."""
        form = None

        if 'apply' in request.POST:
            form = self.StatusAendernForm(request.POST)

            if form.is_valid():
                status = form.cleaned_data['status']

                queryset.update(status=status)
                for veranstaltung in queryset:
                    veranstaltung.log(request.user)

                self.message_user(request, "Status erfolgreich geändert.")
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = self.StatusAendernForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})

        return render(request, 'admin/status_aendern.html', {'veranstaltungen': queryset, 'status': form, })

    status_aendern_action.short_description = "Ändere den Status einer Veranstaltung"

    class KeineEvaluationForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)

    def keine_evaluation_action(self, request, queryset):
        """Beschreibt eine Admin-Action für die Option keine Evaluation."""
        form = None

        if 'apply' in request.POST:     #Dieser Teil reicht bereits zum ändern aus. In diesem Fall können auch Zeile 146-149 gelöscht werden (Kein Bestätigungsfenster erscheint.
            queryset.update(status=Veranstaltung.STATUS_KEINE_EVALUATION_FINAL)
            queryset.update(evaluieren=False)
            for veranstaltung in queryset:
                veranstaltung.log(request.user)

            self.message_user(request, "Keine Evaluation erfolgreich gesetzt.")
            return HttpResponseRedirect(request.get_full_path())
            #nach dem return landet Python in status_aendern_action
        if not form:
            form = self.KeineEvaluationForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render(request, 'admin/keine_evaluation.html', {'veranstaltungen': queryset, 'status':form, })

    keine_evaluation_action.short_description = "Keine Evaluation für diese Veranstaltung"

    actions = [status_aendern_action,keine_evaluation_action]


class SemesterAdmin(admin.ModelAdmin):
    """Admin View für Semester"""
    list_display = ('__str__', 'sichtbarkeit', 'fragebogen')
    list_filter = ('sichtbarkeit', 'fragebogen')
    ordering = ('-semester',)


class EinstellungAdmin(admin.ModelAdmin):
    """Admin View für Einstellung"""
    list_display = ('name', 'wert')
    list_editable = ('wert',)


class MailvorlageAdmin(admin.ModelAdmin):
    """Admin View für Mailvorlage"""
    list_display = ('subject',)


class KommentarAdmin(admin.ModelAdmin):
    """Admin View für Kommentar"""
    list_display = ('typ', 'name', 'semester', 'autor')
    list_display_links = ('name',)


class TutorAdmin(admin.ModelAdmin):
    """Admin View für Tutor"""
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
    """Admin View für BarcodeScannEvent"""
    list_display = ('veranstaltung', 'timestamp',)
    readonly_fields = ('veranstaltung', 'timestamp',)


class BarcodeAllowedStateInline(admin.TabularInline):
    """Admin View für BarcodeAllowedState"""
    model = BarcodeAllowedState


class BarcodeScannerAdmin(admin.ModelAdmin):
    """Admin View für BarcodeScanner"""
    inlines = [
        BarcodeAllowedStateInline,
    ]
    list_display = ('token', 'description')


class FachgebietEmailAdminInline(admin.TabularInline):
    """Admin View für FachgebietEmail"""
    model = FachgebietEmail
    extra = 1


class FachgebietAdmin(admin.ModelAdmin):
    """Admin View für Fachgebiet"""
    list_display = ('name', 'kuerzel')
    list_display_links = ('name',)
    inlines = (FachgebietEmailAdminInline,)

    def save_related(self, request, form, formsets, change):
        super(FachgebietAdmin, self).save_related(request, form, formsets, change)

        if change:
            count_added = 0
            for formset in formsets:
                if formset.extra_forms:
                    for new_forms in formset.extra_forms:
                        if new_forms.instance:
                            fachgebiet_email_instance = new_forms.instance
                            fachgebiet_suffix = fachgebiet_email_instance.email_suffix
                            if fachgebiet_suffix:
                                persons = Person.objects.filter(fachgebiet=None)

                                for person in persons:
                                    proposed_fachgebiet = FachgebietEmail.get_fachgebiet_from_email(person.email)
                                    if proposed_fachgebiet \
                                            and proposed_fachgebiet.id == fachgebiet_email_instance.fachgebiet_id:
                                        person.fachgebiet = proposed_fachgebiet
                                        person.save()
                                        count_added += 1

            if count_added > 0:
                self.message_user(request, "Dieser Fachgebiet wurde {0} Personen zugeordnet".format(count_added))

admin.site.register(Person, PersonAdmin)
admin.site.register(Veranstaltung, VeranstaltungAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Einstellung, EinstellungAdmin)
admin.site.register(Mailvorlage, MailvorlageAdmin)
admin.site.register(Kommentar, KommentarAdmin)
admin.site.register(Tutor, TutorAdmin)
admin.site.register(BarcodeScannEvent, BarcodeScannEventAdmin)
admin.site.register(BarcodeScanner, BarcodeScannerAdmin)
admin.site.register(Fachgebiet, FachgebietAdmin)
