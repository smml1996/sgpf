from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Savings_Percentage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    percentage = models.DecimalField(decimal_places=2, default=0.1, max_digits=3) # by default user is saving 10% of her/his incomes

class Savings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None) # foreign key
    value = models.DecimalField(decimal_places=2, default=0.0, max_digits=10)
    #the following attributes are used for the savings history view
    month = models.IntegerField()
        #some integer between 1 and 12
    year = models.IntegerField()

    isFinalValue = models.BooleanField(default=False)
        #false: is not yet final
        #True: month has passed and we can finally calculate
