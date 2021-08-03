from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractUser
from typing import List


class User(AbstractUser):
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True
    

class Message(models.Model):
    email = models.EmailField(max_length=254)
    message = models.TextField(max_length=300)


class DataBefore(models.Model):
    name = models.CharField(max_length=150)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_before')
    file = models.FileField(upload_to='before/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DataFormat(models.Model):
    name = models.CharField(max_length=150)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_formats')
    file = models.FileField(upload_to='format/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ignore_columns = models.CharField(max_length=150) #ArrayField(models.CharField(max_length=30, blank=True), size=50, blank=True)
    use_columns = models.CharField(max_length=150) #ArrayField(models.CharField(max_length=30, blank=True), size=50, blank=True)


class DataFormatClues(models.Model):
    column_name = models.CharField(max_length=150)
    clues = models.CharField(max_length=150)
    format = models.ForeignKey(DataFormat, on_delete=models.CASCADE, related_name='clues')


class DataAfter(models.Model):
    name = models.CharField(max_length=150)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_after')
    file = models.FileField(upload_to='after/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    data_before = models.ForeignKey(DataBefore, on_delete=models.DO_NOTHING)
    data_format = models.ForeignKey(DataFormat, on_delete=models.DO_NOTHING)
