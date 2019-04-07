# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class User(models.Model):
	id = models.CharField(primary_key=True, max_length=16)
	password_lib = models.CharField(max_length=16)    # base64
	password_space = models.CharField(max_length=16)  # base64
	sessionid_lib = models.CharField(max_length=36)
	sessionid_space = models.CharField(max_length=36)

class Room(models.Model):
	id = models.AutoField(primary_key=True)
	date = models.IntegerField()
	room = models.CharField(max_length=10)
	availability = models.IntegerField()