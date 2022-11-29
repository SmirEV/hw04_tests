from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


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
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

        cls.POST_CREATE_URL = reverse('posts:post_create')
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id},
        )

        cls.FORM_DATA = {
            'text': 'Тестовый пост формы',
            'group': cls.group.id,
        }

        cls.cases_post_form = [
            (
                cls.POST_EDIT_URL,
                0
            ),
            (
                cls.POST_CREATE_URL,
                1
            )
        ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_posts_forms_create_edit_post(self):

        for case in self.cases_post_form:
            post_count_before = Post.objects.count()
            url, add_count = case
            with self.subTest(url=url):
                self.authorized_client.post(url, self.FORM_DATA)

                self.assertEqual(
                    Post.objects.count(),
                    post_count_before + add_count
                )
                self.assertTrue(
                    Post.objects.filter(
                        text=self.FORM_DATA['text'],
                        group=self.FORM_DATA['group'],
                        author=self.author.id,
                    ).exists()
                )

    def test_guest_cant_create_post(self):
        """Проверка, что неавторизованный
        пользователь не может создать пост."""
        post_count_before = Post.objects.count()

        self.guest_client.post(
            reverse('posts:post_create'),
            data={
                'text': 'Тестовый пост формы',
                'author': self.author.id,
                'group': self.group.id,
            },
        )

        self.assertEqual(Post.objects.count(), post_count_before)
