from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from flag.serializers import FlagSerializer, FlagDependencySerializer, AuditLogSerializer
from .models import Flag, AuditLog
from .services import auto_disable_dependents_cascade


class FlagListView(APIView):
    def get(self, request):
        instance = Flag.objects.all()
        serializer = FlagSerializer(instance, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FlagDetailView(APIView):
    def get(self, request, pk):
        instance = get_object_or_404(Flag, pk=pk)
        serializer = FlagSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FlagToggleView(APIView):

    def post(self, request, pk):
        instance = get_object_or_404(Flag, pk=pk)
        if instance.is_active:
            auto_disable_dependents_cascade(instance)
            instance.is_active = False
            instance.save()
            AuditLog.objects.create(flag=instance, action='toggle_off', reason='manual inactive', actor='API')
        else:
            inactive_deps = [dep.depends_on.name for dep in instance.dependencies.all() if
                             dep.depends_on.is_active == False]
            if inactive_deps:
                return Response({"error": "inactive dependencies",
                                 "inactive dependencies": inactive_deps}, status=status.HTTP_400_BAD_REQUEST)
            instance.is_active = True
            instance.save()
            AuditLog.objects.create(flag=instance, action='toggle_on', reason='manual active', actor='API')
        return Response({"response": f'{instance.name} is now {"active" if instance.is_active else "inactive"}'},
                        status=status.HTTP_200_OK)


class AddFlagView(APIView):
    def post(self, request):
        serializer = FlagSerializer(data=request.data)
        if serializer.is_valid():
            flag = serializer.save()
            AuditLog.objects.create(flag=flag, action='create', reason=f"Flag {flag.name} was created", actor='API')
            return Response({"flag added"}, status=status.HTTP_201_CREATED)
        errors = []
        for field, messages in serializer.errors.items():
            for message in messages:
                errors.append({
                    "field": field,
                    "message": str(message)
                })
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)


class AddDependencyView(APIView):
    def post(self, request):
        serializer = FlagDependencySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"dependency added"}, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class AuditLogListView(APIView):
    def get(self, request):
        instance = AuditLog.objects.all()
        serializer = AuditLogSerializer(instance, many=True)
        return Response(serializer.data)
