from django.db import models
from django.conf import settings
# models.py
class PhoneNumber(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]

    number = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return self.number

    @property
    def is_authenticated(self):
        return True  # Mimics authenticated user behavior


    @property
    def is_authenticated(self):
        return True  # Mimics authenticated user behavior


class CommunityMember(models.Model):
    COMMUNITY_CHOICES = [
        (1, 'shared dhikr'),
        (2, 'Noticeboard'),
        (3, 'Question/Answer'),
        (4, 'Donate'),
        
    ]

    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    name = models.CharField(max_length=255)
    phone_number = models.ForeignKey(PhoneNumber, on_delete=models.CASCADE, related_name="community_members")
    community = models.IntegerField(choices=COMMUNITY_CHOICES)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True) # Stores base64 image data as text
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) in {self.get_community_display()}"


class Token(models.Model):
    phone_number = models.OneToOneField(PhoneNumber, on_delete=models.CASCADE, related_name="token")
    jwt_token = models.TextField()  # Stores JWT as text to handle longer tokens
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.phone_number}"



class Khitmah(models.Model):
    khitmah_number = models.PositiveIntegerField()
    enddate = models.DateField()
    STATUS_CHOICES = (
        ('none', 'None'),
        ('inprocess', 'In Process'),
        ('completed', 'Completed'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='none')
    created_by = models.ForeignKey(PhoneNumber, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Khitmah {self.khitmah_number} by {self.created_by.number} ending on {self.enddate}"



class Juz(models.Model):
    khitmah = models.ForeignKey(Khitmah, related_name='juz_list', on_delete=models.CASCADE)
    juz_number = models.PositiveIntegerField()
    STATUS_CHOICES = (
        ('incomplete', 'Incomplete'),
        ('inprocess', 'In Process'),
        ('completed', 'Completed'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='incomplete')
    assigned_to = models.ForeignKey(PhoneNumber, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Juz {self.juz_number} of Khitmah {self.khitmah.khitmah_number}"



class NoticeboardPost(models.Model):
    text = models.TextField(blank=True)
    post_image = models.ImageField(upload_to='noticeboard_posts/', blank=True, null=True)
    created_by = models.ForeignKey(PhoneNumber, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post by {self.created_by.number} on {self.created_at}"
    
    

class Question(models.Model):
    STATUS_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    question_title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='public')
    created_by = models.ForeignKey(PhoneNumber, on_delete=models.CASCADE)  # Reference PhoneNumber directly
    created_at = models.DateTimeField(auto_now_add=True)
    community = models.PositiveIntegerField(default=3)  # Community ID for Question/Answer

    def __str__(self):
        return f"Question by {self.created_by.number} - {self.question_title}"
    
    
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    created_by = models.ForeignKey(PhoneNumber, on_delete=models.CASCADE)  # Admin who created the answer
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer by {self.created_by.number} to Question {self.question.id}"