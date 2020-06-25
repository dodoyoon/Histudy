from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

from .models import Data, Announcement, Member, Verification
from .forms import DataForm, AnnouncementForm, MemberForm

from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from django.db.models import Count, Max, Sum
from django.db.models.expressions import RawSQL

#For Code Verification
from datetime import datetime, timedelta
from django.utils import timezone
import json, random


#CSV import
from tablib import Dataset
import magic, copy, csv

# for Infinite Scroll
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# for device detection
from django_user_agents.utils import get_user_agent

def detail(request, pk):
    data = get_object_or_404(Data, pk=pk)
    ctx={}
    if request.user.is_authenticated:
        username = request.user.username
        user = request.user
        ctx['userobj'] = user
    else:
        return redirect('loginpage')

    memberList = Member.objects.filter(data__pk=pk)

    ctx = {
        'post': data,
        'username': username,
        'memberList': memberList,
    }

    now_time = timezone.localtime()
    time_diff = now_time - data.date

    if time_diff.seconds / 3600 < 1 :
        ctx['can_edit'] = True
    else:
        ctx['can_edit'] = False

    return render(request, 'detail.html', ctx)

# For Random Code Generator
all_pins = [format(i, '04') for i in range(1000, 10000)]
possible = [i for i in all_pins if len(set(i)) > 3]

def data_upload(request):
    ctx={}

    if request.user.is_authenticated:
        username = request.user.username
        ctx['username'] = request.user.username
    else:
        return redirect('loginpage')

    if username:
        user = User.objects.get(username=username)
        ctx['userobj'] = user
        if user.is_staff is True:
            return redirect('userList')
    else:
        return redirect('loginpage')

    is_mobile = request.user_agent.is_mobile
    is_tablet = request.user_agent.is_tablet


    now_time = timezone.localtime()

    if user.verification.code_when_saved is None:
        user.verification.code_when_saved = now_time
        verify_code = random.choice(possible)
        user.verification.code = verify_code
        user.save()

    time_diff = now_time - user.verification.code_when_saved


    if (60*10 - time_diff.seconds) > 0:
        ctx['code_time'] = time_diff.seconds
    else:
        ctx['code_time'] = 0


    if request.method == "GET":
        if is_mobile or is_tablet:
            form = DataForm(user=request.user, is_mobile=True)
            form.set_is_mobile()
        else:
            form = DataForm(user=request.user, is_mobile=False)
            form.set_is_mobile()
    elif request.method == "POST":
        form = DataForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            obj = form.save()
            obj.user = user
            obj.author = username
            latestid = Data.objects.filter(author=username).order_by('-id')
            if latestid:
                obj.idgroup = latestid[0].idgroup + 1
            else:
                obj.idgroup = 1

            if user.verification.code is not None:
                if (time_diff.seconds)/60 < 10:
                    obj.code = user.verification.code
                    obj.code_when_saved = user.verification.code_when_saved
                    user.verification.code = None
                    user.verification.code_when_saved = None
                else:
                    user.verification.code = None
                    user.verification.code_when_saved = None
                    messages.warning(request, '코드가 생성된지 10분이 지났습니다.', extra_tags='alert')

            num = user.userinfo.num_posts
            user.userinfo.num_posts = num + 1
            user.userinfo.most_recent = obj.date
            user.userinfo.name = username
            user.save()

            obj.save()
            messages.success(request, '게시물을 등록하였습니다.', extra_tags='alert')
            return HttpResponseRedirect(reverse('main'))
        else:
            messages.warning(request, '모든 내용이 정확하게 입력되었는지 확인해주세요.', extra_tags='alert')

    ctx['form'] = form
    ctx['userobj'] = user

    return render(request, 'upload.html', ctx)


def data_edit(request, pk):
    ctx={}

    if request.user.is_authenticated:
        username = request.user.username
        ctx['username'] = request.user.username
    else:
        return redirect('loginpage')

    if username:
        user = User.objects.get(username=username)
        ctx['userobj'] = user
        if user.is_staff is True:
            return redirect('userList')
    else:
        return redirect('loginpage')

    is_mobile = request.user_agent.is_mobile
    is_tablet = request.user_agent.is_tablet


    # if (60*10 - time_diff.seconds) > 0:
    #     ctx['code_time'] = time_diff.seconds
    # else:
    #     ctx['code_time'] = 0

    # find the target post
    post = Data.objects.get(id=pk)

    if request.method == "GET":
        if is_mobile or is_tablet:
            form = DataForm(user=request.user, is_mobile=True, instance=post)
            form.set_is_mobile()
        else:
            form = DataForm(user=request.user, is_mobile=False, instance=post)
            form.set_is_mobile()
    elif request.method == "POST":
        form = DataForm(request.POST, request.FILES, user=request.user, instance=post)
        if form.is_valid():
            # print(form.cleaned_data)
            post.title = form.cleaned_data['title']
            post.text = form.cleaned_data['text']
            post.participator.set(form.cleaned_data['participator'])
            post.study_start_time = form.cleaned_data['study_start_time']
            post.study_total_duration = form.cleaned_data['study_total_duration']

            post.save()

            messages.success(request, '게시물을 등록하였습니다.', extra_tags='alert')
            return redirect('detail', pk)
        else:
            messages.warning(request, '모든 내용이 정확하게 입력되었는지 확인해주세요.', extra_tags='alert')

    ctx['form'] = form
    ctx['userobj'] = user

    return render(request, 'edit.html', ctx)

@csrf_exempt
def csv_upload(request):
    ctx = {}

    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        ctx['userobj'] = user
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('loginpage')

    if request.method == 'POST':
        dataset = Dataset()
        new_usergroup = request.FILES['myfile']

        csv_file = copy.deepcopy(new_usergroup)

        blob = csv_file.read()
        m = magic.Magic(mime_encoding=True)
        encoding = m.from_buffer(blob)

        if encoding == "iso-8859-1":
            encoding = "euc-kr"

        imported_data = dataset.load(new_usergroup.read().decode(encoding), format='csv')


        if imported_data is None:
            messages.warning(request, 'CSV파일의 Encoding이 UTF-8이거나 EUC-KR형식으로 변형해주세요.', extra_tags='alert')
            redirect('csv_upload')

        group_no = "1"
        group_list = []
        for data in imported_data:
            if group_no == data[0]:
                group_list.append(data)

            else:
                group_list.sort(key=lambda tup: tup[1])

                is_first = 1

                for elem in group_list:
                    if is_first:
                        user_id = "group"+elem[0]
                        user_pw = elem[1]
                        user_email = elem[2]
                        is_first = 0

                    if User.objects.filter(username=user_id).exists():
                        member_student_id = elem[1]
                        member_name = elem[3]
                        member_email = elem[2]
                        Member.objects.create(user=User.objects.get(username=user_id), student_id = member_student_id, name = member_name, email = member_email)
                    else:
                        User.objects.create_user(username=user_id,
                                            email=user_email,
                                            password=user_pw)
                        member_student_id = elem[1]
                        member_name = elem[3]
                        member_email = elem[2]
                        Member.objects.create(user=User.objects.get(username=user_id), student_id = member_student_id, name = member_name, email = member_email)


                group_list.clear()
                group_no = data[0]
                group_list.append(data)


        is_first = 1

        for elem in group_list:
            if is_first:
                user_id = "group"+elem[0]
                user_pw = elem[1]
                user_email = elem[2]
                is_first = 0

            if User.objects.filter(username=user_id).exists():
                member_student_id = elem[1]
                member_name = elem[3]
                member_email = elem[2]
                Member.objects.create(user=User.objects.get(username=user_id), student_id = member_student_id, name = member_name, email = member_email)
            else:
                User.objects.create_user(username=user_id,
                                    email=user_email,
                                    password=user_pw)
                member_student_id = elem[1]
                member_name = elem[3]
                member_email = elem[2]
                Member.objects.create(user=User.objects.get(username=user_id), student_id = member_student_id, name = member_name, email = member_email)

        group_list.clear()

        messages.success(request, '계정들을 성공적으로 생성하였습니다.', extra_tags='alert')

    if username:
        ctx['username'] = username

    return render(request, 'csv_upload.html', ctx)


@csrf_exempt
def export_page(request):
    ctx={}
    if request.user.is_authenticated:
        username = request.user.username
        ctx['username'] = request.user.username
    else:
        return redirect('loginpage')

    if username:
        user = User.objects.get(username=username)
        ctx['userobj'] = user
    else:
        return redirect('loginpage')

    if request.method == 'POST':
        criterion = request.POST['criterion']

        orig_query = 'SELECT username, student_id AS id, name, count_id, count_mem, (count_mem/count_id*100) AS percent FROM photos_member JOIN auth_user ON photos_member.user_id = auth_user.id JOIN (SELECT user_id, COUNT(id) AS count_id FROM photos_data GROUP BY user_id) AS count_data ON photos_member.user_id = count_data.user_id JOIN (SELECT member_id, COUNT(data_id) AS count_mem FROM photos_data_participator JOIN photos_member ON photos_member.id = photos_data_participator.member_id GROUP BY member_id) AS participator ON photos_member.id = participator.member_id WHERE username <> "test" AND count_id >= '

        criterion_str = str(criterion)
        query = orig_query + criterion_str

        member = Data.objects.raw(query)
        response = HttpResponse(content_type = 'text/csv')
        response['Content-Disposition'] = 'attachment; filename="student_final.csv"'

        writer = csv.writer(response, delimiter=',')
        writer.writerow(['group', 'student_id', 'name', '%'])

        for stu in member:
            writer.writerow([stu.username, stu.id, stu.name, stu.percent])

        return response
    else:
        return render(request, 'export_page.html', ctx)

    return render(request, 'export_page.html', ctx)

def photoList(request, user):
    picList = Data.objects.raw('SELECT * FROM photos_data WHERE author = %s ORDER BY id DESC', [user])
    listuser = user
    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        if user.is_staff is False:
            return redirect('loginpage')
    else:
        return redirect('loginpage')

    ctx = {
        'list' : picList,
        'user' : user,
        'listuser' : listuser,
    }

    if username:
        ctx['username'] = username

    return render(request, 'list.html', ctx)



def userList(request):
    if request.user.is_authenticated:
        username = request.user.username
        user = request.user
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('loginpage')

    userlist = User.objects.filter(is_staff=False).annotate(
        num_posts = Count('data'),
        recent = Max('data__date'),
        total_dur = Sum('data__study_total_duration'),
    ).exclude(username='test').order_by('-num_posts', 'recent', 'id')

    ctx = {
        'list' : userlist,
        'userobj' : user,
    }
    if username:
        ctx['username'] = username

    return render(request, 'userlist.html', ctx)

def rank(request):
    ctx = {}
    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        ctx['user'] = user
        ctx['username'] = username

    userlist = User.objects.filter(is_staff=False).annotate(
        num_posts = Count('data'),
        recent = Max('data__date'),
        total_dur = Sum('data__study_total_duration'),
    ).exclude(username='test').order_by('-num_posts', 'recent', 'id')

    ctx['list'] = userlist

    return render(request, 'rank.html', ctx)



def top3(request):
    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('loginpage')

    toplist = User.objects.raw('SELECT id, username, num_posts, date FROM (SELECT id, username, (SELECT count(*) FROM photos_data WHERE auth_user.username = photos_data.author) AS num_posts, (SELECT date FROM photos_data WHERE auth_user.username = photos_data.author AND photos_data.idgroup = 10) AS date FROM auth_user) AS D WHERE num_posts>9 AND username <> "test" ORDER BY date LIMIT 3')

    ctx = {
        'list' : toplist,
        'userobj' : user,
    }
    if username:
        ctx['username'] = username

    return render(request, 'top3.html', ctx)


def announce(request):
    ctx={}
    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        ctx['userobj'] = user
        ctx['username'] = username
    else:
        return redirect('loginpage')

    announceList = Announcement.objects.all()
    ctx['list'] = announceList

    return render(request, 'announce.html', ctx)


def main(request):
    ctx={}

    if request.user.is_authenticated:
        username = request.user.username
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


    is_mobile = request.user_agent.is_mobile
    is_tablet = request.user_agent.is_tablet

    if request.method == "GET":
        if is_mobile or is_tablet:
            form = DataForm(user=request.user, is_mobile=True)
            form.set_is_mobile()
        else:
            form = DataForm(user=request.user, is_mobile=False)
            form.set_is_mobile()

    elif request.method == "POST":
        form = DataForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            obj = form.save()
            obj.user = user
            obj.author = username
            latestid = Data.objects.filter(author=username).order_by('-id')
            if latestid:
                obj.idgroup = latestid[0].idgroup + 1
            else:
                obj.idgroup = 1

            if user.verification.code is not None:
                now_time = timezone.localtime()
                time_diff = now_time - user.verification.code_when_saved

                if (time_diff.seconds)/60 < 10:
                    obj.code = user.verification.code
                    obj.code_when_saved = user.verification.code_when_saved
                    user.verification.code = None
                    user.verification.code_when_saved = None
                else:
                    user.verification.code = None
                    user.verification.code_when_saved = None
                    messages.warning(request, '코드가 생성된지 10분이 지났습니다.', extra_tags='alert')

            num = user.userinfo.num_posts
            user.userinfo.num_posts = num + 1
            user.userinfo.most_recent = obj.date
            user.userinfo.name = username
            user.save()

            obj.save()
            messages.success(request, '게시물을 등록하였습니다.', extra_tags='alert')
            return HttpResponseRedirect(reverse('main'))
        else:
            messages.warning(request, '참여멤버를 지정해주세요.', extra_tags='alert')


    dataList = Data.objects.raw('SELECT * FROM photos_data WHERE author = %s ORDER BY id DESC', [username])

    paginator = Paginator(dataList, 10)
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

def confirm_delete_data(request, pk):
    ctx={}

    if request.user.is_authenticated:
        loginname = request.user.username
        pass
    else:
        return redirect('loginpage')

    item = Data.objects.get(id=pk)
    username = item.author
    user = User.objects.get(username=username)

    if user.userinfo.num_posts > 0:
        user.userinfo.num_posts -= 1
        user.save()

    Data.objects.filter(id=pk).delete()
    return redirect('main')

def confirm_delete_announce(request, pk):
    ctx={}

    if request.user.is_authenticated:
        loginname = request.user.username
        pass
    else:
        return redirect('loginpage')

    item = Announcement.objects.get(id=pk)
    username = item.author
    user = User.objects.get(username=username)

    Announcement.objects.filter(id=pk).delete()
    messages.success(request, '공지가 삭제되었습니다.', extra_tags='alert')
    return redirect('announce')


# User Login Customization

def trim_string(string1):
    return string1.replace(' ','')

@csrf_exempt
def loginpage(request):
    ctx={}
    if request.method == 'POST':
        username = request.POST['username']
        password =  request.POST['password']

        username = trim_string(username)
        password = trim_string(password)

        user = authenticate(username=username, password=password)

        ctx['user_id'] = username

        if user is not None:
            post = User.objects.filter(username=username)

            if post:
                login(request, user)
                username = request.POST['username']
                response = HttpResponseRedirect(reverse('main'))
                messages.success(request, '환영합니다.', extra_tags='alert')
                return response
            else:
                messages.warning(request, '다시 로그인 해주세요.', extra_tags='alert')
                return render(request, 'login.html', ctx)
        else:
            messages.warning(request, '다시 로그인 해주세요.', extra_tags='alert')

    return render(request, 'login.html', ctx)

def group_profile(request, user):
    memuser = User.objects.get(username=user)
    ctx={}

    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        ctx['user'] = user
        if user.is_staff is False:
            return redirect('loginpage')
    else:
        return redirect('loginpage')

    if username:
        ctx['username'] = username

    memberList = Member.objects.filter(user=memuser).annotate(
        num_posts = Count('data'),
        total_time = Sum('data__study_total_duration')
    )
    ctx['list'] = memberList

    return render(request, 'group_profile.html', ctx)


def profile(request):
    ctx={}

    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        ctx['userobj'] = user
    else:
        return redirect('loginpage')

    if username:
        ctx['username'] = username

    memberList = Member.objects.filter(user=user).annotate(
        num_posts = Count('data'),
        total_time = Sum('data__study_total_duration')
    )
    ctx['list'] = memberList

    return render(request, 'profile.html', ctx)

def staff_profile(request):
    ctx={}

    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        ctx['userobj'] = user
    else:
        return redirect('loginpage')

    if username:
        ctx['username'] = username

    return render(request, 'staff_profile.html', ctx)

def grid(request):
    ctx = {}
    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        ctx['userobj'] = user
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('loginpage')

    if username:
        ctx['username'] = username

    ctx['data'] = Data.objects.raw('SELECT * FROM photos_data INNER JOIN (SELECT MAX(id) as id FROM photos_data GROUP BY author) last_updates ON last_updates.id = photos_data.id')

    return render(request, 'grid.html', ctx)

def logout_view(request):
    try:
        logout(request)
        response = HttpResponseRedirect(reverse('loginpage'))
        return response
    except:
        pass
    return render(request, 'home.html', {})


def signup(request):
    ctx = {}

    if request.user.is_authenticated:
        username = request.user.username
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
            messages.success(request, '유저가 성공적으로 추가되었습니다.', extra_tags='alert')
            return redirect("staff_profile")

        else:
            messages.warning(request, '유저를 만드는데 실패하였습니다.', extra_tags='alert')
        return render(request, 'signup.html', ctx)

    return render(request, 'signup.html', ctx)

def announce_write(request):
    ctx = {}
    if request.user.is_authenticated:
        username = request.user.username
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

    ctx = {
        'post': post,
    }

    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username = username)
        ctx['userobj'] = user
        ctx['username'] = username
    else:
        return redirect('loginpage')

    return render(request, 'announce_content.html', ctx)


def change_password(request):
    ctx = {}

    if request.user.is_authenticated:
        username = request.user.username
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
                login(request, user)
                return redirect("profile")

            else:
                messages.warning(request, '바꾸는 비밀번호가 일치해야합니다.', extra_tags='alert')

            return redirect("change_password")
        else:
            messages.warning(request, '현재 비밀번호를 확인해주세요.', extra_tags='alert')
            return render(request, 'change_password.html', ctx)

    return render(request, 'change_password.html', ctx)


def add_member(request):
    ctx={}

    if request.user.is_authenticated:
        username = request.user.username
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
            obj.user = user
            obj.save()
            messages.success(request, '멤버가 추가되었습니다.', extra_tags='alert')
            return redirect("profile")
        else:
            messages.warning(request, '학번을 확인해주세요.', extra_tags='alert')

    ctx['form'] = form

    return render(request, 'member.html', ctx)

def confirm_delete_member(request, pk):
    item = Member.objects.get(id=pk)
    Member.objects.filter(id=pk).delete()
    return redirect('profile')


def confirm_delete_user(request, pk):
    user = User.objects.get(id=pk)
    User.objects.filter(id=pk).delete()
    return redirect('userList')


# For verification popup
def popup(request):
    ctx = {}

    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        orig, created = Verification.objects.get_or_create(user=user)

        now_time = timezone.localtime()


        if user.verification.code_when_saved is None:
            user.verification.code_when_saved = now_time
            verify_code = random.choice(possible)
            user.verification.code = verify_code
            user.save()
            ctx['code'] = verify_code


        save_time = user.verification.code_when_saved

        time_diff = now_time - save_time

        if (time_diff.seconds)/60 >= 10:
            verify_code = random.choice(possible)
            user.verification.code = verify_code
            user.verification.code_when_saved = now_time
            user.save()
            ctx['code'] = verify_code
        else:
            if user.verification.code is None:
                verify_code = random.choice(possible)
                user.verification.code = verify_code
                user.verification.code_when_saved = now_time
                user.save()
                ctx['code'] = verify_code
            else:
                ctx['code'] = user.verification.code

        return render(request, 'popup.html', ctx)
    else:
        return redirect("main")

def inquiry(request):
    ctx = {}

    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        ctx['userobj'] = user
        ctx['username'] = username

    return render(request, 'inquiry.html', ctx)


from django.conf import settings
import zipfile
from wsgiref.util import FileWrapper
import os

def img_download(request):
    home = os.path.expanduser('~')
    location = os.path.join(home, 'Downloads')
    location += '/'

    ctx={}
    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        ctx['userobj'] = user
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('loginpage')


    user_list = User.objects.all()

    export_zip = zipfile.ZipFile("histudy_img.zip", 'w')

    for user in user_list:
        if not user.is_staff:
            # print(">>> User: " + user.username)
            image_list = Data.objects.raw('SELECT * FROM photos_data WHERE user_id = %s', [user.pk])

            for image in image_list:
                product_image_url = image.image.url
                image_path = settings.MEDIA_ROOT+ product_image_url[13:]
                image_name = product_image_url; # Get your file name here.

                export_zip.write(image_path, image_name)


    wrapper = FileWrapper(open('histudy_img.zip', 'rb'))
    content_type = 'application/zip'
    content_disposition = 'attachment; filename=export.zip'

    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Disposition'] = content_disposition

    export_zip.close()
    
    return response
