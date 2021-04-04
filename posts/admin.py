from django.contrib import admin

from .models import Comment, Group, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    list_display_links = ('pk', 'text',)
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    date_hierarchy = 'pub_date'
    fields = ('text', 'author', 'group', 'pub_date',)
    readonly_fields = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'slug', 'description')
    list_display_links = ('pk', 'title',)
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}
    empty_value_display = '-пусто-'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'created', 'post', 'author')
    list_display_links = ('pk', 'text',)
    list_editable = ('post',)
    search_fields = ('title',)
    list_filter = ('created',)
    date_hierarchy = 'created'
    fields = ('text', 'created', 'post', 'author',)
    readonly_fields = ('created',)
