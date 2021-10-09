from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
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
            group=PostURLTests.group,
            text="Тестовый текст",
            author=User.objects.get(username='AuthorForPosts')
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        template_url_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_posts', args=[self.group.slug]
            ),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/post_detail.html': reverse(
                'posts:post_detail', args=[self.post.id]
            ),
            'posts/profile.html': reverse(
                'posts:profile', args=[self.user.username]
            ),
        }
        for template, reverse_name in template_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_url_exists_at_desired_location(self):
        response = self.guest_client.get(reverse(
            'posts:index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_list_url_exists_at_desired_location(self):
        response = self.guest_client.get(reverse(
            'posts:group_posts', args=[self.group.slug]))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_exists_at_desired_location(self):
        response = self.guest_client.get(reverse(
            'posts:profile', args=[self.user.username]))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_exists_at_desired_location(self):
        response = self.guest_client.get(reverse(
            'posts:post_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # def test_add_comment_exists_at_desired_location(self):
    #     response = self.authorized_client.get(reverse(
    #         'posts:add_comment', args=[self.post.id]))
    #     self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_exists_at_desired_location(self):
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get(
            reverse('posts:post_create'),
            follow=True)
        redirect = reverse('login') + '?next=' + reverse('posts:post_create')
        self.assertRedirects(response, redirect)

    def test_404(self):
        response = self.guest_client.get('/404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
