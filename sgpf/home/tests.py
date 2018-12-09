from django.test import TestCase
from .models import Concept, Daily_Input
from login.models import Savings
from django.contrib.auth.models import User
from .views import get_number_of_days, checkIfSavingExist, get_concepts
from .views import get_current_saving, update_past, can_expense
from datetime import datetime as dt
# Create your tests here.

# BEGIN TESTS UNIDAD

class unitFuncNumDays(TestCase):
    # testing is_email_valid()
    def setUp(self):
        pass
    def test1(self):
        #test mes diciembre
        date = dt(year=2018, month=12, day=1)
        self.assertTrue(get_number_of_days(date)== 31)
    def test2(self):
        #test mes noviembre
        date = dt(year=2018, month=11, day=1)
        self.assertTrue(get_number_of_days(date)== 30)
    def test2(self):
        #test febrero en año bisiesto
        date = dt(year=2016, month=2, day=1)
        self.assertTrue(get_number_of_days(date)== 29)

class unitSavingExist(TestCase):
    #test checkIfSavingExist()
    def setUp(self):
        self.credentials = {
            'username': 'smml1996',
            'password': 'ponisponis',
            'email': 'michellemuroya96@gmail.com'
        }
        User.objects.create_user(**self.credentials) # creacion de user en tabla temporal
        self.user = User.objects.get(username='smml1996')

    def test1(self):
        #test must not exist
        self.assertTrue(len(Savings.objects.all()) == 0)
        checkIfSavingExist(self.user, 2018, 11) # this savings must not exist
        self.assertTrue(len(Savings.objects.filter(user=self.user, month=11,year=2018)) == 1)
        checkIfSavingExist(self.user, 2018, 11) # now it must exist
        self.assertTrue(len(Savings.objects.filter(user=self.user, month=11,year=2018)) == 1) #check that not new register is being created

class unitget_concepts(TestCase):
    #test checkIfSavingExist()
    def setUp(self):
        self.credentials = {
            'username': 'smml1996',
            'password': 'ponisponis',
            'email': 'michellemuroya96@gmail.com'
        }
        User.objects.create_user(**self.credentials) # creacion de user en tabla temporal
        self.user = User.objects.get(username='smml1996')
        c = Concept(name='Concept1', value=100.00, period=0,type=False, user=self.user)
        c.save()
        c = Concept(name='Concept2', value=100.00, period=0,type=False, user=self.user, is_disabled=True)
        c.save()

    def test1(self):
        #test must not exist
        self.assertTrue(len(Concept.objects.all()) == 2)
        self.assertTrue(len(get_concepts(self.user)) == 1)

class unitget_current_saving(TestCase):
    #test get_current_saving
    def setUp(self):
        self.credentials = {
            'username': 'smml1996',
            'password': 'ponisponis',
            'email': 'michellemuroya96@gmail.com'
        }
        User.objects.create_user(**self.credentials) # creacion de user en tabla temporal
        self.user = User.objects.get(username='smml1996')
        checkIfSavingExist(self.user, year=2018, month=11)
        s = Savings.objects.get(user=self.user,year=2018,month=11)
        s.value+=10
        s.save()

    def test1(self):
        #testing no period
        self.assertTrue(get_current_saving(self.user) == 10)
        #add one daily saving
        c = Concept(user=self.user, value=100, period=1, type=False)
        c.save()
        d = Daily_Input(user=self.user, concept=c, value=100, savings_value=10, date_from=dt(year=2018, month=11, day=1))
        d.save()
        self.assertTrue(get_current_saving(self.user, d=1, month=11, year=2018)==20)
        # add one biweekly saving
        c = Concept(user=self.user, value=100, period=2, type=False)
        c.save()
        d = Daily_Input(user=self.user, concept=c, value=100, savings_value=10, date_from=dt(year=2018, month=11, day=1))
        d.save()
        self.assertTrue(get_current_saving(self.user, d=1, month=11, year=2018)==20)
        # add one monthly saving
        c = Concept(user=self.user, value=100, period=3, type=False)
        c.save()
        d = Daily_Input(user=self.user, concept=c, value=100, savings_value=10, date_from=dt(year=2018, month=11, day=1))
        d.save()
        self.assertTrue(get_current_saving(self.user, d=1, month=11, year=2018)==20)
        self.assertTrue(get_current_saving(self.user, d=15, month=11, year=2018)==(10*15 + 10*2)) #15 days of dailies plus one no period plus one biweekly
        self.assertTrue(get_current_saving(self.user, d=30, month=11, year=2018)==(10*30 + 10*4)) #30 days of dailies plus one no period plus one biweekly
                                                                                                # plus one monthly plus one biweekly more
class unitupdate_past(TestCase):
    #test update_past()
    def setUp(self):
        self.credentials = {
            'username': 'smml1996',
            'password': 'ponisponis',
            'email': 'michellemuroya96@gmail.com'
        }
        User.objects.create_user(**self.credentials) # creacion de user en tabla temporal
        self.user = User.objects.get(username='smml1996')
        s = Savings(user=self.user, value=10, month=10, year=2018)
        s.save()
    def test1(self):
        update_past(self.user)
        s = Savings.objects.get(user=self.user, month=10,year=2018)
        self.assertTrue(s.isFinalValue == True)


class unitcan_expense(TestCase):
    def setUp(self):
        self.credentials = {
            'username': 'smml1996',
            'password': 'ponisponis',
            'email': 'michellemuroya96@gmail.com'
        }
        User.objects.create_user(**self.credentials) # creacion de user en tabla temporal
        self.user = User.objects.get(username='smml1996')
        c = Concept(user=self.user, value=100, period=1, type=False)
        c.save()
        d = Daily_Input(user=self.user, concept=c, value=900, savings_value=100, date_from=dt(year=2018, month=11, day=1))
        d.save()
    def test1(self):
        self.assertTrue(can_expense(self.user,500))
    def test2(self):
        self.assertTrue(not can_expense(self.user, 1000))
    def test3(self):
        self.assertTrue(can_expense(self.user, 900))
    def test3(self):
        self.assertTrue(not can_expense(self.user, 1001))




# END TESTS UNIDAD
