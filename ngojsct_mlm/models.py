from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.core.exceptions import ValidationError
import hashlib
import random
import string
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, applicant_name=None, password=None, **extra_fields):
        if not email and not extra_fields.get('phone_number') :
            raise ValueError('At least one of Email, Phone Number, or Member ID must be set.')

        email = self.normalize_email(email) if email else None
        user = self.model(email=email, applicant_name=applicant_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, applicant_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email=email, applicant_name=applicant_name, password=password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    applicant_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=True, blank=True)
    # is_active = models.BooleanField(default=True)
    # address = models.TextField()
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    # area = models.CharField(max_length=150,null=True, blank=True)
    memberID = models.CharField(max_length=50, unique=True, blank=True, null=True)
    user_type = models.CharField(max_length=50,  default='user1')
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(default=1)
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['applicant_name']

    def __str__(self):
        return self.email or self.phone_number or self.memberID

    class Meta:
        db_table = 'tbl_user'


class MemberModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_detail = models.ForeignKey("CustomUser",  on_delete=models.CASCADE)
    senior_ID = models.CharField(max_length=50)
    senior_Name = models.CharField(max_length=100)
    sponser_member = models.ForeignKey(
        "self",  # Self-referential ForeignKey
        # verbose_name=_("Sponsor Member"),
        on_delete=models.CASCADE,
        blank=True,  # Allows this field to be optional
        null=True    # Allows this field to accept NULL values
    )
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number=  models.CharField(max_length=10,unique=True)
    address = models.TextField(null=False, blank=False)
    applicant_name = models.CharField(max_length=100,null=False, blank=False)
    # mobile_no = models.CharField(max_length=10)
    # emailaddress = models.EmailField(blank=True, null=True)
    # aadhaar = models.CharField(max_length=12)
    # pan_no = models.CharField(max_length=10)
    user_type = models.CharField(max_length=50,  null=False,blank=False)
    
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=now)  # Default to current time
    updated_at = models.DateTimeField(auto_now=True)  # Automatically update on save
    status = models.IntegerField(default=1)
    rank    = models.CharField(max_length=50)
    registration_fee =models.DecimalField( max_digits=6, decimal_places=2)
    is_active = models.BooleanField(default=True)
    joining_date= models.DateField( auto_now=True)
    def __str__(self):
        return self.applicant_name

    class Meta:
        db_table = "tbl_member"


class StateModel(models.Model):
    id= models.BigAutoField(primary_key=True)
    name =models.CharField(max_length=100)
    # code = models.IntegerField()
    created_at = models.DateTimeField(default=now)  # Default to current time
    updated_at = models.DateTimeField(auto_now=True)  # Automatically update on save
    status = models.IntegerField(default=1)

    def __str__(self):
        return self.name
    class Meta:
        db_table="tbl_state"

class CityModel(models.Model):
    id= models.BigAutoField(primary_key=True)
    name=models.CharField(max_length=100)
    state= models.ForeignKey("StateModel", on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=now)  # Default to current time
    updated_at = models.DateTimeField(auto_now=True)  # Automatically update on save
    status = models.IntegerField(default=1)

    def __str__(self):
        return self.name
    class Meta:
        db_table="tbl_city"


class ExpanseModel(models.Model):
    # user_type = models.CharField(max_length=20)  # 'individual' or 'organization'
    member = models.ForeignKey("MemberModel", on_delete=models.CASCADE)
    total_amount = models.IntegerField(default=1551)

    leader_expense = models.IntegerField()
    tour = models.IntegerField()
    board_members = models.IntegerField()
    admin_expense = models.IntegerField()
    social_work = models.IntegerField()
    misc = models.IntegerField()
    product_cost = models.IntegerField()
    karykarta_fund = models.IntegerField()
    ngo_reserve_fund = models.IntegerField()
    created_at = models.DateTimeField(default=now)  # Default to current time
    updated_at = models.DateTimeField(auto_now=True)  # Automatically update on save
    status = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.member.applicant_name} - {self.amount} - "

    class Meta:
        db_table = "tbl_expense"



class LevelIncomeDistributionModel(models.Model):
    #referrer:A person who refers another
    referrer = models.ForeignKey(
        "MemberModel",  # Self-referential ForeignKey
        related_name='referrals',  # To access referrals from a member
        on_delete=models.CASCADE,
        blank=True,  # Allows this field to be optional
        null=True    # Allows this field to accept NULL values
    )
    referee= models.ForeignKey(
        "MemberModel",  # Self-referential ForeignKey
        related_name='referees',  # To access referees from a member
        on_delete=models.CASCADE,
        blank=True,  # Allows this field to be optional
        null=True    # Allows this field to accept NULL values
    )
    level = models.CharField(max_length=50)  # e.g., 'district', 'block', etc.
    income = models.IntegerField()
    created_at = models.DateTimeField(default=now)  # Default to current time
    updated_at = models.DateTimeField(auto_now=True)  # Automatically update on save
    status = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.referrer.applicant_name} - {self.level} - {self.income}"

    class Meta:
        db_table = "tbl_level_income"



class FundDistributionModel(models.Model):
    member = models.ForeignKey('MemberModel', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(default=1)
    
    # def __str__(self):
    #     return f"{self.referrer.name} - {self.level} - {self.income}"

    class Meta:
        db_table = "tbl_fund_distri"


class DonationsModel(models.Model):
    member = models.ForeignKey('MemberModel', on_delete=models.CASCADE)
    amount=models.DecimalField( max_digits=20, decimal_places=2)
    slip_for = models.CharField( max_length=50)
    created_at = models.DateTimeField(default=now)  # Default to current time
    updated_at = models.DateTimeField(auto_now=True)  # Automatically update on save
    status = models.IntegerField(default=1)
    
    class Meta:
        db_table="tbl_donation"


class WalletModel(models.Model):
    member = models.ForeignKey('MemberModel', on_delete=models.CASCADE)
    credited = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    debited = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(default=now)  # Default to current time
    updated_at = models.DateTimeField(auto_now=True)  # Automatically update on save
    status = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.member.applicant_name} - {self.balance}"

    class Meta:
        db_table = "tbl_wallet"


class PaymentRequestDetailsModel(models.Model):
    id = models.AutoField(primary_key=True)
    request_text                    =   models.TextField()
    success_status                  =   models.BooleanField()
    # payemnt_code                    =   models.CharField(max_length=50, null=False)
    payment_gatway_name             =   models.CharField(max_length=50, null=False)
    # message                         =   models.CharField(max_length=50, null=False)
    # merchantId                      =   models.CharField(max_length=50, null=False)
    # merchantTransactionId           =   models.CharField(max_length=50, null=False)
    # instrumentResponse_type         =   models.CharField(max_length=50, null=False)
    # instrumentResponse_redirect     =   models.TextField( null=False)
    method_type                     =   models.CharField(max_length=50, null=False)
    checksum                        =   models.TextField()
    amount                          =   models.DecimalField(max_digits=10, decimal_places=2)
    attempts                        =   models.IntegerField()
    member                          =   models.ForeignKey("MemberModel", on_delete=models.CASCADE ,null=True,blank=True)
    # ngo                          =   models.ForeignKey("NgoModel", on_delete=models.CASCADE ,null=True,blank=True)
    # campaign                          =   models.ForeignKey("CampaignModel", on_delete=models.CASCADE ,null=True,blank=True)
    pay_for                        =   models.CharField(max_length=50, null=False, )
    currency                        =   models.CharField(max_length=50, null=False, )
    name                            = models.CharField(max_length=255, blank=True, null=True)
    email                           = models.EmailField(blank=True, null=True)
    mobile                           = models.CharField(max_length=20, blank=True, null=True)
    is_indian                       = models.BooleanField(default=True)
    order_id                        =models.CharField( max_length=100)
    # make_donation_anonymous         = models.BooleanField(default=False)
    # receive_whatsapp_updates         = models.BooleanField(default=False)
    # tip_amount                          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status                          =models.CharField( max_length=100)
    class Meta:
        db_table = "tbl_payment_requets_det"


class PaymentResponseDetailsModel(models.Model):
    id = models.AutoField(primary_key=True)
    member                          =   models.ForeignKey("MemberModel", on_delete=models.CASCADE ,null=True,blank=True)
    request_text                    =   models.TextField()
    razorpay_payment_id             =   models.CharField( max_length=200)
    razorpay_order_id               =   models.CharField( max_length=200)
    razorpay_signature              =   models.CharField( max_length=200)
    created_at                      =   models.DateTimeField( auto_now=False, auto_now_add=False)
    status                         =   models.CharField( max_length=50)
    class Meta:
        db_table = "tbl_payment_response_det"