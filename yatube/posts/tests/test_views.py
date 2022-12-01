from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

from ..constants import MAX_POSTS_COUNT

SLUG1 = 'slug1'
SLUG2 = 'slug2'
USERNAME1 = 'username1'
USERNAME2 = 'username2'
INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse(
    'posts:group_list',
    kwargs={'slug': SLUG1})
ANOTHER_GROUP_LIST_URL = reverse(
    'posts:group_list',
    kwargs={'slug': SLUG2})
PROFILE1_URL = reverse(
    'posts:profile',
    kwargs={'username': USERNAME1})
PROFILE2_URL = reverse(
    'posts:profile',
    kwargs={'username': USERNAME2})
CREATE_PAGE_URL = reverse('posts:post_create')


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username=USERNAME1)
        cls.user2 = User.objects.create_user(username=USERNAME2)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG1,
            description='Тестовое описание')
        cls.another_group = Group.objects.create(
            title='Дополнительная тестовая группа',
            slug=SLUG2,
            description='Тестовое описание дополнительной группы')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user1,
            group=cls.group)
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.pk})
        cls.EDIT_PAGE_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id})

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
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.pk, self.post.pk)

    def test_index_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(INDEX_URL)
        self.assertEqual(len(response.context['page_obj']), 1)
        self.posts_check_all_fields(response.context['page_obj'][0])

    def test_groups_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(GROUP_LIST_URL)
        group = response.context['group']
        self.assertEqual(group, self.group)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(
            group.description,
            self.group.description)
        self.assertEqual(len(response.context['page_obj']), 1)
        self.posts_check_all_fields(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(PROFILE1_URL)
        self.assertEqual(response.context['author'], self.user1)
        self.assertEqual(len(response.context['page_obj']), 1)
        self.posts_check_all_fields(response.context['page_obj'][0])

    def test_posts_context_post_detail_template(self):
        """Проверка, сформирован ли шаблон post_detail"""
        self.posts_check_all_fields(
            self.authorized_client.get(self.POST_DETAIL_URL).context['post'])

    def test_post_not_another_group(self):
        """Созданный пост не попал в группу, для которой не был предназначен"""
        self.assertNotIn(
            self.post,
            self.authorized_client.get(
                ANOTHER_GROUP_LIST_URL
            ).context['page_obj'])


class PostsPaginatorViewsTests(TestCase):
    ADDITIONAL_POST_COUNT = 3
    PAGE_COUNT = MAX_POSTS_COUNT + ADDITIONAL_POST_COUNT

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME1)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG1,
            description='Тестовое описание')
        Post.objects.bulk_create(
            Post(
                text=f'Текст {i}',
                author=cls.user,
                group=cls.group
            ) for i in range(cls.PAGE_COUNT))

    def test_count_records_at_pages(self):
        """Проверка, содержат ли страницы нужное количество записей"""
        cases = [
            (INDEX_URL, MAX_POSTS_COUNT),
            (INDEX_URL + '?page=2', self.ADDITIONAL_POST_COUNT),
            (GROUP_LIST_URL, MAX_POSTS_COUNT),
            (GROUP_LIST_URL + '?page=2', self.ADDITIONAL_POST_COUNT),
            (PROFILE1_URL, MAX_POSTS_COUNT),
            (PROFILE1_URL + '?page=2', self.ADDITIONAL_POST_COUNT)]
        for url, posts_count in cases:
            response = self.authorized_client.get(url)
            with self.subTest(url=url, posts_count=posts_count):
                self.assertEqual(
                    len(response.context.get('page_obj').object_list),
                    posts_count)
