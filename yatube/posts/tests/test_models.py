from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост больше чем на 15 символов =(',
        )

    def test_post_models_have_correct_object_names(self):
        self.post = PostModelTest.post
        self.assertEqual(self.post.text[:15], str(self.post))

    def test_post_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_post_help_text(self):
        post = PostModelTest.post
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу'
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_group_models_have_correct_object_names(self):
        group = GroupModelTest.group
        self.assertEqual(group.slug, str(group))

    def test_group_verbose_name(self):
        group = GroupModelTest.group
        field_verboses = {
            'title': 'Заголовок',
            'description': 'Описание'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост больше чем на 15 символов =(((',
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user,
            post=cls.post
        )

    def test_comment_model_have_correct_object_names(self):
        self.post = CommentModelTest.comment
        self.assertEqual(self.post.text[:15], str(self.post))

    def test_comment_verbose_name(self):
        comment = CommentModelTest.comment
        field_verboses = {
            'text': 'Текст комментария',
            'created': 'Дата комментария',
            'author': 'Автор',
            'post': 'Пост'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).verbose_name, expected)
