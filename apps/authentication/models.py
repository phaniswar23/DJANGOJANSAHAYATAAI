from django.db import models
from django.utils import timezone

class User(models.Model):
    ROLE_CHOICES = [
        ('CITIZEN', 'Citizen'),
        ('EMPLOYEE', 'Employee'),
        ('SUPER_ADMIN', 'Super Admin'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Disabled', 'Disabled'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=50, blank=True, default='')
    passwordHash = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='CITIZEN', db_index=True)
    employeeId = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    mustResetPassword = models.BooleanField(default=False)
    department = models.JSONField(blank=True, null=True, default=dict)
    extraData = models.JSONField(blank=True, default=dict)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-createdAt']

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.role}"

    def to_dict(self):
        res = {
            '_id': str(self.id),
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'passwordHash': self.passwordHash,
            'role': self.role,
            'employeeId': self.employeeId,
            'designation': self.designation,
            'status': self.status,
            'mustResetPassword': self.mustResetPassword,
            'department': self.department or {},
            'createdAt': self.createdAt.isoformat() if self.createdAt else None,
            'updatedAt': self.updatedAt.isoformat() if self.updatedAt else None,
        }
        if self.extraData and isinstance(self.extraData, dict):
            for k, v in self.extraData.items():
                if k not in res:
                    res[k] = v
        return res


class EmailChangeRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    employeeId = models.CharField(max_length=100, blank=True, default='')
    name = models.CharField(max_length=255, blank=True, default='')
    departmentName = models.CharField(max_length=255, blank=True, default='')
    currentEmail = models.CharField(max_length=255)
    requestedEmail = models.CharField(max_length=255)
    reason = models.TextField(blank=True, default='')
    contactPhone = models.CharField(max_length=50, blank=True, default='')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    adminRemarks = models.TextField(blank=True, default='')
    createdAt = models.DateTimeField(default=timezone.now)
    resolvedAt = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'email_change_requests'
        ordering = ['-createdAt']

    def to_dict(self):
        return {
            '_id': str(self.id),
            'id': str(self.id),
            'employeeId': self.employeeId,
            'name': self.name,
            'departmentName': self.departmentName,
            'currentEmail': self.currentEmail,
            'requestedEmail': self.requestedEmail,
            'reason': self.reason,
            'contactPhone': self.contactPhone,
            'status': self.status,
            'adminRemarks': self.adminRemarks,
            'createdAt': self.createdAt.isoformat() if self.createdAt else None,
            'resolvedAt': self.resolvedAt.isoformat() if self.resolvedAt else None,
        }
