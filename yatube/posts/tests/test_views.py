from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User
# from posts.utils import MAX_POSTS_COUNT, page_split
from ..constants import *


INDEX_TEMPLATE = 'posts/index.html'
GROUP_LIST_TEMPLATE = 'posts/group_list.html'
PROFILE_TEMPLATE = 'posts/profile.html'
POST_DETAIL_TEMPLATE = 'posts/post_detail.html'

CREATE_POST_TEMPLATE = 'posts/create_post.html'
EDIT_POST_TEMPLATE = 'posts/create_post.html'  # ???


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(
            username='username1'
        )
        cls.user2 = User.objects.create_user(
            username='username2'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.another_group = Group.objects.create(
            title='Дополнительная тестовая группа',
            slug='test-another-slug',
            description='Тестовое описание дополнительной группы',
        )

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user1,
            group=cls.group,
        )

        cls.INDEX_URL = reverse('posts:index')
        cls.GROUP_LIST_URL = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug}
        )
        cls.ANOTHER_GROUP_LIST_URL = reverse(
            'posts:group_list',
            kwargs={'slug': cls.another_group.slug}
        )
        cls.PROFILE1_URL = reverse(
            'posts:profile',
            kwargs={'username': cls.user1.username}
        )
        cls.PROFILE2_URL = reverse(
            'posts:profile',
            kwargs={'username': cls.user2.username}
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.pk}
        )
        cls.CREATE_PAGE_URL = reverse(
            'posts:post_create'
        )
        cls.EDIT_PAGE_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def posts_check_all_fields(self, post):
        """Метод, проверяющий поля поста."""
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, self.post.group.id)
        self.assertEqual(post.pk, self.post.pk)

    def test_index_group_profile_show_correct_context_posts(self):
        """Шаблоны index, group_list, profile сформированы
        с правильным контекстом."""
        urls = (
            self.INDEX_URL,
            self.GROUP_LIST_URL,
            self.PROFILE1_URL
        )

        for url in urls:
            with self.subTest(URL=url):
                first_object = self.guest_client.get(url).context['page_obj']
                if len(first_object) == 1:
                    self.posts_check_all_fields(first_object[0])
                else:
                    self.assertEqual(len(first_object), 1)

# не понимаю, как добавить его в основной цикл, если тут нет page_obj
    def test_posts_context_post_detail_template(self):
        """Проверка, сформирован ли шаблон post_detail"""
        self.posts_check_all_fields(
            self.authorized_client.get(self.POST_DETAIL_URL).context['post'])

    def test_post_not_another_group(self):
        """Созданный пост не попал в группу, для которой не был предназначен"""
        self.assertNotIn(
            self.post,
            self.authorized_client.get(
                self.ANOTHER_GROUP_LIST_URL
            ).context['page_obj']
        )


class PostsPaginatorViewsTests(TestCase):
    ADDITIONAL_POST_COUNT = 3
    PAGE_COUNT = MAX_POSTS_COUNT + ADDITIONAL_POST_COUNT

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        posts_list = list(
            Post(
                text=f'Текст {i}',
                author=cls.user,
                group=cls.group
            ) for i in range(cls.PAGE_COUNT))
        cls.new_posts = Post.objects.bulk_create(posts_list)

        cls.INDEX_URL = reverse('posts:index')
        cls.GROUP_LIST_URL = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile',
            kwargs={'username': cls.user.username}
        )

        cls.cases = [
            (
                cls.INDEX_URL,
                MAX_POSTS_COUNT
            ),
            (
                cls.INDEX_URL + '?page=2',
                cls.ADDITIONAL_POST_COUNT
            ),
            (
                cls.GROUP_LIST_URL,
                MAX_POSTS_COUNT
            ),
            (
                cls.GROUP_LIST_URL + '?page=2',
                cls.ADDITIONAL_POST_COUNT
            ),
            (
                cls.PROFILE_URL,
                MAX_POSTS_COUNT
            ),
            (
                cls.PROFILE_URL + '?page=2',
                cls.ADDITIONAL_POST_COUNT
            ),
        ]

    def test_count_records_at_index_group_profile_pages(self):
        """Проверка, содержат ли страницы нужное количество записей"""
        for self.case in self.cases:
            url, posts_count = self.case
            response = self.authorized_client.get(url)
            with self.subTest():
                self.assertEqual(
                    len(response.context.get('page_obj').object_list),
                    posts_count)

# не хватает тестов: автор в контексте профиля - что это?
# Группа в контексте Групп-ленты без искажения атрибутов - что это значит?
