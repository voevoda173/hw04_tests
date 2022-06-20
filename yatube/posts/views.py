from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User
from .utils import pagin


def index(request):
    """
    Метод, предназначенный для вывода данных при
    обращении к главной странице сайта.
    """
    posts = Post.objects.select_related(
        'author',
        'group',
    )
    page_obj = pagin(request, posts)
    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """
    Метод, предназначенный для вывода данных при
    обращении к публикациям в тематической группе.
    """
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related(
        'author',
        'group',
    )
    page_obj = pagin(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """
    Метод, предназначенный для данных
    обо всех записях пользователя.
    """
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related(
        'author',
        'group',
    )
    page_obj = pagin(request, posts)
    context = {
        'author': author,
        'page_obj': page_obj,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """
    Метод, предназначенный для данных
    о деталях записи.
    """
    post = get_object_or_404(Post.objects.select_related(
        'author',
        'group',
    ), id=post_id)
    context = {
        'post': post,
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Метод, предназначенный создания новой записи."""
    form = PostForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()

            return redirect('posts:profile', username=post.author)
    context = {
        'form': form,
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Метод, предназначенный редактирования новой записи."""
    post = get_object_or_404(Post.objects.select_related(
        'author',
        'group',
    ), id=post_id)

    if request.user != post.author:

        return redirect('posts:post_detail', post.pk)

    form = PostForm(request.POST or None, instance=post)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    if not form.is_valid():

        return render(request, 'posts/create_post.html', context)

    form.save()

    return redirect('posts:post_detail', post.pk)
