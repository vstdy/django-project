from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    text = forms.CharField(label='Описание',
                           widget=forms.widgets.Textarea(
                               attrs={'rows': 5}))

    class Meta:
        model = Comment
        fields = ('text',)
