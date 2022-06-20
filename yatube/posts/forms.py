from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    """Форма создания поста"""
    class Meta:
        model = Post
        fields = ('text', 'group',)
