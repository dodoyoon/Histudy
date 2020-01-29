from __future__ import unicode_literals

from django.db import models
from django.urls import reverse_lazy
import datetime

class Photo(models.Model):
    image = models.ImageField(upload_to='%Y/%m/%d/orig')
    content = models.TextField(max_length=500, null=True, blank=True)
    studyDate = models.DateField(default=datetime.date.today)
    author = models.TextField(max_length=100, null=True, blank=True)

    def delete(self, *args, **kwargs):
        self.image.delete()
        self.filtered_image.delete()
        super(Photo, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        url = reverse_lazy('detail', kwargs={'pk': self.pk})
        return url

class Data(models.Model):
    image = models.ImageField(upload_to='%Y/%m/%d/orig')
    text = models.TextField(max_length=500, null=True, blank=True)
    date = models.DateField(default=datetime.date.today)
    author = models.TextField(max_length=100, null=True, blank=True)

    def delete(self, *args, **kwargs):
        self.image.delete()
        self.filtered_image.delete()
        super(Photo, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        url = reverse_lazy('detail', kwargs={'pk': self.pk})
        return url
