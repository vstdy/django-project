from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_app_urls_exist_at_desired_locations(self):
        """Проверка доступности адресов приложения about."""

        urls = (
            '/about/author/',
            '/about/tech/',
        )

        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_app_urls_use_correct_templates(self):
        """Проверка шаблонов для адресов приложения about."""

        templates_url_names = {
            '/about/author/': 'about/about.html',
            '/about/tech/': 'about/tech.html',
        }

        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
