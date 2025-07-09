from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.test import TestCase
from flag.models import Flag,FlagDependency,AuditLog

class FlagListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        Flag.objects.create(name='flag1', is_active=True)
        Flag.objects.create(name='flag2', is_active=False)

    def test_flag_list_view_returns_all_flags(self):
        response = self.client.get(reverse('flag:flag_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        names = [flag['name'] for flag in response.data]
        self.assertIn('flag1', names)
        self.assertIn('flag2', names)

        is_active_values = [flag['is_active'] for flag in response.data]
        self.assertIn(True, is_active_values)
        self.assertIn(False, is_active_values)




class FlagDetailViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.flag = Flag.objects.create(name='flag1', is_active=True)

    def test_get_flag_detail_success(self):
        response = self.client.get(reverse('flag:flag_detail', kwargs={'pk': self.flag.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'flag1')
        self.assertEqual(response.data['is_active'], True)
        self.assertIn('id', response.data)
        self.assertIn('created_at', response.data)

    def test_get_flag_detail_not_found(self):
        response = self.client.get('/flags/999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)




class FlagToggleViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.flag1 = Flag.objects.create(name='flag1', is_active=True)
        self.flag2 = Flag.objects.create(name='flag2', is_active=True)
        self.flag3 = Flag.objects.create(name='flag3', is_active=True)
        FlagDependency.objects.create(flag=self.flag1, depends_on=self.flag2)
        FlagDependency.objects.create(flag=self.flag2, depends_on=self.flag3)

    def test_toggle_off_flag_and_auto_disable_dependents(self):
        response = self.client.post(reverse('flag:flag_toggle',args=[self.flag3.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.flag1.refresh_from_db()
        self.flag2.refresh_from_db()
        self.flag3.refresh_from_db()

        self.assertFalse(self.flag1.is_active)
        self.assertFalse(self.flag2.is_active)
        self.assertFalse(self.flag3.is_active)

        self.assertEqual(AuditLog.objects.filter(action="auto_disable").count(), 2)
        self.assertEqual(AuditLog.objects.filter(action="toggle_off").count(), 1)

    def test_toggle_on_flag_with_inactive_dependencies_should_fail(self):
        self.flag2.is_active = False
        self.flag2.save()

        self.flag1.is_active = False
        self.flag1.save()

        response = self.client.post(reverse('flag:flag_toggle',args=[self.flag1.pk]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inactive dependencies", response.data)
        self.assertIn("flag2", response.data["inactive dependencies"])

    def test_toggle_on_flag_successfully(self):
        self.flag1.is_active = False
        self.flag1.save()

        response = self.client.post(reverse('flag:flag_toggle',args=[self.flag1.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.flag1.refresh_from_db()
        self.assertTrue(self.flag1.is_active)

        log = AuditLog.objects.filter(flag=self.flag1, action="toggle_on").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.reason, "manual active")
        self.assertEqual(log.actor, "API")



class AddFlagViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_add_flag_success(self):
        data = {
            "name": "flag1",
            "is_active": True
        }
        response = self.client.post(reverse('flag:add_flag'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        flag = Flag.objects.get(name="flag1")
        self.assertTrue(flag.is_active)


        log = AuditLog.objects.filter(flag=flag, action='create').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.actor, 'API')
        self.assertIn("Flag flag1 was created", log.reason)

    def test_add_flag_missing_name_should_fail(self):
        data = {
            "is_active": True
        }
        response = self.client.post(reverse('flag:add_flag'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


        self.assertIn("errors", response.data)
        error_fields = [e["field"] for e in response.data["errors"]]
        self.assertIn("name", error_fields)
        self.assertTrue(any("required" in e["message"].lower() for e in response.data["errors"]))



class AddDependencyViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.flagA = Flag.objects.create(name='flagA')
        self.flagB = Flag.objects.create(name='flagB')
        self.flagC = Flag.objects.create(name='flagC')

    def test_add_dependency_success(self):
        data = {
            "flag": "flagA",
            "depends_on": "flagB"
        }
        response = self.client.post(reverse('flag:add_dependency'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(FlagDependency.objects.filter(flag=self.flagA, depends_on=self.flagB).exists())

    def test_add_duplicate_dependency_should_fail(self):
        FlagDependency.objects.create(flag=self.flagA, depends_on=self.flagB)
        data = {
            "flag": "flagA",
            "depends_on": "flagB"
        }
        response = self.client.post(reverse('flag:add_dependency'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        self.assertIn("non_field_errors", response.data["errors"])

    def test_add_self_dependency_should_fail(self):
        data = {
            "flag": "flagA",
            "depends_on": "flagA"
        }
        response = self.client.post(reverse('flag:add_dependency'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        self.assertIn("non_field_errors", response.data["errors"])

    def test_add_circular_dependency_should_fail(self):
        FlagDependency.objects.create(flag=self.flagA, depends_on=self.flagB)
        FlagDependency.objects.create(flag=self.flagB, depends_on=self.flagC)
        data = {
            "flag": "flagC",
            "depends_on": "flagA"
        }
        response = self.client.post(reverse('flag:add_dependency'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        self.assertIn("dependencies", response.data["errors"])



class AuditLogListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.flag1 = Flag.objects.create(name='flag1', is_active=True)
        self.flag2 = Flag.objects.create(name='flag2', is_active=False)

        AuditLog.objects.create(flag=self.flag1, action='create', reason='Created flag1', actor='API')
        AuditLog.objects.create(flag=self.flag2, action='toggle_off', reason='Disabled flag2', actor='API')

    def test_get_audit_log_list_success(self):
        response = self.client.get(reverse('flag:logs'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        actions = [log['action'] for log in response.data]
        self.assertIn('create', actions)
        self.assertIn('toggle_off', actions)

        flags = [log['flag'] for log in response.data]
        self.assertIn('flag1', flags)
        self.assertIn('flag2', flags)

        for log in response.data:
            self.assertIn('reason', log)
            self.assertIn('actor', log)
            self.assertIn('timestamp', log)
