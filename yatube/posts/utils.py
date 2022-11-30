from django.core.paginator import Paginator

from .constants import MAX_POSTS_COUNT


def paginator_max_posts_count(request, post_list):
    return Paginator(
        post_list,
        MAX_POSTS_COUNT
    ).get_page(request.GET.get('page'))
