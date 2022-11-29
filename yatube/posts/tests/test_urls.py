from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User

from ..constants import (INDEX_TEMPLATE, GROUP_LIST_TEMPLATE,
                         PROFILE_TEMPLATE, POST_DETAIL_TEMPLATE,
                         CREATE_POST_TEMPLATE)


class PostsUrlsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название для теста',
            slug='slug',
            description='Описание для теста',
        )
        cls.author = User.objects.create_user(
            username='author'
        )
        cls.no_author = User.objects.create_user(
            username='not_author'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Пост для теста',
            group=cls.group,
        )

        cls.TEMPLATES_URLS = {
            INDEX_TEMPLATE: reverse('posts:index'),
            GROUP_LIST_TEMPLATE: reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ),
            PROFILE_TEMPLATE: reverse(
                'posts:profile',
                kwargs={'username': cls.author.username},
            ),
            POST_DETAIL_TEMPLATE: reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.pk}
            ),
            CREATE_POST_TEMPLATE: reverse('posts:post_create'),
        }

        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id},
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

        self.no_author_client = Client()
        self.no_author_client.force_login(self.no_author)

        self.cases = [
            # страница / доступна любому пользователю
            (
                self.TEMPLATES_URLS[INDEX_TEMPLATE],
                self.guest_client,
                HTTPStatus.OK
            ),
            (
                self.TEMPLATES_URLS[GROUP_LIST_TEMPLATE],
                self.guest_client,
                HTTPStatus.OK
            ),
            (
                self.TEMPLATES_URLS[PROFILE_TEMPLATE],
                self.guest_client,
                HTTPStatus.OK
            ),
            (
                self.TEMPLATES_URLS[POST_DETAIL_TEMPLATE],
                self.guest_client,
                HTTPStatus.OK
            ),
            # не работает
            # (
            #    reverse('posts:unexisting_page'),
            #    self.guest_client,
            #    HTTPStatus.NOT_FOUND
            # ),
            (
                self.TEMPLATES_URLS[CREATE_POST_TEMPLATE],
                self.authorized_client,
                HTTPStatus.OK
            ),
            (
                self.TEMPLATES_URLS[CREATE_POST_TEMPLATE],
                self.guest_client,
                HTTPStatus.FOUND
            ),
            (
                self.POST_EDIT_URL,
                self.authorized_client,
                HTTPStatus.OK
            ),
            (
                self.POST_EDIT_URL,
                self.no_author_client,
                HTTPStatus.FOUND
            ),
        ]
        cache.clear()

    def test_all_cases(self):
        """Проверка доступа страниц приложения post для разных юзеров."""
        for self.case in self.cases:
            url, client, status = self.case
            with self.subTest():
                self.assertEqual(client.get(url).status_code, status)

    def test_urls_use_correct_template(self):
        """Проверка на то что URL-адрес использует подходящий шаблон."""
        for template, url in self.TEMPLATES_URLS.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.authorized_client.get(url),
                    template
                )
