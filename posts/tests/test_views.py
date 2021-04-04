import shutil
import tempfile

from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User


# noinspection PyUnresolvedReferences
@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create_user(
            username='test_user'
        )
        cls.user_2 = User.objects.create_user(
            username='test_user_2'
        )
        cls.group = Group.objects.create(
            title='Test group title',
            slug='test_group',
            description='Test description'
        )
        Post.objects.create(
            text='Post 1 for group',
            author=cls.user_2,
        )
        cls.post = Post.objects.create(
            text='Post 2 for group',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @staticmethod
    def check_object(self, response, expected):
        response_page_obj = response.context.get('page')

        if response_page_obj:
            response_post = response_page_obj.object_list[0]
            expected_post = expected[0]
        else:
            response_post = response.context.get('post')
            expected_post = expected

        self.assertEqual(response_post.text, expected_post.text)
        self.assertEqual(response_post.author.username,
                         expected_post.author.username)
        self.assertEqual(response_post.group, expected_post.group)
        self.assertEqual(response_post.image, expected_post.image)

    def test_pages_accessible_by_name_and_use_correct_templates(self):
        """URL-адрес доступен и использует соответствующий шаблон."""

        username = PostViewTests.user.username
        post_id = PostViewTests.post.pk
        group_slug = PostViewTests.group.slug

        name_and_template = (
            ('posts:index', [], 'index.html'),
            ('posts:follow_index', [], 'follow.html'),
            ('posts:new_post', [], 'post_new.html'),
            ('posts:group_posts', [group_slug], 'group.html'),
            ('posts:profile', [username], 'profile.html'),
            ('posts:post', [username, post_id], 'post.html'),
            ('posts:post_edit', [username, post_id], 'post_new.html'),
        )

        for reverse_name, args, template in name_and_template:
            url = reverse(reverse_name, args=args)
            response = self.authorized_client.get(url)
            with self.subTest(url=url,
                              template=template):
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_paginator(self):
        """Шаблоны сформированы с верным количеством постов"""

        paginate_by = 10
        page_2_expected = 5

        user = PostViewTests.user
        group = PostViewTests.group

        Post.objects.bulk_create(
            Post(text=f'Post {i} with group' if i % 3
                 else f'Post {i} without group',
                 author=user,
                 group=group if i % 3 else None)
            for i in range(1, paginate_by + page_2_expected)
        )

        index_posts = Post.objects.count()
        group_posts = group.posts.count()
        profile_posts = user.posts.count()

        name_and_posts = (
            ('posts:index', [], index_posts),
            ('posts:group_posts', [group.slug], group_posts),
            ('posts:profile', [user.username], profile_posts),
        )

        for reverse_name, args, posts_amount in name_and_posts:
            url = reverse(reverse_name, args=args)
            pages_posts = {
                1: paginate_by,
                2: posts_amount - paginate_by
            }
            for page, posts_expected in pages_posts.items():
                with self.subTest(url=url, posts_amount=posts_amount):
                    response = self.guest_client.get(url, {'page': page})
                    posts_count = len(response.context['page'].object_list)
                    self.assertEqual(posts_count, posts_expected)

    def test_page_cache_exists(self):
        """Шаблоны кэшируют объект page."""

        username = PostViewTests.user.username
        group_slug = PostViewTests.group.slug

        name_and_cache = (
            ('posts:index', [], 'index_page'),
            ('posts:follow_index', [], 'follow_page'),
            ('posts:group_posts', [group_slug], 'group_page'),
            ('posts:profile', [username], 'profile_page'),
        )

        for reverse_name, args, cache_name in name_and_cache:
            with self.subTest(reverse_name=reverse_name,
                              cache_name=cache_name):
                self.authorized_client.get(reverse_name, args=args)
                key = make_template_fragment_key(cache_name)
                self.assertIn(key, cache)

    def test_index_list_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""

        response = self.client.get(reverse('posts:index'))

        self.assertIn('page', response.context)

        expected_page_obj = list(Post.objects.order_by('-pub_date')[:10])

        PostViewTests.check_object(self, response, expected_page_obj)

    def test_group_detail_page_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""

        group = PostViewTests.group

        response = self.client.get(
            reverse('posts:group_posts', kwargs={'slug': group.slug}))

        self.assertIn('page', response.context)
        self.assertIn('group', response.context)
        self.assertEqual(response.context['group'].title, group.title)
        self.assertEqual(response.context['group'].slug, group.slug)

        expected_page_obj = list(group.posts.order_by('-pub_date')[:10])

        PostViewTests.check_object(self, response, expected_page_obj)

    def test_group_detail_page_doesnt_return_wrong_context(self):
        """Шаблон group не возвращает посты не своей группы."""

        user = PostViewTests.user
        group = PostViewTests.group
        group_2 = Group.objects.create(
            title='Test group 2 title',
            slug='test_group_2',
        )
        group_2_post = Post.objects.create(
            text='Post 1 for group',
            author=user,
            group=group_2,
        )

        response = self.client.get(
            reverse('posts:group_posts', kwargs={'slug': group.slug}))

        self.assertNotIn(group_2_post, response.context['page'].object_list)

    def test_new_page_shows_correct_context(self):
        """Шаблон post_new сформирован с правильным контекстом."""

        response = self.authorized_client.get(reverse('posts:new_post'))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for field, field_class in form_fields.items():
            form_field = response.context['form'].fields[field]
            with self.subTest(field=field):
                self.assertIsInstance(form_field, field_class)

    def test_post_edit_page_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""

        user = PostViewTests.user
        post = PostViewTests.post
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'username': user.username,
                                               'post_id': post.pk}))

        form_fields = (
            ('text', forms.fields.CharField, post.text),
            ('group', forms.models.ModelChoiceField, post.group.id),
        )

        for field, field_class, field_initial in form_fields:
            form_field = response.context['form'].fields[field]
            form_initial = response.context['form'].initial[field]
            with self.subTest(field=field,
                              field_class=field_class,
                              field_initial=field_initial):
                self.assertIsInstance(form_field, field_class)
                self.assertEqual(form_initial, field_initial)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""

        user = PostViewTests.user

        response = self.client.get(
            reverse('posts:profile', kwargs={'username': user.username}))

        self.assertIn('page', response.context)
        self.assertIn('profile', response.context)
        self.assertEqual(response.context['profile'].username, user.username)

        expected_page_obj = list(user.posts.order_by('-pub_date')[:10])

        PostViewTests.check_object(self, response, expected_page_obj)

    def test_post_page_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""

        user = PostViewTests.user
        post = PostViewTests.post
        response = self.authorized_client.get(
            reverse('posts:post', kwargs={'username': user.username,
                                          'post_id': post.pk}))

        self.assertIn('post', response.context)
        self.assertIn('profile', response.context)
        self.assertEqual(response.context['profile'].username, user.username)

        expected_post = user.posts.get(id=post.id)

        PostViewTests.check_object(self, response, expected_post)

    def test_profile_follow_view(self):
        """Авторизованный пользователь может подписываться на других
        пользователей."""

        user = PostViewTests.user
        user_2 = PostViewTests.user_2

        self.assertFalse(
            Follow.objects.filter(user=user, author=user_2).exists())

        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': user_2.username}))

        self.assertTrue(
            Follow.objects.filter(user=user, author=user_2).exists())

    def test_profile_follow_view_cant_follow_itself(self):
        """Авторизованный пользователь не может подписываться на себя."""

        user = PostViewTests.user

        self.assertFalse(
            Follow.objects.filter(user=user, author=user).exists())

        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': user.username}))

        self.assertFalse(
            Follow.objects.filter(user=user, author=user).exists())

    def test_profile_unfollow_view(self):
        """Авторизованный пользователь может удалять других пользователей
        из подписок."""

        user = PostViewTests.user
        user_2 = PostViewTests.user_2

        Follow.objects.create(user=user, author=user_2)

        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': user_2.username}))

        self.assertFalse(
            Follow.objects.filter(user=user, author=user_2).exists())

    def test_follow_view_new_followed_post(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""

        user_2 = PostViewTests.user_2

        Post.objects.create(
            text='Post for follow_view',
            author=user_2
        )

        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': user_2.username}))

        response = self.authorized_client.get(reverse('posts:follow_index'))

        response_page_obj = list(response.context.get('page').object_list)
        expected_page_obj = list(Post.objects.filter(
            author=user_2).order_by('-pub_date'))

        self.assertEqual(response_page_obj, expected_page_obj)

    def test_follow_view_new_unfollowed_post(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан."""

        user_2 = PostViewTests.user_2
        user_3 = User.objects.create_user(
            username='test_user_3')

        authorized_client_3 = Client()
        authorized_client_3.force_login(user_3)

        Post.objects.create(
            text='Post for follow_view',
            author=user_2
        )

        response_3 = authorized_client_3.get(reverse('posts:follow_index'))

        response_page_obj_3 = list(response_3.context.get('page').object_list)

        self.assertFalse(
            Follow.objects.filter(user=user_3, author=user_2).exists())
        self.assertFalse(response_page_obj_3)
