from __future__ import unicode_literals

from django import forms

from .models import Photo, Data


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ('studyDate', 'image', 'content',)

class DataForm(forms.ModelForm):
    class Meta:
        model = Data
        fields = ('text', 'image',)
