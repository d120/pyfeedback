from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from django.utils import translation
from django.conf.urls.i18n import i18n_patterns

from feedback.templatetags.filter_range import filter_range
from feedback.templatetags.translate_url import translate_url


class FilterRangeTests(SimpleTestCase):
    def test_returns_range_as_list(self):
        self.assertEqual(filter_range(0, 5), [0, 1, 2, 3, 4])

    def test_start_is_inclusive(self):
        self.assertEqual(filter_range(2, 5), [2, 3, 4])

    def test_end_is_exclusive(self):
        self.assertEqual(filter_range(2, 5), [2, 3, 4])
        self.assertNotIn(5, filter_range(2, 5))

    def test_empty_range(self):
        self.assertEqual(filter_range(5, 5), [])

    def test_reverse_range(self):
        self.assertEqual(filter_range(5, 2), [])

    def test_negative_numbers(self):
        self.assertEqual(filter_range(-2, 3), [-2, -1, 0, 1, 2])


# URL namespace used by translate_url tests.
def test_view(request, pk=None):
    return HttpResponse("OK")

urlpatterns = [
    path(
        "",
        include(
            (
                [
                    path(
                        "product/<int:pk>/",
                        test_view,
                        name="detail",
                    ),
                ],
                "testapp",
            ),
            namespace="products",
        ),
    ),
]

@override_settings(ROOT_URLCONF=__name__)
class TranslateUrlTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        translation.activate("en")

    def tearDown(self):
        translation.deactivate()

    def test_returns_empty_string_when_request_is_missing(self):
        context = {}

        result = translate_url(context, "de")

        self.assertEqual(result, "")

    def test_returns_empty_string_for_unresolvable_url(self):
        request = self.factory.get("/does-not-exist/")

        context = {
            "request": request,
        }

        result = translate_url(context, "de")

        self.assertEqual(result, "")

    def test_translates_url(self):
        request = self.factory.get("/product/123/")

        context = {
            "request": request,
        }

        result = translate_url(context, "de")

        self.assertEqual(result, "/product/123/")

    def test_preserves_original_language(self):
        translation.activate("en")

        request = self.factory.get("/product/123/")

        context = {
            "request": request,
        }

        translate_url(context, "de")

        self.assertEqual(
            translation.get_language(),
            "en",
        )

    def test_uses_url_kwargs(self):
        request = self.factory.get("/product/42/")

        context = {
            "request": request,
        }

        result = translate_url(context, "de")

        self.assertEqual(result, "/product/42/")