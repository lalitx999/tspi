from django.db import models

class Patient(models.Model):
    """คนไข้จาก MariaDB table `user`"""
    
    # Identity
    legacy_id = models.CharField(max_length=20, unique=True, db_index=True)
    hn = models.CharField(max_length=20, null=True, blank=True, db_index=True)  # ❌ เอา unique ออก
    
    # Personal info
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    nickname = models.CharField(max_length=50, blank=True, null=True)
    
    # Contact
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, null=True)
    line_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    # Demographics
    GENDER_CHOICES = [('M', 'ชาย'), ('F', 'หญิง'), ('O', 'อื่นๆ')]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Address
    address = models.TextField(blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    subdistrict = models.CharField(max_length=100, blank=True, null=True)
    postcode = models.CharField(max_length=10, blank=True, null=True)
    
    # Clinical status
    STATUS_CHOICES = [
        ('pending', 'รอดำเนินการ'),
        ('medicine', 'รับยา'),
        ('urgent', 'ด่วน'),
        ('wait_doctor', 'รอหมอ'),
        ('died', 'เสียชีวิต'),
        ('delete', 'ลบ'),
    ]
    status = models.CharField(max_length=50, default='pending', db_index=True)
    
    # Intake
    chief_complaint = models.TextField(blank=True, null=True)
    present_illness = models.TextField(blank=True, null=True)
    past_history = models.TextField(blank=True, null=True)
    drug_allergy = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    
    # Extra
    extra_data = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['phone']),
            models.Index(fields=['status']),
        ]
        verbose_name = "คนไข้"
        verbose_name_plural = "คนไข้ทั้งหมด"
    
    def __str__(self):
        return f"{self.legacy_id} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def age(self):
        from datetime import date
        if not self.birth_date:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
