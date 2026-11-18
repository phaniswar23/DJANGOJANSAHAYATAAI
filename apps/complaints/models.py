from django.db import models
from django.utils import timezone

class Complaint(models.Model):
    URGENCY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Emergency', 'Emergency'),
    ]

    STATUS_CHOICES = [
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Disputed', 'Disputed'),
        ('Rejected', 'Rejected'),
        ('Escalated', 'Escalated'),
    ]

    complaintId = models.CharField(max_length=100, unique=True, db_index=True)
    citizenId = models.CharField(max_length=100, db_index=True)
    citizenName = models.CharField(max_length=255, blank=True, default='')
    citizenEmail = models.CharField(max_length=255, blank=True, default='', db_index=True)
    citizenPhone = models.CharField(max_length=50, blank=True, default='')

    department = models.JSONField(default=dict)  # {'id': '...', 'name': '...', 'code': '...'}
    category = models.CharField(max_length=255, default='General Grievance', db_index=True)
    subCategory = models.CharField(max_length=255, blank=True, default='')
    title = models.CharField(max_length=500, blank=True, default='')
    description = models.TextField()
    originalText = models.TextField(blank=True, default='')

    urgency = models.CharField(max_length=50, choices=URGENCY_CHOICES, default='Medium')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Submitted', db_index=True)
    priorityScore = models.IntegerField(default=50)

    location = models.CharField(max_length=500, blank=True, default='')
    landmark = models.CharField(max_length=255, blank=True, default='')
    pincode = models.CharField(max_length=20, blank=True, default='')
    coordinates = models.JSONField(blank=True, null=True, default=dict)  # {'lat': ..., 'lng': ...}

    railwayDetails = models.JSONField(blank=True, null=True, default=dict)  # {'pnr': ..., 'trainNo': ..., 'coach': ..., 'berth': ...}
    documents = models.JSONField(blank=True, default=list)  # [{'url': ..., 'type': ...}]
    timeline = models.JSONField(blank=True, default=list)   # [{'status': ..., 'message': ..., 'timestamp': ..., 'by': ...}]

    resolutionProof = models.JSONField(blank=True, null=True, default=dict) # {'photo': ..., 'officerNotes': ..., 'resolvedAt': ...}
    feedback = models.JSONField(blank=True, null=True, default=dict)        # {'rating': 5, 'comment': ..., 'submittedAt': ...}

    isAudio = models.BooleanField(default=False)
    audioPath = models.CharField(max_length=500, blank=True, null=True)
    assignedTo = models.JSONField(blank=True, null=True, default=dict)
    extraData = models.JSONField(blank=True, default=dict)

    createdAt = models.DateTimeField(default=timezone.now, db_index=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'complaints'
        ordering = ['-createdAt']

    def __str__(self):
        return f"{self.complaintId} - {self.category} ({self.status})"

    def to_dict(self):
        res = {
            '_id': str(self.id),
            'id': str(self.id),
            'complaintId': self.complaintId,
            'citizenId': self.citizenId,
            'citizenName': self.citizenName,
            'citizenEmail': self.citizenEmail,
            'citizenPhone': self.citizenPhone,
            'department': self.department or {},
            'category': self.category,
            'subCategory': self.subCategory,
            'title': self.title,
            'description': self.description,
            'originalText': self.originalText,
            'urgency': self.urgency,
            'status': self.status,
            'priorityScore': self.priorityScore,
            'location': self.location,
            'landmark': self.landmark,
            'pincode': self.pincode,
            'coordinates': self.coordinates or {},
            'railwayDetails': self.railwayDetails or {},
            'documents': self.documents or [],
            'timeline': self.timeline or [],
            'resolutionProof': self.resolutionProof or {},
            'feedback': self.feedback or {},
            'isAudio': self.isAudio,
            'audioPath': self.audioPath,
            'assignedTo': self.assignedTo or {},
            'createdAt': self.createdAt.isoformat() if self.createdAt else None,
            'updatedAt': self.updatedAt.isoformat() if self.updatedAt else None,
        }
        if self.extraData and isinstance(self.extraData, dict):
            for k, v in self.extraData.items():
                if k not in res:
                    res[k] = v
        return res


class AuditLog(models.Model):
    action = models.CharField(max_length=255, db_index=True)
    performedBy = models.JSONField(default=dict)
    targetType = models.CharField(max_length=100, default='System')
    targetId = models.CharField(max_length=255, blank=True, default='')
    details = models.TextField(blank=True, default='')
    ipAddress = models.CharField(max_length=100, default='127.0.0.1')
    metadata = models.JSONField(blank=True, default=dict)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-createdAt']

    def to_dict(self):
        return {
            '_id': str(self.id),
            'id': str(self.id),
            'action': self.action,
            'performedBy': self.performedBy or {},
            'targetType': self.targetType,
            'targetId': self.targetId,
            'details': self.details,
            'ipAddress': self.ipAddress,
            'metadata': self.metadata or {},
            'createdAt': self.createdAt.isoformat() if self.createdAt else None,
            'updatedAt': self.updatedAt.isoformat() if self.updatedAt else None,
        }
