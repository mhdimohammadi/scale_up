from rest_framework import serializers
from .models import Flag,FlagDependency,AuditLog

class FlagSerializer(serializers.ModelSerializer):
    dependencies_list = serializers.SerializerMethodField(read_only=True)
    dependents_list = serializers.SerializerMethodField(read_only=True)
    dependency_names = serializers.ListField(child=serializers.CharField(), required=False)
    id = serializers.IntegerField(required=False,read_only=True)
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = Flag
        fields = '__all__'


    def get_dependencies_list(self, obj):
        return [dep.depends_on.name for dep in obj.dependencies.all()]


    def get_dependents_list(self, obj):
        return [dep.flag.name for dep in obj.dependents.all()]



    def validate(self, data):
        name = data['name']
        dependency_names = data.get('dependency_names', [])

        visited = set()
        def has_cycle(current_name):
            if current_name == name:
                return True
            if current_name in visited:
                return False
            visited.add(current_name)
            current_flag = Flag.objects.filter(name=current_name).first()
            if not current_flag:
                return False
            for dep in current_flag.dependencies.all():
                if has_cycle(dep.depends_on.name):
                    return True
            return False

        for dep_name in dependency_names:
            if has_cycle(dep_name):
                raise serializers.ValidationError({
                    "dependencies": [f"Adding dependency to '{dep_name}' creates a circular dependency."]})

        return data

    def create(self, validated_data):
        deps = validated_data.pop("dependency_names", [])
        flag = Flag.objects.create(**validated_data)
        for dep_name in deps:
            dep_flag = Flag.objects.get(name=dep_name)
            FlagDependency.objects.create(flag=flag, depends_on=dep_flag)
        return flag



class FlagDependencySerializer(serializers.ModelSerializer):
    flag = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Flag.objects.all()
    )
    depends_on = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Flag.objects.all()
    )

    class Meta:
        model = FlagDependency
        fields = ['flag', 'depends_on']

    def validate(self, data):
        flag = data['flag']
        depends_on = data['depends_on']

        if flag == depends_on:
            raise serializers.ValidationError("A flag cannot depend on itself.")

        if FlagDependency.objects.filter(flag=flag, depends_on=depends_on).exists():
            raise serializers.ValidationError("This dependency already exists.")

        visited = set()
        def has_cycle(current_flag):
            if current_flag == flag:
                return True
            if current_flag in visited:
                return False
            visited.add(current_flag)
            for dep in current_flag.dependencies.all():
                if has_cycle(dep.depends_on):
                    return True
            return False

        if has_cycle(depends_on):
            raise serializers.ValidationError({
                    "dependencies": [f"Adding dependency to '{depends_on}' creates a circular dependency."]})

        return data




class AuditLogSerializer(serializers.ModelSerializer):
    flag = serializers.SlugRelatedField(slug_field='name', queryset=Flag.objects.all())
    class Meta:
        model = AuditLog
        fields = '__all__'