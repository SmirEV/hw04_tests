from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post
from posts.utils import MAX_POSTS_COUNT

User = get_user_model()


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(
            username='Тестовый пользователь №1'
        )
        cls.user2 = User.objects.create_user(
            username='Тестовый пользователь №2'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user1,
            group=cls.group,
        )

        cls.index_page = ('posts:index', None)
        cls.group_page = ('posts:group_list', ['test-slug'])
        cls.profile1_page = ('posts:profile', [cls.user1])
        cls.profile2_page = ('posts:profile', [cls.user2])
        cls.detail_page = ('posts:post_detail', [cls.post.id])
        cls.create_page = ('posts:post_create', None)
        cls.edit_page = ('posts:post_edit', [cls.post.id])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def posts_check_all_fields(self, post):
        """Метод, проверяющий поля поста."""

        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)

    def test_posts_pages_use_correct_template(self):
        """Проверка, использует ли адрес URL соответствующий шаблон."""
        templates_pages_names = (
            (
                'posts/index.html',
                reverse(self.index_page[0])
            ),
            (
                'posts/group_list.html',
                reverse(
                    self.group_page[0], kwargs={'slug': self.group.slug}
                )
            ),
            (
                'posts/profile.html',
                reverse(
                    self.profile1_page[0],
                    args=[self.user1]
                )
            ),
            (
                'posts/post_detail.html',
                reverse(
                    self.detail_page[0], kwargs={'post_id': self.post.pk}
                )
            ),
            (
                'posts/create_post.html',
                reverse(
                    self.create_page[0]
                )
            ),
            (
                'posts/create_post.html',
                reverse(
                    self.edit_page[0],
                    args=[self.post.pk])
            )
        )

        for template, reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client1.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_index_group_profile_show_correct_context_posts(self):
        """Шаблоны index, group_list, profile сформированы
        с правильным контекстом."""
        responses = (
            self.index_page,
            self.group_page,
            self.profile1_page,
        )

        for response in responses:
            with self.subTest(response=response):
                template_address, argument = response
                first_object = self.guest_client.get(
                    reverse(
                        template_address,
                        args=argument
                    )
                ).context['page_obj'][0]
                self.posts_check_all_fields(first_object)

    def test_posts_context_group_list_template(self):
        """
        Проверка, сформирован ли шаблон group_list с
        правильным контекстом.
        Появляется ли пост, при создании на странице его группы.
        """
        template_address, argument = self.group_page
        response = self.authorized_client1.get(
            reverse(
                template_address,
                args=argument
            )
        )

        test_group = response.context['group']

        self.posts_check_all_fields(response.context['page_obj'][0])
        self.assertEqual(test_group, self.group)

    def test_posts_context_post_create_template(self):
        """
        Проверка, сформирован ли шаблон post_create с
        правильным контекстом.
        """
        template_address, argument = self.create_page
        response = self.authorized_client1.get(
            reverse(
                template_address,
                args=argument
            )
        )

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)   # ###

    def test_posts_context_post_edit_template(self):
        """
        Проверка, сформирован ли шаблон post_edit с
        правильным контекстом.
        """
        template_address, argument = self.edit_page
        response = self.authorized_client1.get(
            reverse(template_address,
                    args=argument
                    )
        )

        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_posts_context_profile_template(self):
        """
        Проверка, сформирован ли шаблон profile с
        правильным контекстом.
        """
        template_address, argument = self.profile1_page
        response = self.authorized_client1.get(
            reverse(
                template_address,
                args=argument
            )
        )
        author = response.context['author']
        self.assertEqual(author, self.post.author)

        self.posts_check_all_fields(response.context['page_obj'][0])

    def test_posts_context_post_detail_template(self):
        """
        Проверка, сформирован ли шаблон post_detail с
        правильным контекстом.
        """
        template_address, argument = self.detail_page
        response = self.authorized_client1.get(
            reverse(
                template_address,
                args=argument
            )
        )
        self.posts_check_all_fields(response.context['post'])

    def test_posts_not_from_foreign_group(self):
        """
        Проверка при указании группы поста, попадает
        ли он в другую группу.
        """
        response = self.authorized_client1.get(reverse(*self.index_page))

        group_list = Post.objects.filter(group=self.post.group)  # ### ????
        self.posts_check_all_fields(response.context['page_obj'][0])

        self.assertEqual(self.group, self.post.group)
        self.assertNotIn(self.post.group, group_list)  # ## ???

    def test_post_in_author_profile(self):
        """Пост попадает в профиль к автору, который его написал"""
        template_address, argument = self.profile1_page

        first_object = self.authorized_client1.get(
            reverse(
                template_address,
                args=argument
            )
        ).context['page_obj'][0]

        profile_list = Post.objects.filter(author=self.post.author)

        self.assertIn(first_object, profile_list)

    def test_post_not_in_author_profile(self):
        """Пост не попадает в профиль к автору, который его не написал;"""
        template_address, argument = self.profile2_page

        first_object = self.authorized_client2.get(
            reverse(
                template_address,
                args=argument
            )
        ).context['page_obj'].object_list

        self.assertEqual(len(first_object), 0)

    def test_post_not_another_group(self):
        """Созданный пост не попал в группу, для которой не был предназначен"""
        another_group = Group.objects.create(
            title='Дополнительная тестовая группа',
            slug='test-another-slug',
            description='Тестовое описание дополнительной группы',
        )

        response = self.authorized_client1.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': another_group.slug}
            )
        )

        self.assertEqual(len(response.context['page_obj']), 0)


class PostsPaginatorViewsTests(TestCase):
    ADDITIONAL_POST_COUNT = 3
    PAGE_COUNT = MAX_POSTS_COUNT + ADDITIONAL_POST_COUNT

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый пользователь')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        for count in range(cls.PAGE_COUNT):
            cls.post = Post.objects.create(
                text=f'Тестовый текст поста номер {count}',
                author=cls.user,
            )
        cls.index_page = ('posts:index', None)
        cls.group_page = ('posts:group_list', ['test-slug'])
        cls.profile_page = ('posts: profile', [cls.user])

    def test_posts_if_first_page_has_ten_records(self):
        """Проверка, содержит ли первая страница 10 записей."""
        response = self.authorized_client.get(reverse(*self.index_page))

        self.assertEqual(
            len(
                response.context.get('page_obj').object_list
            ),
            MAX_POSTS_COUNT
        )

    def test_posts_if_second_page_has_three_records(self):
        """Проверка, содержит ли вторая страница 3 записи."""
        response = self.authorized_client.get(
            reverse(*self.index_page) + '?page=2'
        )

        self.assertEqual(
            len(response.context.get('page_obj').object_list),
            self.ADDITIONAL_POST_COUNT
        )
