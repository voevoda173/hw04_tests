from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группы',
            slug='test-slug',
            description='Тестовое описание'

        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
        )

        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """Проверка добавления поста в базу данных."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост',
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.author,
            ).exists()
        )

    def test_post_edit(self):
        """Проверка изменения поста при его редактировании."""
        form_data = {
            'text': 'Отредактированный пост',
            'author': self.author,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            Post.objects.get(pk=self.post.id).text, form_data['text']
        )
