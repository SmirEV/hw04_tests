from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        act = PostModelTest.post.__str__()
        self.assertEqual(
            act,
            PostModelTest.post.text[:15],
            'Метод __str__ у Post работает неправильно'
        )

        group = PostModelTest.group  # Обратите внимание на синтаксис
        expected_object_name = group.title
        self.assertEqual(
            expected_object_name,
            str(group),
            'Метод __str__ у Group работает неправильно'
        )
