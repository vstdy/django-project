from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_app_pages_accessible_by_names(self):
        """URLs, генерируемые при помощи имён, доступны."""

        reverse_names = (
            'about:author',
            'about:tech',
        )

        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse(reverse_name))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_app_pages_uses_correct_templates(self):
        """URLs, генерируемые при помощи имён, используют верные шаблоны."""

        templates_url_names = {
            'about:author': 'about/about.html',
            'about:tech': 'about/tech.html',
        }

        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse(reverse_name))
                self.assertTemplateUsed(response, template)
