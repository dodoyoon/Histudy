from __future__ import unicode_literals

from django.db import models
from django.urls import reverse_lazy
import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator

class Member(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null = True)
    student_id = models.PositiveIntegerField(validators=[MaxValueValidator(99999999)], null=True)
    name = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    attendance = models.IntegerField(default=0)

    def delete(self, *args, **kwargs):
        self.student_id.delete()
        self.name.delete()
        self.email.delete()
        super(Data, self).delete(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        url = reverse_lazy('detail', kwargs={'pk': self.pk})
        return url

class Data(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null = True)
    image = models.ImageField(upload_to='%Y/%m/%d/orig')
    title = models.CharField(max_length=30, blank=True, null=True)
    text = models.TextField(null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    author = models.TextField(max_length=100, null=True, blank=True)
    participator = models.ManyToManyField(Member)
    code = models.IntegerField(blank=True, null=True)
    when_saved = models.DateTimeField(null=True, blank=True)
    study_time = models.CharField(max_length=50, blank=True, null=True)
    idgroup = models.IntegerField(blank=True, null=True)

    def delete(self, *args, **kwargs):
        self.image.delete()
        self.filtered_image.delete()
        super(Data, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        url = reverse_lazy('detail', kwargs={'pk': self.pk})
        return url



class Announcement(models.Model):
    author = models.TextField(max_length=100)
    date = models.DateTimeField(default=timezone.now)
    title = models.TextField(max_length=100)
    content = models.TextField()

    def delete(self, *args, **kwargs):
        self.author.delete()
        self.date.delete()
        self.title.delete()
        self.content.delete()
        super(Announcement, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        url = reverse_lazy('announce_detail', kwargs={'pk': self.pk})
        return url


class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.TextField()
    img = models.ImageField(upload_to='profile/', null=True)
    num_posts = models.IntegerField(default=0)
    most_recent = models.DateTimeField(null=True, blank=True)

@receiver(post_save, sender=User)
def create_user(sender, instance, created, **kwargs):
    if created:
        this_user = UserInfo.objects.create(user=instance)
        this_user.name = instance.username
        this_user.save()

@receiver(post_save, sender=User)
def save_data(sender, instance, **kwargs):
    instance.userinfo.save()


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
