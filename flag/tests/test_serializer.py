from django.test import TestCase
from flag.models import Flag, FlagDependency
from flag.serializers import FlagSerializer, FlagDependencySerializer

class FlagSerializerTest(TestCase):
    def setUp(self):
        self.flag1 = Flag.objects.create(name='flag1')
        self.flag2 = Flag.objects.create(name='flag2')

    def test_create_flag_without_dependencies(self):
        data = {'name': 'flag3'}
        serializer = FlagSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        flag = serializer.save()
        self.assertEqual(flag.name, 'flag3')
        self.assertEqual(flag.dependencies.count(), 0)

    def test_create_flag_with_valid_dependencies(self):
        data = {
            'name': 'flag3',
            'dependency_names': ['flag1', 'flag2']
        }
        serializer = FlagSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        flag = serializer.save()
        self.assertEqual(flag.dependencies.count(), 2)

    def test_create_flag_with_self_dependency_should_fail(self):
        data = {
            'name': 'flag1',
            'dependency_names': ['flag1']
        }
        serializer = FlagSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('dependencies', serializer.errors)

    def test_create_flag_with_circular_dependency_should_fail(self):
        flag3 = Flag.objects.create(name='flag3')
        FlagDependency.objects.create(flag=self.flag1, depends_on=flag3)
        FlagDependency.objects.create(flag=self.flag2, depends_on=self.flag1)

        data = {
            'name': 'flag3',
            'dependency_names': ['flag2']
        }
        serializer = FlagSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('dependencies', serializer.errors)

    def test_dependencies_and_dependents_output(self):
        flag3 = Flag.objects.create(name='flag3')
        FlagDependency.objects.create(flag=flag3, depends_on=self.flag1)
        FlagDependency.objects.create(flag=flag3, depends_on=self.flag2)

        FlagDependency.objects.create(flag=self.flag1, depends_on=self.flag2)

        serializer = FlagSerializer(flag3)
        self.assertEqual(set(serializer.data['dependencies_list']), {'flag1', 'flag2'})
        self.assertEqual(serializer.data['dependents_list'], [])

        serializer1 = FlagSerializer(self.flag1)
        self.assertEqual(serializer1.data['dependents_list'], ['flag3'])
        self.assertEqual(serializer1.data['dependencies_list'], ['flag2'])



class FlagDependencySerializerTest(TestCase):
    def setUp(self):
        self.flag1 = Flag.objects.create(name='flag1')
        self.flag2 = Flag.objects.create(name='flag2')
        self.flag3 = Flag.objects.create(name='flag3')

    def test_create_valid_dependency(self):
        data = {
            'flag': 'flag1',
            'depends_on': 'flag2'
        }
        serializer = FlagDependencySerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        dep = serializer.save()
        self.assertEqual(dep.flag, self.flag1)
        self.assertEqual(dep.depends_on, self.flag2)

    def test_self_dependency_should_fail(self):
        data = {
            'flag': 'flag1',
            'depends_on': 'flag1'
        }
        serializer = FlagDependencySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn("A flag cannot depend on itself.", serializer.errors["non_field_errors"])

    def test_duplicate_dependency_should_fail(self):
        flag_a = Flag.objects.create(name='flag_a')
        flag_b = Flag.objects.create(name='flag_b')
        FlagDependency.objects.create(flag=flag_a, depends_on=flag_b)

        data = {
            'flag': 'flag_a',
            'depends_on': 'flag_b'
        }
        serializer = FlagDependencySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_circular_dependency_should_fail(self):
        FlagDependency.objects.create(flag=self.flag1, depends_on=self.flag2)
        FlagDependency.objects.create(flag=self.flag2, depends_on=self.flag3)


        data = {
            'flag': 'flag3',
            'depends_on': 'flag1'
        }
        serializer = FlagDependencySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("dependencies", serializer.errors)
        self.assertIn("circular dependency", serializer.errors["dependencies"][0])
