from django.views.generic import ListView
from django.views.generic.edit import CreateView

from feedback.models import Veranstaltung, Semester, BarcodeScannEvent
from feedback.forms import CreateBarcodeScannEventForm


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
