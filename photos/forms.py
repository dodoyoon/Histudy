from __future__ import unicode_literals

from django import forms

from django.contrib.auth.models import User
from .models import Data, Announcement, Member

class DataForm(forms.ModelForm):
    title = forms.CharField(label='', widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': '제목을 입력해주세요.',
            }
        ))

    text = forms.CharField(label='', widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'placeholder': '공부한 내용을 써주세요 ʕ•ﻌ•ʔ ♡',
            }
        ))

    participator = forms.ModelMultipleChoiceField(
        widget = forms.CheckboxSelectMultiple,
        queryset = Member.objects.none()
    )

    class Meta:
        model = Data
        fields = ('text', 'participator', 'image', 'title')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(DataForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['participator'].queryset = Member.objects.filter(user=user)



class MemberForm(forms.ModelForm):
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


class AnnouncementForm(forms.ModelForm):
    title = forms.CharField(label='', widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': '제목',
        }
    ))

    content = forms.CharField(label='', widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'placeholder': '내용',
        }
    ))

    class Meta:
        model = Announcement
        fields = ('title' , 'content')
