from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Котики',
            slug='cat',
            description='Группа о котиках',
        )

        cls.author = User.objects.create_user(
            username='AuthorForPosts'
        )

        cls.post = Post.objects.create(
            group=PostPagesTests.group,
            text="Тестовый текст",
            author=User.objects.get(username='AuthorForPosts')
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def checking_post_context(self, page_object):
        self.assertEqual(page_object.text, PostPagesTests.post.text)
        self.assertEqual(page_object.author, PostPagesTests.post.author)
        self.assertEqual(page_object.id, PostPagesTests.post.id)

    def test_create_post_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:index'))
        page_object = response.context['page_obj'][0]
        self.assertIn('page_obj', response.context)
        self.checking_post_context(page_object)

    def test_group_list_show_correct_context(self):
        group = PostPagesTests.group
        response = self.guest_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': PostPagesTests.group.slug})
        )
        page_object = response.context['page_obj'][0]
        response_group = response.context['group']
        self.checking_post_context(page_object)
        self.assertEqual(response_group.title, group.title)
        self.assertEqual(response_group.slug, group.slug)
        self.assertEqual(response_group.description, group.description)

    def test_profile_show_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:profile', args=[PostPagesTests.author.username]))
        page_object = response.context['page_obj'][0]
        author_object = response.context['author']
        self.checking_post_context(page_object)
        self.assertEqual(author_object.get_full_name(),
                         PostPagesTests.author.get_full_name())
        self.assertEqual(author_object.get_username(),
                         PostPagesTests.author.username)

    def test_post_deail_show_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:post_detail', args=[PostPagesTests.post.id]))
        post_object = response.context['post']
        self.checking_post_context(post_object)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Автор')
        cls.group = Group.objects.create(
            title='Котики',
            slug='cat',
            description='Группа о котиках',
        )
        Post.objects.bulk_create(
            [Post(
                author=cls.author,
                group=PaginatorViewsTest.group,
                text='Тестовый текст')] * 15
        )

    def setUp(self):
        self.client = Client()

    def test_page_records(self):
        first_page = 10
        second_page = 5
        urls = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': PaginatorViewsTest.group.slug}),
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.author.username})
        ]
        for reverses in urls:
            with self.subTest(reverses=reverses):
                self.assertEqual(
                    len(self.client.get(
                        reverses).context.get('page_obj')), first_page)
                self.assertEqual(
                    len(self.client.get(
                        reverses + '?page=2').context.get('page_obj')),
                    second_page
                )
