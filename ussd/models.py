from __future__ import unicode_literals

from django.db import models

# Create your models here.

class UssdUser(models.Model):
    msisdn = models.CharField(max_length=12, primary_key=True) #TODO validate msisdn
    network = models.CharField(max_length=32) #TODO restrict to enum
    name = models.CharField(max_length=128)
    goal_item = models.CharField(max_length=128) #TODO should this be an enum
    goal_amount = models.CharField(max_length=128) #TODO Should be an integer field
    #TODO created_at = models.DateTimeField()
    #TODO updated_at = models.DateTimeField()

    def to_dict(self):
        return {
            'msisdn': self.msisdn,
            'name': self.name,
            'goal_item': self.goal_item,
            'goal_amount': self.goal_amount,
            'balance': 0
        }
