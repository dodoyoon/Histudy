from __future__ import unicode_literals

from django import forms

from .models import Photo, Data, Announcement


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


class AnnouncementForm(forms.ModelForm):
    title = forms.CharField(label='', widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': '제목',
        }
    ))

    content = forms.CharField(label='', widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': '내용',
        }
    ))

    class Meta:
        model = Announcement
        fields = ('title' , 'content')