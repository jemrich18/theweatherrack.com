from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from .models import HuntingArea
from .utils import score_day


class HuntingAreaModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.area = HuntingArea.objects.create(
            user=self.user,
            name='Test Field',
            latitude=38.5,
            longitude=-97.5
        )

    def test_area_created(self):
        self.assertEqual(self.area.name, 'Test Field')

    def test_area_coordinates(self):
        self.assertEqual(self.area.latitude, 38.5)
        self.assertEqual(self.area.longitude, -97.5)

    def test_area_str(self):
        self.assertIn('Test Field', str(self.area))
        self.assertIn('testuser', str(self.area))


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_page_loads(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)

    def test_register_valid_user(self):
        response = self.client.post('/register/', {
            'username': 'newuser',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_invalid_user(self):
        response = self.client.post('/register/', {
            'username': 'newuser',
            'password1': 'pass',
            'password2': 'different'
        })
        self.assertEqual(response.status_code, 200)


class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_dashboard_requires_login(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_loads_when_logged_in(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_shows_user_areas(self):
        self.client.login(username='testuser', password='testpass123')
        HuntingArea.objects.create(
            user=self.user,
            name='My Field',
            latitude=38.5,
            longitude=-97.5
        )
        response = self.client.get('/dashboard/')
        self.assertContains(response, 'My Field')


class AddAreaViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_add_area_page_loads(self):
        response = self.client.get('/add-area/')
        self.assertEqual(response.status_code, 200)

    @patch('hunt.views.geocode_location')
    def test_add_area_valid_location(self, mock_geocode):
        mock_geocode.return_value = {
            'latitude': 38.5,
            'longitude': -97.5,
            'display_name': 'Haven, Kansas'
        }
        response = self.client.post('/add-area/', {
            'name': 'New Field',
            'location_search': 'Haven, KS'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(HuntingArea.objects.filter(name='New Field').exists())

    @patch('hunt.views.geocode_location')
    def test_add_area_invalid_location(self, mock_geocode):
        mock_geocode.return_value = None
        response = self.client.post('/add-area/', {
            'name': 'Bad Field',
            'location_search': 'nowhere123456'
        })
        self.assertEqual(response.status_code, 200)


class DeleteAreaViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.area = HuntingArea.objects.create(
            user=self.user,
            name='Delete Me',
            latitude=38.5,
            longitude=-97.5
        )

    def test_delete_area(self):
        response = self.client.post(f'/delete-area/{self.area.pk}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(HuntingArea.objects.filter(pk=self.area.pk).exists())


class ForecastViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.area = HuntingArea.objects.create(
            user=self.user,
            name='Forecast Field',
            latitude=38.5,
            longitude=-97.5
        )

    @patch('hunt.views.get_scored_forecast')
    def test_forecast_loads(self, mock_forecast):
        mock_forecast.return_value = [
            {'date': '2026-05-11', 'score': 85, 'wind': 5}
        ]
        response = self.client.get(f'/forecast/{self.area.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_favorable_wind_direction_improves_score(self):
        day_data = {
            'temp_max': 55,
            'temp_min': 40,
            'wind_max': 10,
            'precip_prob': 5,
        }
        favorable = score_day(day_data, 0, [1010] * 24, 60, wind_direction=330)
        unfavorable = score_day(day_data, 0, [1010] * 24, 60, wind_direction=180)
        self.assertGreater(favorable['score'], unfavorable['score'])