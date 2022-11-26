from django.views.generic.base import TemplateView
from django.shortcuts import render


class about_author(TemplateView):
    template_name = 'about/author.html'


class about_tech(TemplateView):
    template_name = 'about/tech.html'


def AboutAuthorView(request):
    return render(request, 'about/author.html')


def AboutTechView(request):
    return render(request, 'about/tech.html')
