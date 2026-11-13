from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.patients.models import Patient, ECGRecord

User = get_user_model()

class DashboardTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(username="dr_cardiologist", password="Password123!")
        self.patient = Patient.objects.create(
            doctor=self.doctor,
            first_name="مریم",
            last_name="سلطانی",
            age=38,
            gender="F",
            national_id="0055544433"
        )

    def test_dashboard_view_metrics_and_context(self):
        """تست صحت مقادیر مستقل Context در داشبورد"""
        ECGRecord.objects.create(
            patient=self.patient,
            signal_status=ECGRecord.SignalStatus.NORMAL,
            bpm=72
        )
        ECGRecord.objects.create(
            patient=self.patient,
            signal_status=ECGRecord.SignalStatus.ARRHYTHMIA,
            bpm=110
        )
        ECGRecord.objects.create(
            patient=self.patient,
            signal_status=ECGRecord.SignalStatus.PENDING
        )

        self.client.login(username="dr_cardiologist", password="Password123!")
        response = self.client.get(reverse('dashboard:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/index.html')

        # بررسی کلیدهای سطح اول context بر اساس DashboardView واقعی
        self.assertEqual(response.context['total_patients'], 1)
        self.assertEqual(response.context['total_ecg'], 3)
        self.assertEqual(response.context['normal_count'], 1)
        self.assertEqual(response.context['arrhythmia_count'], 1)
        self.assertEqual(response.context['pending_count'], 1)
        self.assertEqual(response.context['noise_count'], 0)
        self.assertIn('recent_records', response.context)

    def test_dashboard_login_required(self):
        """تست عدم دسترسی به داشبورد بدون لاگین"""
        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertNotEqual(response.status_code, 200)
