from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.db import models
from django.urls import reverse

User = get_user_model()


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Введите текст публикации',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата',
        db_index=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name='Сообщество',
        help_text='Выберете сообщество',
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True, null=True,
        verbose_name='Изображение',
        help_text='Загрузите изображение',
    )

    class Meta:
        verbose_name_plural = 'Публикации'
        verbose_name = 'Публикация'
        ordering = ['-pub_date']
        default_related_name = 'posts'

    def __str__(self):
        return self.text[:15]

    # noinspection PyUnresolvedReferences
    def get_absolute_url(self):
        return reverse('posts:post', kwargs={'username': self.author.username,
                                             'post_id': self.pk})


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Имя',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Адрес',
        validators=(
            MinLengthValidator(3, 'Адрес должен быть не короче 3 символов'),),
    )
    description = models.TextField(
        verbose_name='Описание',
    )

    class Meta:
        verbose_name_plural = 'Сообщества'
        verbose_name = 'Сообщество'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('posts:group_posts', kwargs={'slug': self.slug})


class Comment(models.Model):
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария',
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации комментария',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Публикация',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    class Meta:
        verbose_name_plural = 'Комментарии'
        verbose_name = 'Комментарий'
        ordering = ['-created']
        default_related_name = 'comments'

    def __str__(self):
        return self.text[:15]

    # noinspection PyUnresolvedReferences
    def get_absolute_url(self):
        return reverse('posts:post',
                       kwargs={'username': self.post.author.username,
                               'post_id': self.post.id})


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='posts_follow_user_author_constraint',
            )
        ]

    # noinspection PyUnresolvedReferences
    def __str__(self):
        return f'{self.user.username} - {self.author.username}'
