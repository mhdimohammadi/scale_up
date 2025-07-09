from django.db import models



class Flag(models.Model):
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FlagDependency(models.Model):
    flag = models.ForeignKey(Flag,related_name='dependencies',on_delete=models.CASCADE)
    depends_on = models.ForeignKey(Flag,related_name='dependents',on_delete=models.CASCADE)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ['flag', 'depends_on'], name='unique_flag_dependencies')
        ]

    def __str__(self):
        return f"{self.flag.name} ---> {self.depends_on.name}"



class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('toggle_on', 'Toggle On'),
        ('toggle_off', 'Toggle Off'),
        ('auto_disable', 'Auto Disable'),
    ]
    flag = models.ForeignKey(Flag, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True,null=True)
    actor = models.CharField(max_length=100, blank=True,null=True)

    def __str__(self):
        return f"{self.action} for {self.flag.name}"
