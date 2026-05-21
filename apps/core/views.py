from django.shortcuts import render


def amor(request):
    """Endpoint /amor com foto e emoji caindo"""
    return render(request, 'amor.html')
