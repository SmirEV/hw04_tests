from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from posts.models import Group, Post, User

POST_CREATE_URL = reverse('posts:post_create')
LOGIN_URL = reverse('login')


class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='Новый пользователь'
        )
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

        cls.PROFILE_URL = reverse(
            'posts:profile',
            kwargs={'username': cls.author.username})

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
        posts_count = Post.objects.count()

        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=self.FORM_DATA,
        )
        self.assertRedirects(
            response,
            self.PROFILE_URL
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, self.FORM_DATA['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group_id, self.FORM_DATA['group'])

    def test_authorized_user_edit_post(self):
        """Проверка редактирования записи авторизированным клиентом."""
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
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group_id, form_data['group'])

    def test_nonauthorized_user_create_post(self):
        """Проверка создания записи не авторизированным пользователем."""
        posts_count = Post.objects.count()

        response = self.guest_client.post(
            POST_CREATE_URL,
            data=self.FORM_DATA,
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        redirect = LOGIN_URL + '?next=' + POST_CREATE_URL
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)
