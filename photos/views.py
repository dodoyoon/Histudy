from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

from .models import Photo, Data, Verification, Announcement
from .forms import PhotoForm, DataForm, AnnouncementForm, MemberForm

from django.views.generic import ListView
from datetime import datetime, timedelta
from django.utils import timezone
import json, random

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib import auth

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def detail(request, pk):
    # photo = Photo.objects.get(pk=pk)
    data = get_object_or_404(Data, pk=pk)
    username = request.COOKIES.get('username', '')

    ctx = {
        'post': data,
    }

    if username:
        ctx['username'] = username

    return render(request, 'detail.html', ctx)

from tablib import Dataset

@csrf_exempt
def upload(request):
    username = request.COOKIES.get('username', '')
    ctx = {}

    if username:
        user = User.objects.get(username=username)
        ctx['userobj'] = user
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('main')


    if request.method == 'POST':
        dataset = Dataset()
        new_usergroup = request.FILES['myfile']

        imported_data = dataset.load(new_usergroup.read().decode('utf-8'), format='csv')

        for data in imported_data:
            user_id = "group"+data[0]
            user_pw = data[1]
            user_email = data[2]
            User.objects.create_user(username=user_id,
                                 email=user_email,
                                 password=user_pw)

        messages.success(request, '계정들을 성공적으로 생성하였습니다.', extra_tags='alert')


    if username:
        ctx['username'] = username

    return render(request, 'upload.html', ctx)

def photoList(request, user):
    username = request.COOKIES.get('username', '')
    picList = Data.objects.raw('SELECT * FROM photos_data WHERE author = %s ORDER BY id DESC', [user])
    if username:
        userobj = User.objects.get(username=username)
        if userobj.is_staff is False:
            return redirect('loginpage')
    else:
        return redirect('loginpage')

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

from django.db.models import Count, Max
from django.db.models.expressions import RawSQL
def userList(request):
    username = request.COOKIES.get('username', '')
    if username:
        user = User.objects.get(username=username)
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('main')

    userlist = User.objects.all().annotate(
        num_posts = Count('data'),
        recent = Max('data__date'),
    ).order_by('-num_posts')

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

    ctx={}
    if username:
        user = User.objects.get(username=username)
        ctx = {'userobj' : user}
        ctx = {'username' : username}

    announceList = Announcement.objects.all()
    ctx['list'] = announceList

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
                messages.warning(request, '게시물을 등록에 실패하였습니다. 코드를 생성해주세요.', extra_tags='alert')
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
                messages.success(request, '게시물을 등록하였습니다.', extra_tags='alert')
                return HttpResponseRedirect(reverse('main'))


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
    picList = Data.objects.raw('SELECT * FROM photos_data WHERE id = %s', [pk])

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

def loginpage(request):
    if request.method == 'POST':
        username = request.POST['username']
        password =  request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            post = User.objects.filter(username=username)

            if post:
                login(request, user)
                username = request.POST['username']
                response = HttpResponseRedirect(reverse('main'))
                response.set_cookie('username', username, 3600)
                messages.success(request, '환영합니다.', extra_tags='alert')
                return response
            else:
                messages.warning(request, '다시 로그인 해주세요.', extra_tags='alert')
                return render(request, 'login.html', {})
        else:
            messages.warning(request, '다시 로그인 해주세요.', extra_tags='alert')

    return render(request, 'login.html', {})

def profile(request):
    username = request.COOKIES.get('username', '')

    ctx={}

    if username:
        user = User.objects.get(username=username)
        ctx['userobj'] = user

    if username:
        ctx['username'] = username

    return render(request, 'profile.html', ctx)

def logout_view(request):
    try:
        logout(request)
        response = HttpResponseRedirect(reverse('loginpage'))
        response.delete_cookie('username')
        return response
        messages.success(request, '로그아웃 되었습니다.', extra_tags='alert')
    except:
        pass
    return render(request, 'home.html', {})


def signup(request):
    username  = request.COOKIES.get('username', '')
    ctx = {}

    if username:
        user = User.objects.get(username=username)
        ctx['userobj'] = user
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('loginpage')

    ctx['username'] = username
    if request.method == 'POST':
        if request.POST["password1"] == request.POST["password2"]:
            user = User.objects.create_user(
                    username=request.POST["username"],
                    password=request.POST["password1"])
            auth.login(request, user)
            messages.success(request, '유저가 성공적으로 추가되었습니다.', extra_tags='alert')
            return redirect("profile")

        else:
            messages.warning(request, '유저를 만드는데 실패하였습니다.', extra_tags='alert')
        return render(request, 'signup.html', ctx)

    return render(request, 'signup.html', ctx)

def announce_write(request):
    username  = request.COOKIES.get('username', '')
    ctx = {}
    if username:
        ctx['username'] = username
        user = User.objects.get(username = username)
        ctx['userobj'] = user
        if user.is_staff is False:
            return redirect('announce')
    else:
        return redirect('loginpage')

    if request.method == "GET":
        form = AnnouncementForm()
    elif request.method == "POST":
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            obj.author = username
            obj.save()
            messages.success(request, '공지가 추가되었습니다.', extra_tags='alert')
            return redirect("announce")

    ctx['form'] = form

    return render(request, 'announce_write.html', ctx)

def announce_detail(request, pk):
    post = get_object_or_404(Announcement, pk=pk)
    username = request.COOKIES.get('username', '')

    ctx = {
        'post': post,
    }

    if username:
        ctx['username'] = username

    return render(request, 'announce_content.html', ctx)


def change_password(request):
    username  = request.COOKIES.get('username', '')
    ctx = {}

    if username:
        user = User.objects.get(username=username)
        ctx['userobj'] = user
    else:
        return redirect('loginpage')

    ctx['username'] = username
    if request.method == 'POST':
        old_password = request.POST["old_password"]
        is_pw_correct = authenticate(username=username, password=old_password)
        if is_pw_correct is not None:
            password1 = request.POST["password1"]
            password2 = request.POST["password2"]

            if password1 == password2:
                user.set_password(password1)
                user.save()
                messages.success(request, '비밀번호가 변경 되었습니다.', extra_tags='alert')
                return redirect("profile")

            else:
                messages.warning(request, '바꾸는 비밀번호가 일치해야합니다.', extra_tags='alert')

            return redirect("change_password")
        else:
            messages.warning(request, '현재 비밀번호를 확인해주세요.', extra_tags='alert')
            return render(request, 'change_password.html', ctx)

    return render(request, 'change_password.html', ctx)


def add_member(request):
    username  = request.COOKIES.get('username', '')

    ctx={}

    if username:
        ctx['username'] = username
    else:
        return redirect('loginpage')

    if username:
        user = User.objects.get(username=username)
        ctx['userobj'] = user

    if request.method == "GET":
        form = MemberForm()
    elif request.method == "POST":
        form = MemberForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            obj.author = username
            obj.save()
            messages.success(request, '멤버가 추가되었습니다.', extra_tags='alert')
            return redirect("announce")

    ctx['form'] = form

    return render(request, 'profile.html', ctx)
