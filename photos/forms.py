from __future__ import unicode_literals

from django import forms
from django.forms import ModelMultipleChoiceField

from django.contrib.auth.models import User
from .models import Data, Announcement, Profile, UserInfo
from django_summernote.widgets import SummernoteWidget


class DataForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.is_mobile = kwargs.pop('is_mobile', None)

        super(DataForm, self).__init__(*args, **kwargs)

        if user and user.profile.group is not None:
            self.fields['participator'].queryset = UserInfo.objects.filter(group=user.profile.group)

        print(type(self.fields['participator']))

    image = forms.ImageField(label='', widget=forms.ClearableFileInput(
        attrs={
            'id': 'ex_file',
            'name': 'ex_file',
            'onchange': "javascript:document.getElementById('fileName').value = this.value",
        }
    ))

    participator = forms.ModelMultipleChoiceField(
        widget = forms.CheckboxSelectMultiple,
        queryset = UserInfo.objects.none()
    )


    study_start_time = forms.CharField(label='', widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': '공부를 시작한 시간을 입력해 주세요. Ex) 18:30',
            }
        ))

    study_total_duration = forms.IntegerField(label='', widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'placeholder': '스터디 시간을 분 단위으로 써주세요. Ex) 75'
            }
        ))

    title = forms.CharField(label='', widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': '제목을 입력해주세요.',
            }
        ))


    text = forms.CharField(widget=SummernoteWidget())



    class Meta:
        model = Data
        fields = ('text', 'participator', 'image', 'title', 'study_start_time', 'study_total_duration')

    def set_is_mobile(self):
        if self.is_mobile:
            self.fields['text'].widget = forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': '공부한 내용을 써주세요 ʕ•ﻌ•ʔ ♡',
                    }
            )

'''
class ProfileForm(forms.ModelForm):
    student_id = forms.IntegerField(label='', widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'placeholder': '학번을 입력해주세요.'
            }
        ))

    name = forms.CharField(label='', widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': '이름을 입력해주세요.',
            }
        ))

    email = forms.EmailField(label='', widget=forms.EmailInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Email 주소를 입력해주세요',
            }
        ))
    class Meta:
        model = Member
        fields = ('student_id', 'name', 'email')
'''

class AnnouncementForm(forms.ModelForm):
    title = forms.CharField(label='', widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': '제목',
        }
    ))

    content = forms.CharField(widget=SummernoteWidget())

    class Meta:
        model = Announcement
        fields = ('title' , 'content')
