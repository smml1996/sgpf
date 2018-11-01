from django.contrib.auth.models import User
from django.test import TestCase
from django.contrib.auth import authenticate
from .views import isEmailValid
from .models import Savings_Percentage
from decimal import Decimal

#BEGIN TESTS UNIDAD
class unitTestEmailFunc(TestCase):
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

#BEGIN TESTS INTEGRACIÓN
#begin tests SignUp
class SavingsPercentageTest(TestCase):
    #test para probar si se crea nuevo registro cuando se registra un usuario
    def setUp(self):
        self.credentials = {
            'username': 'Yessica',
            'email': 'yessica@gmail.com',
            'password1': 'gatitos9876',
            'password2': 'gatitos9876'}
    def test_signup(self):
        response = self.client.post('/signup/', self.credentials, follow=True)
        user = User.objects.get(username='Yessica')
        self.assertTrue(user is not None)
        sp = Savings_Percentage.objects.get(user = user)
        self.assertTrue(sp is not None)
        print("sp percentage: ", type(sp.percentage))

        self.assertTrue(sp.percentage is Decimal(0.10))

class SignUpTest(TestCase):
    def setUp(self):
        self.credentials = {
            'username': 'Yessica',
            'email': 'yessica@gmail.com',
            'password1': 'gatitos9876',
            'password2': 'gatitos9876'}
        self.credentialsRequired = {
            'username': 'Anabel',
            'email': 'Anabel@gmail.com',
            'password1': '1234',
            'password2': '1234'
        }
        self.credentials2 = {
            'username': 'Anabel',
            'email': 'Anabel@gmail.com',
            'password1': '1234',
            'password2': '1235'}
    def test_signup(self):
        # send login data
        response = self.client.post('/signup/', self.credentials, follow=True)
        user = User.objects.filter(username = 'Yessica')
        self.assertTrue(len(user) > 0)
    def test_signup2(self):
        # send login data
        response = self.client.post('/signup/', self.credentials2, follow=True)
        user = User.objects.filter(username = 'Anabel')
        self.assertTrue(len(user) == 0)

    def test_signup3(self):
        # send login data
        response = self.client.post('/signup/', self.credentialsRequired, follow=True)
        print(response.context)
        user = User.objects.filter(username = 'Anabel')
        self.assertTrue(len(user) == 0)

#end tests SignUp
#begin tests login
class LogInTest(TestCase):
    def setUp(self):
        self.credentials = {
            'username': 'yessica',
            'password': 'gatitos9876'}
        self.credentialsTest2 = {
            'username': 'yessica',
            'password': '159'
        }
        self.credentialsTest3 = {
            'username': 'Hermenegildo',
            'password': 'perritos1234'
        }
        self.credentialsTest4 = {
            'username': 'Hermenegildo',
            'password': '0'
        }
        User.objects.create_user(**self.credentials)
    def test_login(self):
        response = self.client.post('/login/', self.credentials, follow=True)
        self.assertTrue(response.context['user'].is_active)
    def test_login2(self):
        response = self.client.post('/login/', self.credentialsTest2, follow=True)
        self.assertTrue(not response.context['user'].is_active)
    def test_login3(self):
        response = self.client.post('/login/', self.credentialsTest3, follow=True)
        self.assertTrue(not response.context['user'].is_active)
    def test_login4(self):
        response = self.client.post('/login/', self.credentialsTest4, follow=True)
        self.assertTrue(not response.context['user'].is_active)
#end tests login
