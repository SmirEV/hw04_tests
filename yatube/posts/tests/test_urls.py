from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User

from ..constants import (INDEX_TEMPLATE, GROUP_LIST_TEMPLATE,
                         PROFILE_TEMPLATE, CREATE_POST_TEMPLATE)

SLUG = 'slug'
USERNAME = 'author'
LOGIN_URL = reverse('users:login')
INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', kwargs={'slug': SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
CREATE_POST_URL = reverse('posts:post_create')


class PostsUrlsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название для теста',
            slug=SLUG,
            description='Описание для теста',
        )
        cls.user1 = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username=USERNAME + '1')
        cls.post = Post.objects.create(
            author=cls.user1,
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
        self.guest = Client()

        self.author = Client()
        self.author.force_login(self.user1)

        self.another = Client()
        self.another.force_login(self.user2)

        cache.clear()

    def test_all_cases(self):
        """Проверка доступа страниц приложения post для разных юзеров."""
        cases = [
            (INDEX_URL, self.guest),
            (GROUP_LIST_URL, self.guest),
            (PROFILE_URL, self.guest),
            (self.POST_DETAIL_URL, self.guest),
            (CREATE_POST_URL, self.author),
            (self.POST_EDIT_URL, self.author)]
        for url, client in cases:
            with self.subTest(url=url, client=client):
                self.assertEqual(client.get(url).status_code, HTTPStatus.OK)

    def test_redirect_cases(self):
        """Проверка редиректа для неавториз и невавтора."""
        cases = [
            (
                CREATE_POST_URL,
                self.guest,
                LOGIN_URL + '?next=' + CREATE_POST_URL
            ),
            (
                self.POST_EDIT_URL,
                self.guest,
                LOGIN_URL + '?next=' + self.POST_EDIT_URL
            ),
            (
                self.POST_EDIT_URL,
                self.another,
                self.POST_DETAIL_URL
            ),
        ]
        for url, client, redirect in cases:
            with self.subTest(url=url, client=client, redirect=redirect):
                self.assertEqual(client.get(url).status_code, HTTPStatus.FOUND)
                self.assertRedirects(client.get(url), redirect)

    def test_urls_use_correct_template(self):
        """Проверка на то что URL-адрес использует подходящий шаблон."""
        cases = {
            (INDEX_TEMPLATE, reverse('posts:index')),
            (GROUP_LIST_TEMPLATE, reverse(
                'posts:group_list', kwargs={'slug': SLUG})),
            (PROFILE_TEMPLATE, reverse(
                'posts:profile', kwargs={'username': USERNAME})),
            (CREATE_POST_TEMPLATE, reverse('posts:post_create'))}

        for template, url in cases:
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.author.get(url),
                    template
                )
