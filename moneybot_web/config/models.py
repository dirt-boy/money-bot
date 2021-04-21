from django.db import models

# Create your models here.


class Source(models.Model):
    Sources = models.TextChoices('Source', 'STRIPE FACEBOOK PAYPAL')
    description = models.CharField(max_length=60)
    medal = models.CharField(blank=True, choices=Sources.choices, max_length=10)