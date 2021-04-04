from django.test import TestCase

from posts.models import Group, Post, User


# noinspection PyUnresolvedReferences
class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_user',
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

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""

        post = PostModelTests.post

        field_verboses = {
            'text': 'Текст',
            'group': 'Сообщество',
            'image': 'Изображение',
        }

        for field, field_verbose in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, field_verbose)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""

        post = PostModelTests.post

        field_helps = {
            'text': 'Введите текст публикации',
            'group': 'Выберете сообщество',
            'image': 'Загрузите изображение',
        }

        for field, field_help in field_helps.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, field_help)

    def test_model_as_str(self):
        """Отображение модели в виде строки совпадает с ожидаемым."""

        post = PostModelTests.post
        group = PostModelTests.group

        model_as_str = {
            post: post.text[:15],
            group: group.title,
        }

        for model, model_str in model_as_str.items():
            with self.subTest(model=model):
                self.assertEqual(str(model), model_str)
