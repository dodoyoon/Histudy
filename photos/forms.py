from __future__ import unicode_literals

from django import forms

from .models import Photo, Data, Announcement, Member


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ('studyDate', 'image', 'content',)

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
    class Meta:
        model = Data
        fields = ('text', 'image', 'title')

class MemberForm(forms.ModelForm):
    student_id = forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': '학번을 입력해주세요.'
        }
    )

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
