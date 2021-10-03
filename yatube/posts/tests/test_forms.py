from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Тестовый автор')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Текст тестовой группы',
        )

    def setUp(self):
        self.user = User.objects.get(username='Тестовый автор')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.latest('id')
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=[self.user.username]))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group, self.group)

    def test_edit_post(self):
        post_edit = Post.objects.create(
            text='Текст для редактирования',
            author=self.user,
            group=self.group,
        )
        post_id = post_edit.id
        form_data = {
            'text': 'Текст поста для редактирование',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[
                    post_edit.id]),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', args=[post_edit.id]))
        self.assertEqual(Post.objects.get(id=post_id).text, form_data['text'])
