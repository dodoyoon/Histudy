from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

from .models import Data, Announcement, Profile, Verification, Year, UserInfo, StudentInfo, Group, Current
from .forms import DataForm, AnnouncementForm#, ProfileForm

from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction

from django.db.models import Count, Max, Sum, Subquery, OuterRef, F, Min, Value, DateTimeField, CharField
from django.db.models.expressions import RawSQL

#For Code Verification
from datetime import datetime, timedelta
from django.utils import timezone
import json, random

#CSV import
from tablib import Dataset
import pandas
import magic, copy, csv

# for Infinite Scroll
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# for device detection
from django_user_agents.utils import get_user_agent

from operator import attrgetter, itemgetter # toplist

LOGIN_REDIRECT_URL = '/user_check/'


def current_year():
    return datetime.date.today().year

def current_sem():
    if datetime.date.today().month < 8 and datetime.date.today().month > 1:
        return 1
    else:
        return 2

@staff_member_required
def set_current(request):
    ctx = {}

    currents = Current.objects.all()
    if request.method == 'POST':
        year = request.POST['year']
        if request.POST['semester'] == 'spring':
            semester = 1
        elif request.POST['semester'] == 'fall':
            semester = 2

        if int(year) < 2000:
            pass # 에러 처리
        else:
            try:
                yearobj = Year.objects.get(year=year)
            except:
                yearobj = Year.objects.create(year=year)

        if currents.exists():
            current = currents[0]
            current.year = yearobj
            current.sem = semester
            print(semester)
            print(current.year, current.sem)
            current.save()
        else:
            Current.objects.create(year=yearobj, sem=semester)

    ctx['current'] = Current.objects.all()[0]
    ctx['username'] = request.user.username

    return render(request, 'set_current.html', ctx)

@login_required(login_url=LOGIN_REDIRECT_URL)
def detail(request, pk):
    data = get_object_or_404(Data, pk=pk)
    current = Current.objects.all()[0]
    ctx={}
    if request.user.is_authenticated:
        username = request.user.username
        ctx['userobj'] = request.user
    else:
        return redirect('loginpage')

    if not (request.user.is_staff or (data.group == request.user.profile.group and data.year == current.year and data.sem == current.sem)):
        messages.warning(request, 'invalid access', extra_tags='alert')
        return HttpResponseRedirect(reverse('main'))

    participators = data.participator.all()
    print("detail participators: ", participators)

    ctx = {
        'post': data,
        'username': username,
        'participators': participators,
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

@login_required(login_url=LOGIN_REDIRECT_URL)
def data_upload(request):
    ctx={}

    try:
        user = User.objects.get(pk=request.user.pk)
        ctx['userobj'] = user
        if user.is_staff is True:
            return redirect('userList')
    except User.DoesNotExist:
        return redirect(reverse('loginpage'))

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
            obj.author = user
            # latestid = Data.objects.filter(author=user).order_by('-id')
            # if latestid:
            #     obj.idgroup = latestid[0].idgroup + 1
            # else:
            #     obj.idgroup = 1

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

            # num = user.userinfo.num_posts
            # user.userinfo.num_posts = num + 1
            # user.userinfo.most_recent = obj.date
            # user.userinfo.name = username
            user.save()

            current = Current.objects.all()
            if current.exists():
                yearobj = current[0].year
                semester = current[0].sem
            else:
                year = current_year()
                try:
                    yearobj = Year.objects.get(year=year)
                except:
                    yearobj = Year.objects.create(year=year)
                semester = current_sem()

            obj.group = user.profile.group
            obj.year = yearobj
            obj.sem = semester

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
    if post.group != user.profile.group:
        messages.warning(request, '해당 게시물의 그룹이 아닙니다', extra_tags='alert')
        return HttpResponseRedirect(reverse('main'))

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


def warn_overwrite(request, year_pk, sem):
    ctx={}
    yearobj = Year.objects.get(pk=year_pk)
    userinfo_list = UserInfo.objects.filter(year=yearobj, sem=sem)
    ctx['userinfo_list'] = userinfo_list

    if request.method == 'POST':
        imported_data_string = request.session.get('imported_data_string', None)
        imported_data_json = json.loads(imported_data_string)
        imported_data_list = []

        for data in imported_data_json.items():
            value_list = list(data[1].values())
            imported_data_list.append(copy.deepcopy(value_list))

        # but first remove existing userinfo
        userinfo_list.delete()

        num_of_ppl = len(data[1])
        for i in range(num_of_ppl):
            groupNo = imported_data_list[0][i]
            stuID = imported_data_list[1][i]
            name = imported_data_list[3][i]

            try:
                groupobj = Group.objects.get(no=groupNo)
            except:
                groupobj = Group.objects.create(no=groupNo)

            try:
                student_info_obj = StudentInfo.objects.get(student_id=stuID)
            except:
                student_info_obj = StudentInfo.objects.create(student_id=stuID, name=name)

            UserInfo.objects.create(year=yearobj, sem=sem, group=groupobj, student_info=student_info_obj)

        messages.success(request, 'csv 정보를 성공적으로 덮어씌웠습니다. ', extra_tags='alert')

        return redirect(reverse('csv_upload'))

    else:
        return render(request, 'warn_overwrite.html', ctx)




@csrf_exempt
@staff_member_required
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
        data = request.FILES
        new_usergroup = data['myfile']

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

        year = request.POST['year']
        if request.POST['semester'] == 'spring':
            semester = 1
        elif request.POST['semester'] == 'fall':
            semester = 2

        if int(year) < 2000:
            messages.warning(request, '년도가 2000보다 작습니다', extra_tags='alert')
            return render(request, 'csv_upload.html', ctx)
        else:
            try:
                yearobj = Year.objects.get(year=year)
            except:
                yearobj = Year.objects.create(year=year)


        userinfo_list = UserInfo.objects.filter(year=yearobj, sem=semester)
        if userinfo_list:
            df = pandas.DataFrame(data=list(imported_data))
            request.session['imported_data_string'] = df.to_json()
            return redirect(reverse('warn_overwrite', args=(yearobj.pk, semester)))


        for data in imported_data:
            print("data", data)
            try:
                groupobj = Group.objects.get(no=data[0])
            except:
                groupobj = Group.objects.create(no=data[0])

            try:
                student_info_obj = StudentInfo.objects.get(student_id=data[1])
            except:
                student_info_obj = StudentInfo.objects.create(student_id=data[1], name=data[3])

            UserInfo.objects.create(year=yearobj, sem=semester, group=groupobj, student_info=student_info_obj)

        messages.success(request, 'csv 정보를 저장했습니다. ', extra_tags='alert')

    if username:
        ctx['username'] = username

    return render(request, 'csv_upload.html', ctx)

@csrf_exempt
@staff_member_required
def new_userinfo(request):
    ctx = {}

    if request.method == 'POST':
        year = request.POST['year']
        sem = request.POST['semester']
        student_id = request.POST['student_id']
        name = request.POST['name']
        groupno = request.POST['group']
        try:
            yearobj = Year.objects.get(year=year)
        except:
            yearobj = Year.objects.create(year=year)
        try:
            student_info_obj = StudentInfo.objects.get(student_id=student_id)
        except:
            student_info_obj = StudentInfo.objects.create(student_id=student_id, name=name)
        
        checklist = UserInfo.objects.filter(year=yearobj, sem=sem, student_info=student_info_obj)
        if checklist.exists():
            group = checklist[0].group.no
            msg = '이번 학기 해당 학생의 조가 존재합니다: Group ' + str(group)
            messages.info(request, msg)
        else:
            try:
                groupobj = Group.objects.get(no=groupno)
            except:
                groupobj = Group.objects.create(no=groupno)
            UserInfo.objects.create(year=yearobj, sem=sem, group=groupobj, student_info=student_info_obj)
            messages.info(request, '해당 정보가 성공적으로 생성되었습니다.')
    else:
        pass

    return render(request, 'new_userinfo.html', ctx)

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
        criterion = int(request.POST['criterion'])
        year = request.POST['year']
        sem = request.POST['semester']

        try:
            yearobj = Year.objects.get(year=year)
        except Year.DoesNotExist:
            yearobj = None

        pass_stu_list = UserInfo.objects.filter(year=yearobj, sem=sem).values("group").distinct().annotate(
            total_posts = Count('group__data', distinct=True, filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)),
            no = F('group__no'),
            student_id = F('group__userinfo__student_info__student_id'),
            name = F('group__userinfo__student_info__name'),
            total_participation = Count('group__data', distinct=True, filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)&Q(group__data__participator__student_info__student_id=F('group__userinfo__student_info__student_id'))),
        ).order_by('no', 'student_id').filter(total_participation__gte=criterion)


        response = HttpResponse(content_type = 'text/csv')
        response['Content-Disposition'] = 'attachment; filename="student_final.csv"'

        writer = csv.writer(response, delimiter=',')
        writer.writerow(['group', 'student_id', 'name', '%'])

        for stu in pass_stu_list:
            percent = float(stu['total_participation']) / float(stu['total_posts']) * 100
            percent = round(percent, 2)
            writer.writerow([stu['no'], stu['student_id'], stu['name'], percent])

        return response
    else:
        return render(request, 'export_page.html', ctx)

    return render(request, 'export_page.html', ctx)

@csrf_exempt
def export_all_page(request):
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
        year = request.POST['year']
        sem = request.POST['semester']

        try:
            yearobj = Year.objects.get(year=year)
        except Year.DoesNotExist:
            yearobj = None

        pass_stu_list = UserInfo.objects.filter(year=yearobj, sem=sem).values("group").distinct().annotate(
            total_posts = Count('group__data', distinct=True, filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)),
            no = F('group__no'),
            student_id = F('group__userinfo__student_info__student_id'),
            name = F('group__userinfo__student_info__name'),
            total_participation = Count('group__data', distinct=True, filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)&Q(group__data__participator__student_info__student_id=F('group__userinfo__student_info__student_id'))),
            # total_time = Sum('group__data__study_total_duration', filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)&Q(group__data__participator__student_info__name__icontains=F('group__userinfo__student_info__name'))),
        ).order_by('no', 'student_id')

        for stu in pass_stu_list:
            total_time = stu['total_time']
            if total_time:
                print(stu)


        # response = HttpResponse(content_type = 'text/csv')
        # response['Content-Disposition'] = 'attachment; filename="student_final.csv"'
        #
        # writer = csv.writer(response, delimiter=',')
        # writer.writerow(['이름', '학번', '그룹번호', '그룹 총 스터디 횟수', '개인별 총 스터디 횟수', '개인별 스터디 참여시간(분)'])
        #
        # for stu in pass_stu_list:
        #     writer.writerow([stu['name'], stu['student_id'], stu['no'], stu['total_posts'], stu['total_participation'], stu['total_time']])
        #
        #
        # return response
    else:
        return render(request, 'export_all_page.html', ctx)

    return render(request, 'export_all_page.html', ctx)


@staff_member_required
def photoList(request, group, year, sem):
    # group is group.pk

    yearobj = Year.objects.get(year=year)
    picList = Data.objects.raw('SELECT * FROM photos_data WHERE group_id = %s AND year_id = %s AND sem = %s ORDER BY id DESC', [group, yearobj.pk, sem])
    group_pk = group
    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        if user.is_staff is False:
            return redirect('loginpage')
    else:
        return redirect('loginpage')

    groupno = Group.objects.get(pk=group)

    ctx = {
        'list' : picList,
        'user' : user,
        'year' : year,
        'sem' : sem,
        'group' : groupno.no,
        'group_pk' : group_pk,
    }

    if username:
        ctx['username'] = username

    return render(request, 'list.html', ctx)

import datetime
from django.db.models import Q
@staff_member_required
def userList(request):
    ctx={}
    if request.user.is_authenticated:
        username = request.user.username
        user = request.user
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('loginpage')

    ctx['years'] = Year.objects.all()


    if request.method == 'POST':
        year = request.POST['year']
        sem = request.POST['sem']

        yearobj = Year.objects.get(year=year)
        sem = int(sem)

        ctx['year'] = year
        ctx['sem'] = sem

        if year != 'None' and sem != 'None':
            ctx['chosen_year'] = year
            ctx['chosen_sem'] = sem

    else:
        current = Current.objects.all().first()
        yearobj = current.year
        sem = current.sem
        ctx['year'] = yearobj.year
        ctx['sem'] = sem

    grouplist = UserInfo.objects.filter(year=yearobj, sem=sem).values("group").distinct().annotate(
        num_posts = Count('group__data', distinct=True, filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)),
        recent = Max('group__data__date', filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)), # 해당 학기로 바꿔야함 to fix
        total_dur = Sum('group__data__study_total_duration', distinct=True, filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)),
        no = F('group__no'),
    ).order_by('-num_posts')


    ctx['grouplist'] = grouplist

    '''
    userlist = User.objects.filter(Q(is_staff=False) & Q(userinfo__year__year=year) & Q(userinfo__sem=sem)).annotate(
        num_posts = Count('data'),
        recent = Max('data__date'),
        total_dur = Sum('data__study_total_duration'),
    ).exclude(username='test').order_by('-num_posts', 'recent', 'id')


    ctx['list'] = userlist
    ctx['userobj'] = user
    if username:
        ctx['username'] = username
    '''

    return render(request, 'userlist.html', ctx)

def rank(request):
    ctx = {}
    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        ctx['user'] = user
        ctx['username'] = username

    try:
        current = Current.objects.all().first()
        yearobj = current.year
        sem = current.sem
    except:
        year = current_year()
        sem = current_sem()
        try:
            yearobj = Year.objects.get(year=year)
        except Year.DoesNotExist:
            yearobj = None

    grouplist = UserInfo.objects.filter(year=yearobj, sem=sem).values('group').distinct().annotate(
        num_posts = Count('group__data', distinct=True, filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)),
        recent = Max('group__data__date', filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)), # 해당 학기로 바꿔야함 to fix
        total_dur = Sum('group__data__study_total_duration', distinct=True, filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)),
        no = F('group__no'),
    ).order_by('-num_posts', 'recent')

    # userlist = User.objects.filter(Q(is_staff=False) & Q(userinfo__year__year=year) & Q(userinfo__sem=sem)).annotate(
    #     num_posts = Count('data'),
    #     recent = Max('data__date'),
    #     total_dur = Sum('data__study_total_duration'),
    # ).exclude(username='test').order_by('-num_posts', 'recent', 'id')

    ctx['list'] = grouplist

    return render(request, 'rank.html', ctx)



def top3(request):
    ctx={}

    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('loginpage')

    current = Current.objects.all().first()
    ctx['years'] = Year.objects.all()

    if request.method == 'POST':
        year = request.POST['year']
        sem = request.POST['sem']
        ctx['year'] = year
        ctx['sem'] = sem

        yearobj = Year.objects.get(year=year)

        if year != 'None' and sem != 'None':
            ctx['chosen_year'] = year
            ctx['chosen_sem'] = sem

    else:
        year = current_year()
        sem = current_sem()
        yearobj = current.year
        sem = current.sem
        ctx['year'] = year
        ctx['sem'] = sem

    groupno = UserInfo.objects.filter(year=yearobj, sem=sem).values('group').distinct()
    tenth_date = {}
    for group in groupno:
        data = Data.objects.filter(year=yearobj, sem=sem, group=group['group'])
        if data.exists():
            if data.count() >= 10: #important
                tenth_date[group[str('group')]] = data[9].date #important

    toplist = UserInfo.objects.filter(year=yearobj, sem=sem).values("group").distinct().annotate(
        num_posts = Count('group__data', distinct=True, filter=Q(group__data__year=yearobj)&Q(group__data__sem=sem)),
        no = F('group__no'),
    ).filter(num_posts__gte=10) #important

    for top in toplist:
        if top['no'] in tenth_date.keys():
            top['date'] = tenth_date[top['no']]

    finallist = sorted(toplist, key=itemgetter('date'), reverse=False)
    #toplist = toplist.order_by('date')
    #toplist = sorted(toplist, key=attrgetter('date'))

    #to fix - order by date
    '''
    toplist = User.objects.raw('SELECT id, username, num_posts, date FROM \
                                (SELECT auth_user.id, username, year, sem, \
	                            (SELECT count(*) FROM photos_data WHERE auth_user.username = photos_data.author) AS num_posts, \
	                            (SELECT date FROM photos_data WHERE auth_user.username = photos_data.author AND photos_data.idgroup = 10) AS date \
                                FROM auth_user INNER JOIN photos_userinfo ON auth_user.id = photos_userinfo.user_id INNER JOIN photos_year ON photos_userinfo.year_id = photos_year.id) AS D \
                                WHERE num_posts>9 AND username <> "test" AND year=%s AND sem=%s ORDER BY date LIMIT 3', [year, sem])
    '''

    ctx['list'] = finallist
    ctx['userobj'] = user
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

    try:
        current = Current.objects.all().first()
    except:
        try:
            year = current_year()
            sem = current_sem()
            yearobj = Year.objects.get(year=year)
        except Year.DoesNotExist:
            yearobj = Year.objects.create(year=year)

        try:
            current = Current.objects.get(year=yearobj, sem=sem)
        except Current.DoesNotExist:
            current = Current.objects.create(year=yearobj, sem=sem)

    cur_year = current.year
    cur_sem = current.sem

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

    groupobj = user.profile.group
    dataList = Data.objects.filter(author__profile__group=groupobj, year=cur_year, sem=cur_sem).order_by('-id')

    paginator = Paginator(dataList, 10)
    page = request.GET.get('page', 1)

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    ctx['posts'] = posts
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


@login_required(login_url=LOGIN_REDIRECT_URL)
def group_profile(request, group_pk):
    ctx={}

    group = Group.objects.get(pk=group_pk)
    ctx['group'] = group

    try:
        current = Current.objects.all().first()
        yearobj = current.year
        sem = current.sem
    except Year.DoesNotExist:
        year = current_year()
        yearobj = Year.objects.get(year=year)
        sem = current_sem()
    ctx['year'] = yearobj
    ctx['sem'] = sem

    if yearobj:
        member_list = UserInfo.objects.filter(year=yearobj, sem=sem, group=group).annotate(
            num_posts = Count('data', filter=Q(data__year=yearobj, data__sem=sem)),
            total_time = Sum('data__study_total_duration', filter=Q(data__year=yearobj, data__sem=sem))
        )

        ctx['member_list'] = member_list

    return render(request, 'group_profile.html', ctx)


@login_required(login_url=LOGIN_REDIRECT_URL)
def profile(request):
    ctx={}

    # Tag.objects.filter(person__yourcriterahere=whatever [, morecriteria]).annotate(cnt=Count('person')).order_by('-cnt')[0]
    current = Current.objects.all().first()
    yearobj = current.year
    sem = current.sem
    print(request.user.profile.student_info)
    userinfoobj = UserInfo.objects.get(year=yearobj, sem=sem, student_info=request.user.profile.student_info)
    try:
        user = User.objects.get(pk=request.user.pk)

        # User를 기준으로 하면 가입한 사람만 뜨고, UserInfo를 기준으로 하면 가입하지 않은 사람도 뜬다.
        member_list = UserInfo.objects.filter(year=yearobj, sem=sem, group=userinfoobj.group).annotate(
            num_posts = Count('data', filter=Q(data__year=yearobj, data__sem=sem)),
            total_time = Sum('data__study_total_duration', filter=Q(data__year=yearobj, data__sem=sem))
        )

        ctx['member_list'] = member_list
    except User.DoesNotExist:
        return redirect(reverse('loginpage'))

    return render(request, 'profile.html', ctx)

@staff_member_required
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

    ctx['current'] = Current.objects.all()[0]

    return render(request, 'staff_profile.html', ctx)

@staff_member_required
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

    current = Current.objects.all().first()
    ctx['years'] = Year.objects.all()

    if request.method == 'POST':
        year = request.POST['year']
        sem = request.POST['sem']

        yearobj = Year.objects.get(year=year)
        sem = sem

        if year != 'None' and sem != 'None':
            ctx['chosen_year'] = year
            ctx['chosen_sem'] = sem

    else:
        yearobj = current.year
        year = current.year.year
        sem = current.sem
        ctx['year'] = year
        ctx['sem'] = sem


    '''
    ctx['data'] = Data.objects.raw('SELECT * FROM photos_data INNER JOIN \
        (SELECT MAX(id) as id FROM photos_data GROUP BY author) \
            last_updates ON last_updates.id = photos_data.id INNER JOIN photos_userinfo ON photos_data.user_id = photos_userinfo.user_id INNER JOIN photos_year ON photos_userinfo.year_id = photos_year.id\
                WHERE author <> "kate" AND author <> "test" AND author IS NOT NULL AND year=%s AND sem =%s ORDER BY date DESC', [year, sem])
    '''
    '''
    data_ids = Data.objects.filter(year=yearobj, sem=sem).annotate(
        latest_date=Max('date')
    ).values_list('id', flat=True)

    print(data_ids)
    '''

    model_max_set = Data.objects.filter(year=yearobj, sem=sem).values('group').annotate(
        latest_date = Max('date')
    ).order_by()

    q_statement = Q()
    for pair in model_max_set:
        q_statement |= (Q(group__exact=pair['group']) & Q(date=pair['latest_date']))

    if(len(q_statement)==0):
        data = Data.objects.none()
    else:
        data = Data.objects.filter(q_statement)
    ctx['data'] = data

    return render(request, 'grid.html', ctx)

def logout_view(request):
    try:
        logout(request)
        response = HttpResponseRedirect(reverse('loginpage'))
        return response
    except:
        pass
    return render(request, 'home.html', {})


# def signup(request):
#     ctx = {}
#
#     if request.user.is_authenticated:
#         username = request.user.username
#         user = User.objects.get(username=username)
#         ctx['userobj'] = user
#         if user.is_staff is False:
#             return redirect('main')
#     else:
#         return redirect('loginpage')
#
#     ctx['username'] = username
#     if request.method == 'POST':
#         if request.POST["password1"] == request.POST["password2"]:
#             user = User.objects.create_user(
#                 username=request.POST["username"],
#                 password=request.POST["password1"]
#             )
#
#             this_year = current_year()
#             try:
#                 year = Year.objects.get(year = this_year)
#             except Year.DoesNotExist :
#                 year = None
#
#             if not year:
#                 year = Year(year=this_year)
#                 year.save()
#                 user.userinfo.year = year
#                 user.userinfo.sem = current_sem()
#             else:
#                 user.userinfo.year = year
#                 user.userinfo.sem = current_sem()
#
#             user.save()
#             messages.success(request, '유저가 성공적으로 추가되었습니다.', extra_tags='alert')
#             return redirect("staff_profile")
#
#         else:
#             messages.warning(request, '유저를 만드는데 실패하였습니다.', extra_tags='alert')
#         return render(request, 'signup.html', ctx)
#
#     return render(request, 'signup.html', ctx)


@login_required(login_url=LOGIN_REDIRECT_URL)
@transaction.atomic
def save_profile(request, pk):
    print('save profile')
    user = User.objects.get(pk=pk)

    if user.profile.phone and user.profile.student_id:
        return redirect(reverse('main'))

    if request.method == 'POST':
        profile = user.profile
        try:
            student_info = StudentInfo.objects.get(student_id=request.POST['student_id'])
        except:
            pass #to fix --> inquiry page with message
        profile.student_info = student_info
        profile.phone = "010" + str(request.POST['phone1']) + str(request.POST['phone2'])
        profile.save()
        return redirect(reverse('main'))

    return render(request, 'save_profile.html')



# UserInfo가 없을 때 관리자에게 문의하는 곳
@login_required(login_url=LOGIN_REDIRECT_URL)
@transaction.atomic
def create_userinfo(request, pk):
    messages.info(request, '학우님의 Group을 찾을 수 없습니다. 관리자에게 문의해주세요')
    user = User.objects.get(pk=request.user.pk)
    print(request.user.username)
    print(request.user.last_name)
    try:
        user = User.objects.get(pk=pk)
    except:
        return redirect(reverse('loginpage'))

    if request.method == 'POST':
        student_id = request.POST['student_id']
        email = request.POST['email']
        print(student_id)
        print(email)

    return render(request, 'create_userinfo.html')


def user_check(request):
    if request.user.email.endswith('@handong.edu'):
        try:
            user = User.objects.get(pk=request.user.pk)
            user.email = request.user.email

            # 학교 이메일이 학번으로 시작한다고 가정
            std_id = user.username
            username = user.last_name
            email = user.email

            try:
                current = Current.objects.all().first()
                yearobj = current.year
                sem = current.sem
            except:
                year = current_year()
                try:
                    yearobj = Year.object.get(year=year)
                except:
                    yearobj = Year.object.create(year=year)
                sem = current_sem()

            try:
                student_info_obj = StudentInfo.objects.get(student_id=std_id)
            except StudentInfo.DoesNotExist:
                student_info_obj = StudentInfo.objects.create(student_id=std_id, name=username)

            try:
                user_info = UserInfo.objects.get(year=yearobj, sem=sem, student_info=student_info_obj)
            except UserInfo.DoesNotExist:
                # user info 가 저장안된 유저는 문의 페이지로! (profile아직 생성안됨)
                return redirect(reverse('create_userinfo', args=(user.pk,)))

            try:
                user_profile = user.profile
            except Profile.DoesNotExist:
                user_profile = Profile.objects.create(user=user, name=username, email=email)
                if user_info:
                    user_profile.group = user_info.group

                user_profile.save()
                return HttpResponseRedirect(reverse('save_profile', args=(user.pk,)))

        except(KeyError, User.DoesNotExist):
            return HttpResponseRedirect(reverse('loginpage'))

        return HttpResponseRedirect(reverse('main'))
    else:
        messages.info(request, '한동 이메일로 로그인해주세요.')
        User.objects.filter(pk=request.user.pk).delete()
        return HttpResponseRedirect(reverse('loginpage'))

@staff_member_required
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


def img_download_page(request):
    ctx={}

    if request.user.is_authenticated:
        username = request.user.username
        user = User.objects.get(username=username)
        ctx['userobj'] = user
        if user.is_staff is False:
            return redirect('main')
    else:
        return redirect('loginpage')

    years = Year.objects.all()
    ctx['years'] = years

    if request.method == 'POST':
        year = request.POST['year']
        sem = request.POST['sem']

        if year != 'None' and sem != 'None':
            ctx['chosen_year'] = year
            ctx['chosen_sem'] = sem

            year_obj = Year.objects.get(year=year)
            return redirect('img_download', year_obj.pk)

    else:
        try:
            current = Current.objects.all().first()
            year = current.year.year
            sem = current.sem
        except:
            year = current_year()
            sem = current_sem()
        ctx['year'] = year
        ctx['sem'] = sem

    return render(request, 'img_download_page.html', ctx)

from django.conf import settings
import zipfile
from wsgiref.util import FileWrapper
import os

def img_download(request, pk):
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


    year = Year.objects.get(pk=pk)
    user_list = User.objects.filter(userinfo__year=year)

    export_zip = zipfile.ZipFile("/home/chickadee/projects/HGUstudy/histudy_img.zip", 'w')

    for user in user_list:
        cnt=1
        if not user.is_staff:
            # print(">>> User: " + user.username)
            image_list = Data.objects.raw('SELECT * FROM photos_data WHERE user_id = %s', [user.pk])

            for image in image_list:
                file_name = user.username + '_' + str(cnt) + '.png'
                product_image_url = image.image.url

                image_path = settings.MEDIA_ROOT+ product_image_url[13:]
                image_name = product_image_url; # Get your file name here.

                export_zip.write(image_path, file_name)
                cnt += 1

    export_zip.close()

    wrapper = FileWrapper(open('/home/chickadee/projects/HGUstudy/histudy_img.zip', 'rb'))
    content_type = 'application/zip'
    content_disposition = 'attachment; filename=histudy_img.zip'

    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Disposition'] = content_disposition


    return response
