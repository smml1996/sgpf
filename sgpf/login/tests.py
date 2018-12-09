from django.contrib.auth.models import User
from django.test import TestCase
from django.contrib.auth import authenticate
from .views import isEmailValid
from .models import Savings_Percentage
from decimal import Decimal

#BEGIN TESTS UNIDAD
class Unit_Test_Email_Func(TestCase):
    # testing isEmailValid()
    def setUp(self):
        self.credentials = {
            'username': 'smml1996',
            'password': 'ponisponis',
            'email': 'michellemuroya96@gmail.com'
        }
        User.objects.create_user(**self.credentials) # creacion de user en tabla temporal
    def test_email(self):
        self.assertTrue(isEmailValid('michellemuroya96@gmail.com') == False) # el email ya esta en uso por tanto no es valido
    def test_email2(self):
        self.assertTrue(isEmailValid('michelle@gmai.com') == True) # el mail no esta en uso, si es valido
# END TESTS UNIDAD
