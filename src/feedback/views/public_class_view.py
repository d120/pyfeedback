import datetime
from django.views.generic import ListView
from django.views.generic.edit import CreateView

from feedback.models import Veranstaltung, Semester, BarcodeScannEvent, BarcodeScanner, BarcodeAllowedState, Log
from feedback.forms import CreateBarcodeScannEventForm
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import render


@require_http_methods(('HEAD', 'GET', 'POST'))
def barcodedrop(request):
    if request.method == 'POST':
        success = False
        response_message = ""

        barcode = request.POST.get('barcode')
        scanner_token = request.POST.get('scanner_token')
        try:
            barcode_scanner = BarcodeScanner.objects.get(token=scanner_token)
            barcode_decode = Veranstaltung.decode_barcode(int(barcode))
            verst_obj = Veranstaltung.objects.get(pk=barcode_decode['veranstaltung'])
            next_state = verst_obj.get_next_state()
            if next_state is None:
                response_message = "Nachster Status ungultig."
            else:
                time_offset = datetime.date.today() - datetime.timedelta(minutes=1)
                is_double_scan = Log.objects.filter(
                    veranstaltung=verst_obj,
                    timestamp__gt=time_offset,
                    interface=Log.SCANNER).count()

                if is_double_scan > 0:
                    response_message = "Die Veranstaltung wurde in der vergangenen Stunde " \
                                       "bereits in den nachsten Zustand versetzt."
                else:
                    is_allowed = BarcodeAllowedState.objects.filter(
                        barcode_scanner=barcode_scanner,
                        allow_state=next_state).count()

                    if is_allowed > 0:
                        verst_obj.status = next_state
                        verst_obj.save()
                        verst_obj.log(barcode_scanner)
                        response_message = "Die Veranstaltung wurde erfolgreich in den nachsten Zustand uerfuehrt"
                        success = True
                    else:
                        response_message = "Barcode hat nicht die notigen Berechtigungen"

        except (BarcodeScanner.DoesNotExist, KeyError):
            response_message = "Token ungueltig."
        except (Veranstaltung.DoesNotExist, KeyError):
            response_message = "Veranstaltung nicht gefunden."
        except ValueError, e:
            response_message = unicode(e.message)
        except TypeError, e:
            response_message = unicode(e.message)

        return JsonResponse({"success": success, "message": response_message})
    else:
        # For Debug only
        form = CreateBarcodeScannEventForm()
        return render(request, 'feedback/CreateBarcodeScannEvent.html', {'form': form})


class VeranstaltungsDeadlines(ListView):
    queryset = Veranstaltung.objects.filter(semester=Semester.current(), evaluieren=True).exclude(
        auswertungstermin__isnull=True).order_by('name')
    template_name = "feedback/VeranstaltungsDeadlines.html"


class CreateBarcodeScannEvent(CreateView):
    """View fuer die Barcode scanner.
    Fuer diese view ist wird csrf_exempt in urls.py genutzt!"""
    model = BarcodeScannEvent
    form_class = CreateBarcodeScannEventForm
    template_name = 'feedback/CreateBarcodeScannEvent.html'
    success_url = '/'
