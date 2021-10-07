# Прошу прощения, для ускорения процесса разработки
# использовал другие наработки с stackoverflow и от других студентов
# самому не получается полноценно окунуться в тестирование
import re
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.db.models import fields

try:
    from posts.models import Comment
except ImportError:
    assert False, 'Не найдена модель Comment'

try:
    from posts.models import Post
except ImportError:
    assert False, 'Не найдена модель Post'


@pytest.fixture
def post(user):
    from posts.models import Post
    image = tempfile.NamedTemporaryFile(suffix=".jpg").name
    return Post.objects.create(
        text='Тестовый пост 1', author=user, image=image
    )


@pytest.fixture
def user_client(user, client):
    client.force_login(user)
    return client


def search_field(fields, attname):
    for field in fields:
        if attname == field.attname:
            return field
    return None


def search_refind(execution, user_code):
    """Поиск запуска"""
    for temp_line in user_code.split('\n'):
        if re.search(execution, temp_line):
            return True
    return False


class TestComment:

    def test_comment_model(self):
        model_fields = Comment._meta.fields
        text_field = search_field(model_fields, 'text')
        assert text_field is not None
        assert type(text_field) == fields.TextField

        created_field = search_field(model_fields, 'created')
        assert created_field is not None
        assert type(created_field) == fields.DateTimeField
        assert created_field.auto_now_add

        author_field = search_field(model_fields, 'author_id')
        assert author_field is not None
        assert type(author_field) == fields.related.ForeignKey
        assert author_field.related_model == get_user_model()

        post_field = search_field(model_fields, 'post_id')
        assert post_field is not None
        assert type(post_field) == fields.related.ForeignKey
        assert post_field.related_model == Post

    @pytest.mark.django_db(transaction=True)
    def test_comment_add_view(self, client, post):
        try:
            response = client.get(f'/{post.author.username}/{post.id}/comment')
        except Exception as e:
            assert False, f'''Страница `/<username>/<post_id>/comment/`
            работает неправильно. Ошибка: `{e}`'''
        if response.status_code in (301, 302) and (
            response.url == f'/{post.author.username}/{post.id}/comment/'
        ):
            url = f'/{post.author.username}/{post.id}/comment/'
        else:
            url = f'/{post.author.username}/{post.id}/comment'
        assert response.status_code != 404

        response = client.post(url, data={'text': 'Новый коммент!'})
        if not(response.status_code in (301, 302) and (
            response.url.startswith('/auth/login')
        )):
            assert False

    @pytest.mark.django_db(transaction=True)
    def test_comment_add_auth_view(self, user_client, post):
        try:
            response = user_client.get(
                f'/{post.author.username}/{post.id}/comment'
            )
        except Exception as e:
            assert False, f'''Страница `/<username>/<post_id>/comment/`
            работает неправильно. Ошибка: `{e}`'''
        if response.status_code in (301, 302) and response.url == (
            f'/{post.author.username}/{post.id}/comment/'
        ):
            url = f'/{post.author.username}/{post.id}/comment/'
        else:
            url = f'/{post.author.username}/{post.id}/comment'
        assert response.status_code != 404

        text = 'Новый коммент 2!'
        response = user_client.post(url, data={'text': text})

        assert response.status_code in (301, 302)
        comment = Comment.objects.filter(
            text=text, post=post, author=post.author).first()
        assert comment is not None
        assert response.url.startswith(f'/{post.author.username}/{post.id}')
