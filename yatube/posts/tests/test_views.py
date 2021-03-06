from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

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
        cls.subscribed_user = User.objects.create_user(
            username='Подписавшийся пользователь'
        )
        cls.unsubscribed_user = User.objects.create_user(
            username='Отписавшийся пользователь'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            group=PostPagesTests.group,
            text="Тестовый текст",
            author=PostPagesTests.author,
            image=uploaded,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user)

    def checking_post_context(self, page_object):
        self.assertEqual(page_object.text, PostPagesTests.post.text)
        self.assertEqual(page_object.author, PostPagesTests.post.author)
        self.assertEqual(page_object.id, PostPagesTests.post.id)
        self.assertEqual(page_object.image, PostPagesTests.post.image)

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

    def test_index_cache(self):
        """Проверка кеширования index"""
        first_response = self.guest_client.get(reverse('posts:index'))
        new_post = Post.objects.create(
            text='Тестовая запись',
            author=PostPagesTests.author,
        )

        last_response = self.guest_client.get(reverse('posts:index'))

        self.assertEqual(first_response.content, last_response.content)

        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))

        self.assertIn(new_post, response.context['page_obj'])

    def test_followers_see_followed_author_post(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан"""
        subscribed_user = PostPagesTests.subscribed_user

        Follow.objects.create(author=PostPagesTests.author,
                              user=subscribed_user)
        authorized_subscribed = Client()
        authorized_subscribed.force_login(subscribed_user)
        response_subscribed = authorized_subscribed.get(
            reverse('posts:follow_index')
        )
        page_object = response_subscribed.context['page_obj'][0]
        self.checking_post_context(page_object)

    def test_unfollowers_dont_see_author_posts(self):
        """Новая запись пользователя не появляется в ленте тех, кто на него
        не подписан"""
        subscribed_user = PostPagesTests.subscribed_user
        unsubscribed_user = PostPagesTests.unsubscribed_user
        Follow.objects.create(author=PostPagesTests.author,
                              user=unsubscribed_user)
        new_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        new_uploaded = SimpleUploadedFile(
            name='new.gif',
            content=new_gif,
            content_type='image/gif'
        )
        Post.objects.create(
            text='Пост третьего пользователя',
            author=subscribed_user,
            image=new_uploaded
        )
        authorized_unsubscribed = Client()
        authorized_unsubscribed.force_login(unsubscribed_user)
        response_unsubscribed = authorized_unsubscribed.get(
            reverse('posts:follow_index')
        )
        page_object_unsub = response_unsubscribed.context['page_obj'][0]
        self.checking_post_context(page_object_unsub)

    def test_profile_follow(self):
        """Проверка системы подписок"""
        unsubscribed_user = PostPagesTests.unsubscribed_user
        subscribed_user = PostPagesTests.subscribed_user

        self.assertFalse(
            Follow.objects.filter(
                author=unsubscribed_user,
                user=subscribed_user
            ).exists())
        follow_num = Follow.objects.count()
        authorized_subscribed = Client()
        authorized_subscribed.force_login(subscribed_user)
        authorized_subscribed.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': unsubscribed_user}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                author=unsubscribed_user,
                user=subscribed_user
            ).exists()
        )
        follow_num_check = Follow.objects.count()
        self.assertEqual(follow_num + 1, follow_num_check)

    def test_profile_unfollow(self):
        """Проверка системы отписок"""
        unsubscribed_user = PostPagesTests.unsubscribed_user
        subscribed_user = PostPagesTests.subscribed_user

        Follow.objects.create(author=unsubscribed_user,
                              user=subscribed_user)
        follow_num = Follow.objects.count()
        authorized_subscribed = Client()
        authorized_subscribed.force_login(subscribed_user)
        authorized_subscribed.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': unsubscribed_user}
            )
        )
        follow_num_check = Follow.objects.count()
        self.assertEqual(follow_num - 1, follow_num_check)


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
