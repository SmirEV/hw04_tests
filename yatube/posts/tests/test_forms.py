from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from posts.models import Group, Post, User

POST_CREATE_URL = reverse('posts:post_create')
INDEX_URL = reverse('posts:index')
LOGIN_URL = reverse('login')
USERNAME = 'author'
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})


class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.group2 = Group.objects.create(
            title='Тестовое название группы-2',
            slug='test_slug2',
            description='Тестовое описание группы-2',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id},
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id})
        cls.FORM_DATA = {
            'text': 'Тестовый пост формы',
            'group': cls.group.id,
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_posts_forms_create_post(self):
        """Проверка, создает ли форма пост в базе."""
        posts_before = self.authorized_client.get(
            PROFILE_URL).context['page_obj']
        posts_before_count = len(posts_before)

        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=self.FORM_DATA,
        )
        self.assertRedirects(
            response,
            PROFILE_URL
        )

        posts_after = self.authorized_client.get(
            PROFILE_URL).context['page_obj']
        old_posts_count = 0
        for post in posts_after:
            if post in posts_before:
                old_posts_count += 1
            else:
                new_post = post

        self.assertEqual(old_posts_count, posts_before_count)
        self.assertEqual(new_post.text, self.FORM_DATA['text'])
        self.assertEqual(new_post.author, self.author)
        self.assertEqual(new_post.group_id, self.FORM_DATA['group'])

    def test_authorized_user_edit_post(self):
        """Проверка редактирования записи авторизированным клиентом."""
        posts_before = self.authorized_client.get(
            PROFILE_URL).context['page_obj']
        posts_before_count = len(posts_before)

        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group2.id,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
        )
        self.assertRedirects(
            response,
            self.POST_DETAIL_URL
        )

        posts_after = self.authorized_client.get(
            PROFILE_URL).context['page_obj']
        old_posts_count = 0
        for post in posts_after:
            ind = posts_before.index(post)
            if (posts_before[ind].text == post.text
                    and posts_before[ind].group_id == post.group_id):
                old_posts_count += 1
            else:
                edit_post = post
                post_before = posts_before[ind]

        self.assertEqual(old_posts_count + 1, posts_before_count)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(edit_post.text, form_data['text'])
        self.assertEqual(edit_post.author, post_before.author)
        self.assertEqual(edit_post.group_id, form_data['group'])

    def test_nonauthorized_user_create_post(self):
        """Проверка создания записи не авторизированным пользователем."""
        posts_before = self.guest_client.get(INDEX_URL).context['page_obj']
        posts_before_count = len(posts_before)

        response = self.guest_client.post(
            POST_CREATE_URL,
            data=self.FORM_DATA,
        )

        posts_after = self.guest_client.get(INDEX_URL).context['page_obj']
        old_posts_count = 0
        for post in posts_after:
            if post in posts_before:
                old_posts_count += 1

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        redirect = LOGIN_URL + '?next=' + POST_CREATE_URL
        self.assertRedirects(response, redirect)
        self.assertEqual(old_posts_count, posts_before_count)
