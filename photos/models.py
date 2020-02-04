from __future__ import unicode_literals

from django.db import models
from django.urls import reverse_lazy
import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    date = models.DateTimeField(default=timezone.now)
    author = models.TextField(max_length=100, null=True, blank=True)
    code = models.IntegerField(blank=True, null=True)

    def delete(self, *args, **kwargs):
        self.image.delete()
        self.filtered_image.delete()
        super(Photo, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        url = reverse_lazy('detail', kwargs={'pk': self.pk})
        return url


class Verification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.IntegerField(null=True, blank=True)
    when_saved = models.DateTimeField(null=True, blank=True)

@receiver(post_save, sender=User)
def create_user_verification(sender, instance, created, **kwargs):
    if created:
        Verification.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_verification(sender, instance, **kwargs):
    instance.verification.save()

class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.TextField()
    img = models.ImageField(upload_to='profile/', null=True)
    num_posts = models.IntegerField(default=0)
    most_recent = models.DateTimeField(null=True, blank=True)

@receiver(post_save, sender=User)
def create_user(sender, instance, created, **kwargs):
    if created:
        UserInfo.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_data(sender, instance, **kwargs):
    instance.userinfo.save()