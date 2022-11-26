from django.core.paginator import Paginator

MAX_POSTS_COUNT = 10


def page_split(request, post_list):
    paginator = Paginator(post_list, MAX_POSTS_COUNT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
