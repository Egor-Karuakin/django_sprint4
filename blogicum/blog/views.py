from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import Http404
from django.db.models import Count
from .models import Post, Comment, Category
from .forms import PostForm, CommentForm

User = get_user_model()


def get_published_posts():
    """Возвращает QuerySet опубликованных постов"""
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')


def get_paginated_posts(request, posts):
    """Возвращает пагинированный список постов"""
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    posts = get_published_posts()
    page_obj = get_paginated_posts(request, posts)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    is_author = request.user == post.author
    
    if (not post.is_published or 
        post.pub_date > timezone.now() or 
        not post.category.is_published):
        if not is_author:
            raise Http404("Post not available")
    
    comments = post.comments.all()
    form = CommentForm()
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = get_published_posts().filter(category=category)
    page_obj = get_paginated_posts(request, posts)
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj
    })


def profile(request, username):
    user = get_object_or_404(User, username=username)
    if request.user == user:
        posts = Post.objects.filter(author=user).order_by('-pub_date')
    else:
        posts = get_published_posts().filter(author=user)
    page_obj = get_paginated_posts(request, posts)
    return render(request, 'blog/profile.html', {
        'profile': user,
        'page_obj': page_obj
    })


def registration(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:profile', username=user.username)
    else:
        form = UserCreationForm()
    return render(request, 'registration/registration_form.html', {'form': form})


@login_required
def edit_profile(request, username):
    user = get_object_or_404(User, username=username)
    if request.user != user:
        return redirect('blog:profile', username=user.username)
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=user.username)
    else:
        form = UserChangeForm(instance=user)
    return render(request, 'registration/edit_profile.html', {'form': form, 'profile': user})


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.pk)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.pk)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'post': post})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
    return redirect('blog:post_detail', post_id=post.pk)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/comment.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {'comment': comment})