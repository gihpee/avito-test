from django.db import models

# Create your models here.

from django.db import models
import uuid


class Employee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee'


class Organization(models.Model):
    ORGANIZATION_TYPE = [
        ('IE', 'IE'),
        ('LLC', 'LLC'),
        ('JSC', 'JSC'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(choices=ORGANIZATION_TYPE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization'


class OrganizationResponsible(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    organization_id = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user_id = models.ForeignKey(Employee, on_delete=models.CASCADE)

    class Meta:
        db_table = 'organization_responsible'


class Tender(models.Model):
    STATUS_CHOICES = [
        ('Created', 'Created'),
        ('Published', 'Published'),
        ('Closed', 'Closed')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField()
    service_type = models.CharField(max_length=100)
    status = models.CharField(choices=STATUS_CHOICES, default='Created')
    version = models.IntegerField(default=1)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    creator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class TenderVersion(models.Model):
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='versions')
    name = models.CharField(max_length=255)
    description = models.TextField()
    service_type = models.CharField(max_length=100)
    version = models.IntegerField()


class Bid(models.Model):
    STATUS_CHOICES = [
        ('Crated', 'Created'),
        ('Published', 'Published'),
        ('Cancelled', 'Cancelled')
    ]

    AUTHOR_TYPE_CHOICES = [
        ('Organization', 'Organization'),
        ('User', 'User')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(choices=STATUS_CHOICES, default='Created')
    author_type = models.CharField(choices=AUTHOR_TYPE_CHOICES)
    version = models.IntegerField(default=1)
    approvements = models.IntegerField(default=0)
    approved = models.BooleanField(null=True, blank=True)
    creator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class BidVersion(models.Model):
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='versions')
    name = models.CharField(max_length=255)
    description = models.TextField()
    version = models.IntegerField()


class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='feedback')
    description = models.TextField()
    executor = models.ForeignKey(Employee, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

