from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import uuid
from apps.common.models import TimeStampMixin

# Create your models here.

class CustomUserManager(BaseUserManager):
    '''Custom user manager that provides methods for creating regular users and superusers with email as the unique identifier.'''

    def create_user(self,email,password=None,**extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email,**extra_fields)
        user.set_password(password)
        if not extra_fields.get('role'):
            from apps.accounts.models import Role
            try:
                default_role = Role.objects.get(name=Role.RoleChoices.CUSTOMER)
                user.role = default_role

            except Role.DoesNotExist:
                pass
          
        user.save(using=self._db)
        return user
    
    def create_superuser(self,email,password=None,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        from apps.accounts.models import Role
        try:
            admin_role = Role.objects.get(name=Role.RoleChoices.ADMIN)
            extra_fields.setdefault('role', admin_role)
        except Role.DoesNotExist:
            pass

        return self.create_user(email,password,**extra_fields)
    
    

class Role(TimeStampMixin):
    '''Model representing user roles in the system, such as Admin, Customer, and Service Professional.'''
    class RoleChoices(models.TextChoices):
        ADMIN = 'admin','Admin'
        CUSTOMER= 'customer','Customer',
        SERVICE_PROFESSIONAL = 'service_professional','Service Professional'
    uuid = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name = models.CharField(max_length=50,choices=RoleChoices.choices,unique=True)
    description = models.TextField(blank=True,null=True)


class User(AbstractUser,TimeStampMixin):

    '''Custom user model that uses email as the unique identifier and includes additional fields such as phone number, role, and Google ID for authentication.'''
    
    uuid = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15,blank=True,null=True,unique=True)
    role=models.ForeignKey(Role,on_delete=models.SET_NULL,null=True,related_name='users')
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True)

    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def save(self,*args,**kwargs):
        if  self.email:
            self.email = self.email.lower()
        
        if self.role and self.role.name == Role.RoleChoices.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        else:
            self.is_staff = False
            self.is_superuser = False

        super().save(*args,**kwargs)

    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
