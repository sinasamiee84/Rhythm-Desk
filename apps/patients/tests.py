from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from apps.patients.models import Patient, ECGRecord

User = get_user_model()

class PatientsTests(TestCase):
    def setUp(self):
        self.doctor1 = User.objects.create_user(username="dr_shirazi", password="Password123!")
        self.doctor2 = User.objects.create_user(username="dr_karimi", password="Password123!")

        self.patient1 = Patient.objects.create(
            doctor=self.doctor1,
            first_name="علی",
            last_name="رضایی",
            age=45,
            gender="M",
            national_id="0012345678",
            phone_number="09111111111"
        )

    def test_patient_str_and_constraints(self):
        """تست متد __str__ و یکتایی کد ملی برای هر پزشک"""
        self.assertEqual(str(self.patient1), "علی رضایی")

        # تست خطای تکرار کد ملی برای همان پزشک در بلوک atomic
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Patient.objects.create(
                    doctor=self.doctor1,
                    first_name="محمد",
                    last_name="تقوی",
                    age=50,
                    gender="M",
                    national_id="0012345678"
                )

        # ثبت همان کد ملی برای پزشک دیگر باید کاملاً مجاز باشد
        patient_other_doc = Patient.objects.create(
            doctor=self.doctor2,
            first_name="علی",
            last_name="رضایی",
            age=45,
            gender="M",
            national_id="0012345678"
        )
        self.assertIsNotNone(patient_other_doc.pk)

    def test_patient_list_view_permission(self):
        """تست تفکیک بیماران هر پزشک در لیست"""
        self.client.login(username="dr_shirazi", password="Password123!")
        response = self.client.get(reverse('patients:list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.patient1, response.context['patients'])

        patient2 = Patient.objects.create(
            doctor=self.doctor2,
            first_name="سارا",
            last_name="احمدی",
            age=30,
            gender="F",
            national_id="0098765432"
        )
        self.assertNotIn(patient2, response.context['patients'])

    def test_patient_detail_security_mixin(self):
        """تست امنیت PatientOwnerMixin (جلوگیری از دسترسی پزشک دیگر به پرونده)"""
        self.client.login(username="dr_karimi", password="Password123!")
        response = self.client.get(reverse('patients:detail', kwargs={'pk': self.patient1.pk}))
        self.assertEqual(response.status_code, 403)
