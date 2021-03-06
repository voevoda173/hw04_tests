from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from ..constants import POSTS_AMOUNT
from ..models import Group, Post, User


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = [
            Post(
                text=f'Тестовый текст {i}',
                author=cls.user_author,
                group=cls.group,
            )
            for i in range(2)
        ]
        Post.objects.bulk_create(cls.posts)
        cls.posts = Post.objects.select_related('author', 'group')

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user_author)

    def test_pages_uses_correct_template_all_users(self):
        """URL-адрес использует соответствующий шаблон.(posts)."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile',
                    kwargs={'username': self.user_author}):
            'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.posts[0].id}):
            'posts/post_detail.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.posts[0].id}):
            'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_pages_show_correct_context(self, response):
        """Проверка правильности формирования контекста."""
        first_object = response.context['page_obj'][0]
        context_objects = {
            first_object.text: self.posts[0].text,
            first_object.author.id: self.posts[0].author.id,
            first_object.group.slug: self.posts[0].group.slug,
        }
        for response_name, reverse_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:index'))
        self.check_pages_show_correct_context(response)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.author_client.get(reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})))
        self.assertEqual(response.context['group'], self.group)
        self.check_pages_show_correct_context(response)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.author_client.get(reverse('posts:profile',
                    kwargs={'username': self.user_author.username})))
        self.assertEqual(response.context['author'], self.user_author)
        self.check_pages_show_correct_context(response)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контестом."""
        response = (self.author_client.get(reverse('posts:post_detail',
                    kwargs={'post_id': self.posts[0].id})))
        self.assertEqual(response.context.get('post'),
                         self.posts[0])

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = (self.author_client.get(reverse('posts:post_create')))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context_in_edit(self):
        """Шаблон create_post сформирован с правильным контекстом
        при редактировании поста."""
        response = (self.author_client.get(reverse('posts:post_edit',
                    kwargs={'post_id': self.posts[0].id})))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_post_on_create(self):
        """Проверка, что пост правильно добавляется на страницы."""
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.user_author,
            group=self.group,
        )
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user_author}),
        ]
        for address in pages:
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.context.get('page_obj')[0], post)

    def test_group(self):
        """Проверка, что пост не попал в группу, для которой
        не был предназначен."""
        fake_group = Group.objects.create(
            title='Тестовый заголовок',
            slug='fake-slug',
            description='Тестовое описание',
        )
        response = self.author_client.get(reverse('posts:group_list',
                                          args=[fake_group.slug]))
        self.assertNotIn(self.posts, response.context['page_obj'])


class PaginatorViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.first_page_len_posts = POSTS_AMOUNT
        cls.second_page_len_posts = 3
        cls.posts = [
            Post(
                text=f'Тестовый текст {i}',
                author=cls.user_author,
                group=cls.group,
            )
            for i in range(
                cls.first_page_len_posts + cls.second_page_len_posts)
        ]
        Post.objects.bulk_create(cls.posts)
        cls.posts = Post.objects.select_related('author', 'group')

    def test_pages_pagination(self):
        """Проверка правильности вывода количества постов на страницах."""
        pages_with_pagination = {
            reverse('posts:index'): self.first_page_len_posts,
            reverse('posts:index') + '?page=2': self.second_page_len_posts,
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            self.first_page_len_posts,
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
            + '?page=2': self.second_page_len_posts,
            reverse('posts:profile', kwargs={'username': self.user_author}):
            self.first_page_len_posts,
            reverse('posts:profile', kwargs={'username': self.user_author})
            + '?page=2': self.second_page_len_posts,
        }
        for address, len_posts in pages_with_pagination.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']), len_posts)
