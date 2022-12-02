from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

from ..constants import (INDEX_TEMPLATE, GROUP_LIST_TEMPLATE,
                         PROFILE_TEMPLATE, CREATE_POST_TEMPLATE,
                         POST_DETAIL_TEMPLATE, POST_EDIT_TEMPLATE)

SLUG = 'slug'
USERNAME = 'author'
LOGIN_URL = reverse('users:login')
INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', kwargs={'slug': SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
CREATE_POST_URL = reverse('posts:post_create')
CREATE_REDIR_URL = f'{LOGIN_URL}?next={CREATE_POST_URL}'


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
        cls.EDIT_REDIR_URL = f'{LOGIN_URL}?next={cls.POST_EDIT_URL}'

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
            (INDEX_URL, self.guest, 200),
            (GROUP_LIST_URL, self.guest, 200),
            (PROFILE_URL, self.guest, 200),
            (self.POST_DETAIL_URL, self.guest, 200),
            (CREATE_POST_URL, self.author, 200),
            (self.POST_EDIT_URL, self.author, 200),
            (CREATE_POST_URL, self.guest, 302),
            (self.POST_EDIT_URL, self.guest, 302),
            (self.POST_EDIT_URL, self.another, 302)]
        for url, client, status in cases:
            with self.subTest(url=url, client=client):
                self.assertEqual(client.get(url).status_code, status)

    def test_redirect_cases(self):
        """Проверка редиректа для неавториз и невавтора."""
        cases = [
            (CREATE_POST_URL, self.guest, CREATE_REDIR_URL),
            (self.POST_EDIT_URL, self.guest, self.EDIT_REDIR_URL),
            (self.POST_EDIT_URL, self.another, self.POST_DETAIL_URL)]
        for url, client, redirect in cases:
            with self.subTest(url=url, client=client, redirect=redirect):
                self.assertRedirects(client.get(url), redirect)

    def test_urls_use_correct_template(self):
        """Проверка на то что URL-адрес использует подходящий шаблон."""
        cases = [
            (INDEX_TEMPLATE, INDEX_URL),
            (GROUP_LIST_TEMPLATE, GROUP_LIST_URL),
            (PROFILE_TEMPLATE, PROFILE_URL),
            (CREATE_POST_TEMPLATE, CREATE_POST_URL),
            (POST_EDIT_TEMPLATE, self.POST_EDIT_URL),
            (POST_DETAIL_TEMPLATE, self.POST_DETAIL_URL)]

        for template, url in cases:
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.author.get(url),
                    template
                )
