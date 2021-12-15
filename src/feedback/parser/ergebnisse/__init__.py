# coding=utf-8

# TODO: Fehlerbehandlung bei kaputten Dateien
def parse_ergebnisse(semester, csvfile, ueparser=None):
    import csv
    from feedback.models import get_model, get_model_string, Veranstaltung

    if ueparser is None:
        parser = _get_parser(semester)
    else:
        parser = _get_parser(semester, ueparser)

    reader = csv.reader(csvfile, delimiter=';')

    # Die letzte Spalte die noch zur Veranstaltung gehört.
    # Alle diese Spalten sind gleich für jeden Fragebogen einer Veranstaltung
    grenzVeranstFragebogen = 16

    # Kopfzeile überspringen
    next(reader)

    # Einlesen der Zeilen der CSV-Datei
    combined = {}
    for row in reader:
        converted = [str(cell) for cell in row]
        veranstaltung = converted[:grenzVeranstFragebogen]
        fragebogen = converted[grenzVeranstFragebogen:]

        # Bögen pro Veranstaltung zusammensuchen
        if veranstaltung[5] in combined:
            combined[veranstaltung[5]]['f'].append(fragebogen)
        else:
            combined[veranstaltung[5]] = {'v': veranstaltung, 'f': [fragebogen]}

    # Speicherung der Daten
    warnings = []
    errors = []
    vcount = 0
    fbcount = 0
    if ueparser is None:
        fbmodel = get_model('Fragebogen', semester)
    else:
        fbmodel = get_model_string('Fragebogen', ueparser)

    for veranst in list(combined.values()):
        try:
            v = Veranstaltung.objects.get(name=veranst['v'][5], lv_nr=veranst['v'][6], semester=semester)

        except Veranstaltung.DoesNotExist:
            try:
                v = Veranstaltung.objects.get(name=veranst['v'][5], semester=semester)
                warnings.append(('Die Veranstaltung "%s" hat in der Datenbank die ' +
                                 'Lehrveranstaltungsnummer "%s", in der CSV-Datei aber "%s". Die Ergebnisse ' +
                                 'wurden trotzdem importiert.') % (v.name, v.lv_nr, veranst['v'][6]))

            except Veranstaltung.DoesNotExist:
                try:
                    v = Veranstaltung.objects.get(lv_nr=veranst['v'][6], semester=semester)
                    warnings.append(('Die Veranstaltung mit der Lehrveranstaltungsnummer "%s" hat in ' +
                                     'der Datenbank den Namen "%s", in der CSV-Datei aber "%s". Die Ergebnisse ' +
                                     'wurden trotzdem importiert.') % (v.lv_nr, v.name, veranst['v'][5]))

                except Veranstaltung.DoesNotExist:
                    errors.append(('Die Veranstaltung "%s" (%s) existiert im System nicht und ' +
                                   'wurde deshalb nicht importiert!') % (veranst['v'][5], veranst['v'][6]))
                    continue

        if fbmodel.objects.filter(veranstaltung=v).count():
            errors.append(('In der Datenbank existieren bereits Fragebögen zur Veranstaltung ' +
                           '"%s". Sie wurde deshalb nicht importiert!') % v.name)
            continue

        vcount += 1
        for frageb in veranst['f']:
            fbcount += 1
            parser.create_fragebogen(v, frageb)

    # Warnungen, Fehler, Anzahl der importierten Veranstaltungen / Fragebögen zurückgeben
    return warnings, errors, vcount, fbcount


def _get_parser(semester, bogen=None):
    if bogen is None:
        bogen = semester.fragebogen
    mod = '%s.parser%s' % (__name__, bogen)
    cls = 'Parser%s' % bogen
    module = __import__(mod, fromlist=(cls,))
    return getattr(module, cls)
