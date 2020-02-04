from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

from .models import Photo, Data, Verification
from .forms import PhotoForm, DataForm

from django.views.generic import ListView
from datetime import datetime, timedelta, timezone
import json, random


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

def photoList(request, user):
    username = request.COOKIES.get('username', '')
    picList = Photo.objects.raw('SELECT * FROM photos_data WHERE author = %s ORDER BY id DESC', [user])

    ctx = {
        'list' : picList,
        'user' : user,
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

def userList(request):
    username = request.COOKIES.get('username', '')
    if username:
        user = User.objects.get(username=username)
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('main')

    userlist = User.objects.raw('SELECT * FROM auth_user')

    ctx = {
        'list' : userlist,
    }
    
    return render(request, 'userlist.html', ctx)

def homepage(request):
    username = request.COOKIES.get('username', '')
    if username:
        user = User.objects.get(username=username)

    ctx = {
        'userobj' : user,
    }

    if username:
        ctx['username'] = username

    return render(request, 'home.html', ctx)

# for Infinite Scroll
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def main(request):
    username  = request.COOKIES.get('username', '')

    if username:
        user = User.objects.get(username=username)
        if user.is_staff is True:
            return redirect('userList')


    if request.method == "GET":
        form = DataForm()
    elif request.method == "POST":
        form = DataForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            obj.author = username

            if user.verification.code is not None:
                obj.code = user.verification.code
                user.verification.code = None
                user.verification.when_saved = None
                user.save()

            obj.save()

    dataList = Data.objects.raw('SELECT * FROM photos_data WHERE author = %s ORDER BY id DESC', [username])

    paginator = Paginator(dataList, 4)
    page = request.GET.get('page', 1)

    try:
        pics = paginator.page(page)
    except PageNotAnInteger:
        pics = paginator.page(1)
    except EmptyPage:
        pics = paginator.page(paginator.num_pages)


    ctx = {
            'form': form,
            'pics': pics,
    }


    if username:
        ctx['username'] = username
        ctx['userobj'] = user
    else:
        return redirect('loginpage')

    return render(request, 'main.html', ctx)

def delete_data(request, pk):
    item = Data.objects.filter(id=pk)
    picList = Photo.objects.raw('SELECT * FROM photos_data WHERE id = %s', [pk])
    ctx = {
        'list' : picList,
        'item' : item,
        'pk' : pk,
    }
    return render(request, 'confirm_delete.html', ctx)

def confirm_delete(request, pk):
    Data.objects.filter(id=pk).delete()
    return redirect('main')


# For verification popup
def popup(request):
    ctx = {}
    username = request.COOKIES.get('username', '')

    if username:
        user = User.objects.get(username=username)
        orig, created = Verification.objects.get_or_create(user=user)

        now_time = datetime.now(timezone.utc)
        all_pins = [format(i, '04') for i in range(1000, 10000)]
        possible = [i for i in all_pins if len(set(i)) > 3]


        if user.verification.when_saved is None:
            user.verification.when_saved = datetime.now(timezone.utc)
            verify_code = random.choice(possible)
            user.verification.code = verify_code
            user.save()
            ctx['code'] = verify_code


        save_time = user.verification.when_saved

        time_diff = now_time - save_time

        if (time_diff.seconds)/3600 >= 1:
            verify_code = random.choice(possible)
            user.verification.code = verify_code
            user.verification.when_saved = now_time
            user.save()
            ctx['code'] = verify_code
        else:
            if user.verification.code is None:
                verify_code = random.choice(possible)
                user.verification.code = verify_code
                user.verification.when_saved = now_time
                user.save()
                ctx['code'] = verify_code
            else:
                ctx['code'] = user.verification.code



        return render(request, 'popup.html', ctx)
    else:
        return redirect("main")

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
