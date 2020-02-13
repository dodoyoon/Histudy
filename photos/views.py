from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

from .models import Photo, Data, Verification
from .forms import PhotoForm, DataForm

from django.views.generic import ListView
from datetime import datetime, timedelta
from django.utils import timezone
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

from tablib import Dataset
from .resources import UserGroupResource

def upload(request):
    username = request.COOKIES.get('username', '')

    if username:
        user = User.objects.get(username=username)
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('main')


    if request.method == 'POST':
        usergroup_resource = UserGroupResource()
        dataset = Dataset()
        new_usergroup = request.FILES['myfile']

        imported_data = dataset.load(new_usergroup.read().decode('utf-8'), format='csv')
        result = usergroup_resource.import_data(dataset, dry_run=True)  # Test the data import

        if not result.has_errors():
            usergroup_resource.import_data(dataset, dry_run=False)  # Actually import now

    if username:
        ctx = {'username' : username }

    return render(request, 'upload.html', ctx)

def photoList(request, user):
    username = request.COOKIES.get('username', '')
    picList = Photo.objects.raw('SELECT * FROM photos_data WHERE author = %s ORDER BY id DESC', [user])
    if username:
        userobj = User.objects.get(username=username)

    ctx = {
        'list' : picList,
        'user' : user,
        'userobj' : userobj,
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

from django.db.models import Count
def userList(request):
    username = request.COOKIES.get('username', '')
    if username:
        user = User.objects.get(username=username)
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('main')

    userlist = User.objects.all().annotate(
        num_posts = Count('data')
    )

    ctx = {
        'list' : userlist,
        'userobj' : user,
    }
    if username:
        ctx['username'] = username

    return render(request, 'userlist.html', ctx)

def homepage(request):
    username = request.COOKIES.get('username', '')
    if username:
        user = User.objects.get(username=username)

    memberList = Photo.objects.raw('SELECT * FROM photos_usergroup')

    ctx = {
        'userobj' : user,
        'list' : memberList,
    }

    if username:
        ctx = {'username' : username}

    return render(request, 'home.html', ctx)

def announce(request):
    username = request.COOKIES.get('username', '')
    if username:
        user = User.objects.get(username=username)
        ctx = {'userobj' : user}
        ctx = {'username' : username}

    return render(request, 'announce.html', ctx)

# for Infinite Scroll
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def main(request):
    username  = request.COOKIES.get('username', '')

    ctx={}

    if username:
        ctx['username'] = username
    else:
        return redirect('loginpage')

    if username:
        user = User.objects.get(username=username)
        ctx['userobj'] = user
        if user.is_staff is True:
            return redirect('userList')
    else:
        return redirect('loginpage')


    if request.method == "GET":
        form = DataForm()
    elif request.method == "POST":
        form = DataForm(request.POST, request.FILES)
        if form.is_valid():
            if user.verification.code is None:
                msg = "코드를 생성해주세요"
                ctx['msg'] = msg
            else:
                obj = form.save()
                obj.user = user
                obj.author = username

                if user.verification.code is not None:
                    obj.code = user.verification.code
                    obj.when_saved = user.verification.when_saved
                    user.verification.code = None
                    user.verification.when_saved = None

                num = user.userinfo.num_posts
                user.userinfo.num_posts = num + 1
                user.userinfo.most_recent = obj.date
                user.userinfo.name = username
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

    ctx['form'] = form
    ctx['pics'] = pics
    ctx['userobj'] = user

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
    item = Data.objects.get(id=pk)
    username = item.author
    user = User.objects.get(username=username)

    if user.userinfo.num_posts > 0:
        user.userinfo.num_posts -= 1
        user.save()

    Data.objects.filter(id=pk).delete()
    return redirect('main')


# For verification popup
def popup(request):
    ctx = {}
    username = request.COOKIES.get('username', '')

    if username:
        user = User.objects.get(username=username)
        orig, created = Verification.objects.get_or_create(user=user)

        now_time = timezone.localtime()
        all_pins = [format(i, '04') for i in range(1000, 10000)]
        possible = [i for i in all_pins if len(set(i)) > 3]


        if user.verification.when_saved is None:
            user.verification.when_saved = now_time
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
    if username:
        user = User.objects.get(username=username)

    memberList = Photo.objects.raw('SELECT * FROM photos_usergroup')

    ctx = {
        'userobj' : user,
        'list' : memberList,
    }

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
    username  = request.COOKIES.get('username', '')

    if username:
        user = User.objects.get(username=username)
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('loginpage')

    ctx = {'username' : username}
    if request.method == 'POST':
        if request.POST["password1"] == request.POST["password2"]:
            user = User.objects.create_user(
                    username=request.POST["username"],
                    password=request.POST["password1"])
            auth.login(request, user)
            return redirect("profile")
        return render(request, 'signup.html', ctx)

    return render(request, 'signup.html', ctx)
