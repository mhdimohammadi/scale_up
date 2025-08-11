from .models import AuditLog




def has_cycle(current_name,name):
    visited = set()
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


def has_cycle1(current_flag,flag):
    visited = set()
    if current_flag == flag:
        return True
    if current_flag in visited:
        return False
    visited.add(current_flag)
    for dep in current_flag.dependencies.all():
        if has_cycle(dep.depends_on):
            return True
    return False



def auto_disable_dependents_cascade(flag):
    for dep in flag.dependents.all():
        if dep.flag.is_active:
            dep.flag.is_active = False
            dep.flag.save()
            AuditLog.objects.create(
                flag=dep.flag,
                action="auto_disable",
                reason=f"Dependency {flag.name} was disabled",
                actor="system")
            auto_disable_dependents_cascade(dep.flag)