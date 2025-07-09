from django.test import TestCase
from django.db import IntegrityError
from flag.models import Flag, FlagDependency

class FlagDependencyModelTest(TestCase):
    def setUp(self):
        self.flagA = Flag.objects.create(name='flagA')
        self.flagB = Flag.objects.create(name='flagB')

    def test_unique_flag_dependency_constraint(self):
        FlagDependency.objects.create(flag=self.flagA, depends_on=self.flagB)

        with self.assertRaises(IntegrityError):
            FlagDependency.objects.create(flag=self.flagA, depends_on=self.flagB)
