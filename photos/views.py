from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

from .models import Photo, Data
from .forms import PhotoForm, DataForm

from django.views.generic import ListView

def detail(request, pk):
    # photo = Photo.objects.get(pk=pk)
    photo = get_object_or_404(Photo, pk=pk)
    username = request.COOKIES.get('username', '')

    ctx = {
        'post': photo,
    }

    if username:
        ctx['username'] = username

    return render(request, 'detail.html', ctx)

def upload(request):
    username = request.COOKIES.get('username', '')
    if request.method == "GET":
        form = PhotoForm()
    elif request.method == "POST":
        form = PhotoForm(request.POST, request.FILES)

        if form.is_valid():
            obj = form.save()
            obj.author = username
            obj.save()
            return HttpResponseRedirect(reverse('list'))

    ctx = {
        'form': form,
    }

    if username:
        ctx['username'] = username

    return render(request, 'upload.html', ctx)

def photoList(request):
    username = request.COOKIES.get('username', '')
    picList = Photo.objects.raw('SELECT * FROM photos_photo WHERE author = %s', [username])

    ctx = {
        'list' : picList,
    }

    if username:
        ctx['username'] = username

    return render(request, 'list.html', ctx)

def allList(request):
    username = request.COOKIES.get('username', '')
    picList = Photo.objects.raw('SELECT * FROM photos_photo')

    ctx = {
        'list' : picList,
    }

    if username:
        ctx['username'] = username

    return render(request, 'list.html', ctx)

def homepage(request):
    username = request.COOKIES.get('username', '')

    ctx = {}

    if username:
        ctx['username'] = username

    return render(request, 'home.html', ctx)

def main(request):
    username  = request.COOKIES.get('username', '')

    if request.method == "GET":
        form = DataForm()
    elif request.method == "POST":
        form = DataForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            obj.author = username
            obj.save()

    dataList = Data.objects.raw('SELECT * FROM photos_data WHERE author = %s ORDER BY id DESC', [username])

    ctx = {
            'form': form,
            'list': dataList,
    }

    if username:
        ctx['username'] = username
    else:
        return redirect('loginpage')

    return render(request, 'main.html', ctx)

# User Login Customization

from django.contrib.auth.models import User
from django.contrib import auth

def loginpage(request):
    if request.method == 'POST':
        username = request.POST['username']
        password =  request.POST['password']
        post = User.objects.filter(username=username)
        if post:
            username = request.POST['username']
            response = HttpResponseRedirect(reverse('main'))
            response.set_cookie('username', username, 3600)
            return response
        else:
            return render(request, 'login.html', {})
    return render(request, 'login.html', {})

def profile(request):
    username = request.COOKIES.get('username', '')

    ctx = {}
    if username:
        ctx['username'] = username

    return render(request, 'profile.html', ctx)

def logout(request):
    try:
        response = HttpResponseRedirect(reverse('loginpage'))
        response.delete_cookie('username')
        return response
    except:
        pass
    return render(request, 'home.html', {})


def signup(request):
    if request.method == 'POST':
        if request.POST["password1"] == request.POST["password2"]:
            user = User.objects.create_user(
                    username=request.POST["username"],
                    password=request.POST["password1"])
            auth.login(request, user)
            return redirect("profile")
        return render(request, 'signup.html')

    return render(request, 'signup.html')
