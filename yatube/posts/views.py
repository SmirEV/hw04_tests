from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required

from .models import Group, Post, User
from .forms import PostForm
from posts.utils import page_split


def index(request):
    post_list = Post.objects.all()
    page_obj = page_split(request, post_list)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = page_split(request, post_list)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()

    page_obj = page_split(request, post_list)

    context = {
        'page_obj': page_obj,
        'author': author,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            post = form.save(False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)

    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post_for_edit = get_object_or_404(Post, pk=post_id)

    if post_for_edit.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(request.POST or None, instance=post_for_edit)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    context = {
        'post_for_edit': post_for_edit,
        'form': form,
        'is_edit': True,
    }

    return render(request, 'posts/create_post.html', context)
