from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )

        Post.objects.create(
            text='Тестовый текст',
            author=cls.user_author,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.user_author)

    def test_urls_exist_at_desired_location_none_auth(self):
        """Проверка страниц, доступных любому пользователю."""
        urls = [
            '/',
            '/group/test-slug/',
            '/profile/TestAuthor/',
            '/posts/1/',
        ]
        for url in urls:
            with self.subTest(url=url):
                responce = self.guest_client.get(url)
                self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_urls_exist_at_desired_location_auth(self):
        """Проверка страниц, доступных только авторизованному пользователю."""
        urls = [
            '/create/',
        ]
        for url in urls:
            with self.subTest(url=url):
                responce = self.authorized_client.get(url)
                self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_urls_exist_at_desired_location_author(self):
        """Проверка страниц, доступных только автору."""
        urls = [
            '/posts/1/edit/',
        ]
        for url in urls:
            with self.subTest(url=url):
                responce = self.post_author.get(url)
                self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_url_unexisting_page(self):
        """Проверка запроса к несуществующей странице"""
        response = self.guest_client.get('/unexisting-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_url_redirect_no_author_on_post_detail(self):
        """Проверка редиректа не автора поста при попытке редактирования"""
        response = self.authorized_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, '/posts/1/')

    def test_create_or_edit_url_redirect_anonymus_on_login(self):
        """Проверка редиректа анонимного пользователя
        при попытке создания или редактирования поста."""
        urls = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/1/edit/': '/auth/login/?next=/posts/1/edit/',
        }
        for url, redirect in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_urls_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/TestAuthor/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_urls_names.items():
            with self.subTest(address=address):
                response = self.post_author.get(address)
                self.assertTemplateUsed(response, template)
