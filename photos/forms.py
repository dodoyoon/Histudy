from __future__ import unicode_literals

from django import forms

from .models import Photo, Data


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ('studyDate', 'image', 'content',)

class DataForm(forms.ModelForm):
    text = forms.CharField(label='', widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Please Share ... ʕ•ﻌ•ʔ ♡ (Code Required)',
            }
        ))
    class Meta:
        model = Data
        fields = ('text', 'image',)
