from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User

from ..constants import (INDEX_TEMPLATE, GROUP_LIST_TEMPLATE,
                         PROFILE_TEMPLATE, CREATE_POST_TEMPLATE,
                         LOGIN_TEMPLATE)

SLUG = 'slug'
USERNAME = 'author'
TEMPLATES_URLS = {
    INDEX_TEMPLATE: reverse('posts:index'),
    GROUP_LIST_TEMPLATE: reverse(
        'posts:group_list',
        kwargs={'slug': SLUG}),
    PROFILE_TEMPLATE: reverse(
        'posts:profile',
        kwargs={'username': USERNAME}),
    CREATE_POST_TEMPLATE: reverse('posts:post_create'),
    LOGIN_TEMPLATE: reverse('users:login')}


class PostsUrlsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название для теста',
            slug=SLUG,
            description='Описание для теста',
        )
        cls.author = User.objects.create_user(
            username=USERNAME
        )
        cls.no_author = User.objects.create_user(
            username='not_author'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Пост для теста',
            group=cls.group,
        )

        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.pk})

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

        cache.clear()

    def test_all_cases(self):
        """Проверка доступа страниц приложения post для разных юзеров."""
        cases = [
            # страница / доступна любому пользователю
            (
                TEMPLATES_URLS[INDEX_TEMPLATE],
                self.guest_client,
                HTTPStatus.OK,
                None
            ),
            (
                TEMPLATES_URLS[GROUP_LIST_TEMPLATE],
                self.guest_client,
                HTTPStatus.OK,
                None
            ),
            (
                TEMPLATES_URLS[PROFILE_TEMPLATE],
                self.guest_client,
                HTTPStatus.OK,
                None
            ),
            (
                self.POST_DETAIL_URL,
                self.guest_client,
                HTTPStatus.OK,
                None
            ),
            (
                TEMPLATES_URLS[CREATE_POST_TEMPLATE],
                self.authorized_client,
                HTTPStatus.OK,
                None
            ),
            (
                TEMPLATES_URLS[CREATE_POST_TEMPLATE],
                self.guest_client,
                HTTPStatus.FOUND,
                TEMPLATES_URLS[LOGIN_TEMPLATE]
            ),
            (
                self.POST_EDIT_URL,
                self.authorized_client,
                HTTPStatus.OK,
                None
            ),
            (
                self.POST_EDIT_URL,
                self.no_author_client,
                HTTPStatus.FOUND,
                self.POST_DETAIL_URL
            ),
        ]
        for url, client, status, redirect in cases:
            with self.subTest(url=url, client=client, status=status):
                self.assertEqual(client.get(url).status_code, status)

    def test_redirect_cases(self):
        """Проверка редиректа для неавториз и невавтора."""
        cases = [
            (
                TEMPLATES_URLS[CREATE_POST_TEMPLATE],
                self.guest_client,
                (TEMPLATES_URLS[LOGIN_TEMPLATE]
                 + '?next=' + TEMPLATES_URLS[CREATE_POST_TEMPLATE])
            ),
            (
                self.POST_EDIT_URL,
                self.no_author_client,
                self.POST_DETAIL_URL
            ),
        ]
        for url, client, redirect in cases:
            with self.subTest(url=url, client=client, redirect=redirect):
                self.assertRedirects(client.get(url), redirect)

    def test_urls_use_correct_template(self):
        """Проверка на то что URL-адрес использует подходящий шаблон."""
        for template, url in TEMPLATES_URLS.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.authorized_client.get(url),
                    template
                )
