from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


# noinspection PyUnresolvedReferences
class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username='test_user',
        )
        cls.user_2 = User.objects.create_user(
            username='test_user_2',
        )
        cls.group = Group.objects.create(
            title='Test group title',
            slug='test_group',
            description='Test description'
        )
        cls.post = Post.objects.create(
            text='Test post text longer than 15 characters',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)

    def test_404_error_url(self):
        """Некорректный URL-адрес работает корректно."""
        response = self.guest_client.get('/404_error/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_work_for_guests(self):
        """URL-адрес работает корректно для анонимного пользователя."""

        username = PostURLTests.user.username
        post_id = PostURLTests.post.pk
        group_slug = PostURLTests.group.slug

        guests_allowed_urls = (
            '/',
            f'/group/{group_slug}/',
            f'/{username}/',
            f'/{username}/{post_id}/',
        )

        for url in guests_allowed_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_for_guests(self):
        """URL-адрес перенаправляет анонимного пользователя
        на страницу авторизации."""

        username = PostURLTests.user.username
        post_id = PostURLTests.post.pk

        guests_redirected_urls = {
            '/follow/': reverse('login') + '?next=/follow/',

            '/new/': reverse('login') + '?next=/new/',

            f'/{username}/{post_id}/edit/':
                reverse('login') + f'?next=/{username}/{post_id}/edit/',
        }

        for url, redirect_name in (guests_redirected_urls.items()):
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect_name)

    def test_urls_work_for_authorized(self):
        """URL-адрес работает корректно для авторизованного пользователя."""

        username = PostURLTests.user.username
        post_id = PostURLTests.post.pk
        group_slug = PostURLTests.group.slug

        authorized_allowed_urls = (
            '/',
            '/follow/',
            '/new/',
            f'/group/{group_slug}/',
            f'/{username}/',
            f'/{username}/{post_id}/',
            f'/{username}/{post_id}/edit/',
        )

        for url in authorized_allowed_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirects_for_no_author(self):
        """URL-адрес редактирования поста перенаправит неавтора поста
        на страницу просмотра поста."""

        username = PostURLTests.user.username
        post_id = PostURLTests.post.pk

        response = self.authorized_client_2.get(
            f'/{username}/{post_id}/edit/', follow=True)

        redirect_url = f'/{username}/{post_id}/'

        self.assertRedirects(response, redirect_url)

    def test_urls_exist_at_desired_locations(self):
        """URL-адрес использует соответствующий шаблон."""

        username = PostURLTests.user.username
        post_id = PostURLTests.post.pk
        group_slug = PostURLTests.group.slug

        templates_urls = {
            '/': 'index.html',
            f'/group/{group_slug}/': 'group.html',
            '/new/': 'post_new.html',
            f'/{username}/': 'profile.html',
            f'/{username}/{post_id}/': 'post.html',
            f'/{username}/{post_id}/edit/': 'post_new.html',
        }

        for url, template in templates_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
