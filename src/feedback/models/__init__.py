# coding=utf-8

from feedback.models.base import Einstellung, Mailvorlage, Person, Semester, Veranstaltung, \
    Tutor, BarcodeScanner, BarcodeScannEvent, BarcodeAllowedState, Log, FachgebietEmail, Fachgebiet, \
    EmailEndung
from feedback.models.imports import ImportPerson, ImportCategory, ImportVeranstaltung
from feedback.models.fragebogen import Fragebogen, Ergebnis, Kommentar
from feedback.models.fragebogen2008 import Fragebogen2008, Ergebnis2008
from feedback.models.fragebogen2009 import Fragebogen2009, Ergebnis2009
from feedback.models.fragebogen2012 import Fragebogen2012, Ergebnis2012
from feedback.models.fragebogen2016 import Fragebogen2016, Ergebnis2016
from feedback.models.fragebogenUE2016 import FragebogenUE2016
from django.core.exceptions import ObjectDoesNotExist

from django.db.models import Q


def get_model(model, semester):
    mod = '%s.fragebogen%s' % (__name__, semester.fragebogen)
    cls = '%s%s' % (model, semester.fragebogen)
    module = __import__(mod, fromlist=(cls,))
    return getattr(module, cls)

def get_model_string(model, semester):
    mod = '%s.fragebogen%s' % (__name__, semester)
    cls = '%s%s' % (model, semester)
    module = __import__(mod, fromlist=(cls,))
    return getattr(module, cls)

def long_not_ordert():
    """Alle Veranstaltungen die schon länger nicht mehr evaluiert wurden"""
    #suche nach allen Veranstaltungen aus dem aktellen Semester bei denen
    #die anzahl leer oder die anzahl 0 ist oder evaluieren auf false steht
    candidates = Veranstaltung.objects.filter(Q(semester=Semester.current()), Q(anzahl__isnull=True) | Q(anzahl__lte=0) | Q(evaluieren=False))

    result = []

    for can in candidates:
        #hole die früheren Veranstaltungen
        res = past_semester_orders(can)
        if res != None:
            last_result = 'Es liegen keine Ergebnisse vor'
            #Stellt die neuste Veranstaltung an erste stelle
            res.reverse()
            for past in res:
                #Ist aktuelle Veranstaltung nicht laenge als zwei Jahre her?
                jahre = 2
                if past['veranstaltung'].semester.semester >= (Semester.current().semester - (jahre * 10)):
                    #Es gab Ergebnisse
                    if past['anzahl_ruecklauf'] > 0:
                        break
                else:
                    for cord in res:
                        #suche die letzen Ergebnisse
                        if cord['anzahl_ruecklauf']>0:
                            last_result = cord['veranstaltung'].semester
                            break
                    result.append({'veranstaltung': can, 'letzte_ergebnisse': last_result, 'bestellungen': res })
                    break
        else:
            result.append({'veranstaltung': can, 'letzte_ergebnisse': last_result, 'bestellungen': res })
    return result


def past_semester_orders(cur_ver):
    """Gibt die Anzahl an Bestellungen und Rückläufern aus den früheren Semestern"""
    similar_lv = Veranstaltung.objects.filter(lv_nr=cur_ver.lv_nr,semester__semester__lt=cur_ver.semester.semester).order_by('-semester')

    result = []

    for onelv in similar_lv:
        ErgebnisModel = get_model('Ergebnis', onelv.semester)
        anzahl_bestellung = onelv.anzahl

        if anzahl_bestellung == None:
            continue

        anzahl_ruecklauf = 0
        try:
            ergebnis = ErgebnisModel.objects.get(veranstaltung=onelv)
            anzahl_ruecklauf = ergebnis.anzahl
        except ObjectDoesNotExist:
            pass

        result.append({'veranstaltung': onelv, 'anzahl_bestellung': anzahl_bestellung, 'anzahl_ruecklauf': anzahl_ruecklauf})

    return result
