from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


class IndexListView(ListView):
    model = Post
    template_name = 'index.html'
    context_object_name = 'posts'
    paginate_by = 10

    # noinspection PyUnresolvedReferences
    def get_queryset(self):
        return super().get_queryset().select_related(
            'author', 'group').annotate(comments_count=Count('comments'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop('paginator', None)
        context['page'] = context['page_obj']
        return context


class GroupDetailView(DetailView):
    model = Group
    template_name = 'group.html'
    context_object_name = 'group'

    # noinspection PyUnresolvedReferences
    def get_queryset(self):
        posts_queryset = Post.objects.select_related(
            'author').annotate(comments_count=Count('comments'))
        return super().get_queryset().prefetch_related(
            Prefetch('posts', queryset=posts_queryset))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context['group'].posts.all(), 10)
        page_number = self.request.GET.get('page', 1)
        context['page'] = paginator.get_page(page_number)
        return context


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.author = request.user
        obj.save()
        return redirect('posts:index')
    return render(request, 'post_new.html', {'form': form})


# noinspection PyUnresolvedReferences
def profile(request, username):
    posts = Post.objects.select_related(
        'author', 'group').annotate(
        comments_count=Count('comments')).filter(
        author__username=username)
    user_queryset = User.objects.annotate(
        follower_count=Count('follower'),
        following_count=Count('following'),
        subscribed=Count('following', filter=Q(
            following__user=request.user if request.user.is_authenticated
            else None)))
    user = get_object_or_404(user_queryset, username=username)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {'profile': user, 'page': page_obj}
    return render(request, 'profile.html', context)


# noinspection PyUnresolvedReferences
def post_view(request, username, post_id):
    comments_queryset = Comment.objects.select_related(
        'author')
    posts_queryset = Post.objects.select_related(
        'author', 'group').prefetch_related(
        Prefetch('comments', queryset=comments_queryset))
    post = get_object_or_404(posts_queryset, pk=post_id,
                             author__username=username)
    user = User.objects.annotate(
        follower_count=Count('follower'),
        following_count=Count('following'),
        subscribed=Count('following', filter=Q(
            following__user=request.user if request.user.is_authenticated
            else None))).get(username=username)
    form = CommentForm()
    context = {'profile': user, 'post': post,
               'form': form, 'comments': post.comments.all()}
    return render(request, 'post.html', context=context)


# noinspection PyUnresolvedReferences
@login_required
def post_edit(request, username, post_id):
    posts_queryset = Post.objects.select_related('group')
    post = get_object_or_404(posts_queryset, pk=post_id,
                             author__username=username)
    if post.author != request.user:
        return redirect('posts:post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post', username=username, post_id=post_id)
    return render(request, 'post_new.html', {'form': form,
                                             'post': post})


# noinspection PyUnresolvedReferences
@login_required
def post_delete(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if post.author != request.user:
        return redirect('posts:post', username=username, post_id=post_id)
    post.delete()
    return redirect(request.GET.get('next', 'posts:profile'),
                    username=username)


# noinspection PyUnresolvedReferences
@login_required
def add_comment(request, username, post_id):
    posts_queryset = Post.objects.select_related(
        'author', 'group').prefetch_related('comments')
    post = get_object_or_404(posts_queryset, pk=post_id,
                             author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.author = request.user
        obj.post = post
        obj.save()
        return redirect('posts:post', username=username, post_id=post_id)
    context = {'profile': post.author, 'post': post,
               'form': form, 'comments': post.comments.all()}
    return render(request, 'post.html', context=context)


# noinspection PyUnresolvedReferences
@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user).select_related(
        'author', 'group').annotate(comments_count=Count('comments'))
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {'page': page_obj, 'paginator': paginator}
    return render(request, 'follow.html', context)


# noinspection PyUnresolvedReferences
@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author and not Follow.objects.filter(
            user=request.user, author=author).exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect(request.GET.get('next', 'posts:follow_index'))


@login_required
def profile_unfollow(request, username):
    follow = get_object_or_404(Follow, user=request.user,
                               author__username=username)
    follow.delete()
    return redirect(request.GET.get('next', 'posts:follow_index'))


# noinspection PyUnusedLocal
def page_not_found(request, exception):
    return render(
        request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)
