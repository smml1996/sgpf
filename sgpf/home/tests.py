from django.test import TestCase
from .models import Concept, DailyInput
from django.contrib.auth.models import User
# Create your tests here.


class AddConceptTest(TestCase):
    def setUp(self):
        self.credentials = {
            'username': 'user1',
            'password': 'ponisponis'}
        self.formParameters = {
            'isNewConcept': -1,
            'name': 'Concepto Prueba',
            'value': 500.8,
            'period': 1,
            'isExpense': 0
        }
        User.objects.create_user(**self.credentials)
    def test_add_concept(self):
        response = self.client.post('/login/', self.credentials, follow=True)
        # should be logged in now
        self.assertTrue(response.context['user'].is_active)

        response = self.client.post('/conf/', self.formParameters,follow=True)
        self.assertTrue(Concept.objects.filter(id_user=response.context['user'].id)[0].name == 'Concepto Prueba')

class DeleteConceptTest(TestCase):
    #test de integracion
    def setUp(self):
        self.credentials = {
            'username': 'user1',
            'password': 'ponisponis'}
        self.formParameters = {
            'isNewConcept': -1,
            'name': 'Concepto Prueba',
            'value': 500.8,
            'period': 1,
            'isExpense': 0
        }
        User.objects.create_user(**self.credentials)
    def test_delete_concept(self):
        response = self.client.post('/login/', self.credentials, follow=True)
        # should be logged in now
        self.assertTrue(response.context['user'].is_active)
        idUser = response.context['user'].id

        response = self.client.post('/conf/', self.formParameters,follow=True)
        sizePreviousQuery = len(Concept.objects.filter(id_user=idUser));
        self.assertTrue(Concept.objects.filter(id_user=idUser)[0].name == 'Concepto Prueba')
        concepto_id = Concept.objects.filter(id_user=idUser)[0].id
        response = self.client.get('/delete_concept/', {'csrfmiddlewaretoken':response.context['csrf_token'],'id_concept':concepto_id})

        self.assertTrue(Concept.objects.filter(name='Concepto Prueba')[0].is_disabled)
        self.assertTrue(len(Concept.objects.filter(id_user=idUser)) == sizePreviousQuery )


class AddDailyInputTest(TestCase):
    def setUp(self):
        self.credentials = {
            'username': 'user1',
            'password': 'ponisponis'}
        self.formParametersDaily = {
            'from_date':'13/10/2018',
        }
        self.formParametersConcept = {
            'isNewConcept': -1,
            'name': 'Concepto Prueba',
            'value': 500.8,
            'period': 1,
            'isExpense': 0
        }
        User.objects.create_user(**self.credentials)
    def test_addDaily_concept(self):
        response = self.client.post('/login/', self.credentials, follow=True)
        # should be logged in now
        self.assertTrue(response.context['user'].is_active)
        idUser = response.context['user'].id
        response = self.client.post('/conf/', self.formParametersConcept,follow=True)
        concepto_id = Concept.objects.filter(id_user=idUser)[0].id
        value = Concept.objects.filter(id_user=idUser)[0].value
        self.formParametersDaily['value'] = value
        self.formParametersDaily['id_concepto']= concepto_id
        response = self.client.post('/daily_input/', self.formParametersDaily,follow=True)
        sizeQuery = len(DailyInput.objects.filter(id_user=idUser, value=value, id_concept=concepto_id))
        self.assertTrue(sizeQuery==1)

class DeleteDailyInputTest(TestCase):
    #integrado
    def setUp(self):
        self.credentials = {
            'username': 'user1',
            'password': 'ponisponis'}
        self.formParametersDaily = {
            'from_date':'13/10/2018',
        }
        self.formParametersConcept = {
            'isNewConcept': -1,
            'name': 'Concepto Prueba',
            'value': 500.8,
            'period': 1,
            'isExpense': 0
        }
        self.formDeleteDaily = {
            'date':'13/10/2018',
        }
        User.objects.create_user(**self.credentials)

    def test_addDaily_concept(self):
        response = self.client.post('/login/', self.credentials, follow=True)
        # should be logged in now
        self.assertTrue(response.context['user'].is_active)
        idUser = response.context['user'].id
        response = self.client.post('/conf/', self.formParametersConcept,follow=True)
        concepto_id = Concept.objects.filter(id_user=idUser)[0].id
        value = Concept.objects.filter(id_user=idUser)[0].value
        self.formParametersDaily['value'] = value
        self.formParametersDaily['id_concepto']= concepto_id
        response = self.client.post('/daily_input/', self.formParametersDaily,follow=True)
        sizeQuery = len(DailyInput.objects.filter(id_user=idUser, date_from ='2018-10-13',id_concept=concepto_id))
        self.assertTrue(sizeQuery == 1)
        self.formDeleteDaily['id_concept'] = concepto_id
        self.formDeleteDaily['csrfmiddlewaretoken'] = response.context['csrf_token']
        response = self.client.get('/delete_daily/', self.formDeleteDaily)
        sizeQuery = len(DailyInput.objects.filter(id_user=idUser, date_from ='2018-10-13',id_concept=concepto_id))
        self.assertTrue(sizeQuery == 0)
