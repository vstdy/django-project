import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User


# noinspection PyUnresolvedReferences
@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.user = User.objects.create_user(
            username='test_user',
        )
        cls.group = Group.objects.create(
            title='Test group title',
            slug='test_group',
            description='Test description'
        )
        cls.group_2 = Group.objects.create(
            title='Test group 2 title',
            slug='test_group_2',
            description='Test description 2'
        )
        cls.post = Post.objects.create(
            text='Post for edition',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""

        uploaded = SimpleUploadedFile(
            name='small_1.gif',
            content=PostFormTests.small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Created post',
            'group': PostFormTests.group.id,
            'image': uploaded
        }

        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )

        post = Post.objects.get(text='Created post')

        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, 'posts/small_1.gif')
        self.assertEqual(response.status_code, 200)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""

        user = PostFormTests.user
        post = PostFormTests.post
        uploaded = SimpleUploadedFile(
            name='small_2.gif',
            content=PostFormTests.small_gif,
            content_type='image/gif',
        )

        form_data = {
            'text': 'Edited post text',
            'group': PostFormTests.group_2.id,
            'image': uploaded
        }

        post_edit_url = reverse(
            'posts:post_edit', kwargs={'username': user.username,
                                       'post_id': post.id})
        redirect_edited_url = reverse(
            'posts:post', kwargs={'username': user.username,
                                  'post_id': post.id})
        group_posts_url = reverse(
            'posts:group_posts', kwargs={'slug': PostFormTests.group.slug})

        response = self.authorized_client.post(
            post_edit_url, data=form_data, follow=True)
        edited_post = response.context['post']

        group_posts_response = self.authorized_client.get(group_posts_url)
        group_posts_context = group_posts_response.context_data['page'][:]

        self.assertRedirects(response, redirect_edited_url)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group_id, form_data['group'])
        self.assertEqual(edited_post.image,
                         f"posts/{form_data['image'].name}")
        self.assertNotIn(edited_post, group_posts_context)

    def test_comment_post_for_authorized(self):
        """Авторизированный пользователь может комментировать посты."""

        user = PostFormTests.user
        post = PostFormTests.post

        form_data = {
            'text': 'Post comment'
        }

        auth_redirect_url = reverse(
            'posts:post', kwargs={'username': user.username,
                                  'post_id': post.id})

        auth_response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'username': user.username,
                            'post_id': post.id}), data=form_data, follow=True)

        self.assertRedirects(auth_response, auth_redirect_url)
        self.assertTrue(
            Comment.objects.filter(text=form_data['text']).exists())

    def test_comment_post_redirects_unauthorized(self):
        """Неавторизированный пользователь перенаправляется
        на страницу авторизации."""

        user = PostFormTests.user
        post = PostFormTests.post

        guest_client = Client()

        form_data = {
            'text': 'Post comment'
        }

        url = reverse('posts:add_comment',
                      kwargs={'username': user.username,
                              'post_id': post.id})
        guest_redirect_url = reverse('login') + f'?next={url}'

        guest_response = guest_client.post(
            url, data=form_data, follow=True)

        self.assertRedirects(guest_response, guest_redirect_url)
