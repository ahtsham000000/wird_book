# serializers.py

from rest_framework import serializers
from .models import PhoneNumber, CommunityMember, Token , Khitmah , Juz ,NoticeboardPost ,Answer


class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ['id', 'number', 'is_verified', 'role']
        read_only_fields = ['role']


class JoinCommunitySerializer(serializers.ModelSerializer):
    phone_number = serializers.HiddenField(default=serializers.CurrentUserDefault())
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = CommunityMember
        fields = ['id', 'name', 'community', 'profile_image', 'phone_number', 'role', 'status']
        read_only_fields = ['status']  # Remove 'role' from read_only_fields if it was there

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=CommunityMember.objects.all(),
                fields=['phone_number', 'community'],
                message="You have already requested to join this community."
            )
        ]

    def create(self, validated_data):
        # If the role is 'admin', automatically set status to 'accepted'
        if validated_data.get('role') == 'admin':
            validated_data['status'] = 'accepted'
        else:
            # Optionally, set status to 'pending' for other roles
            validated_data['status'] = 'pending'

        # Create the CommunityMember instance
        community_member = CommunityMember.objects.create(**validated_data)

        # Update the role in PhoneNumber model
        phone_number = validated_data['phone_number']
        phone_number.role = validated_data['role']
        phone_number.save()

        return community_member





class CommunityMemberSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='phone_number.number', read_only=True)
    community = serializers.CharField(source='get_community_display')
    role = serializers.CharField(source='get_role_display')
    status = serializers.CharField(source='get_status_display')

    class Meta:
        model = CommunityMember
        fields = ['id', 'name', 'phone_number', 'community', 'profile_image', 'role', 'status']
        
class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ['jwt_token', 'created_at']




class JuzSerializer(serializers.ModelSerializer):
    assigned_to = serializers.CharField(source='assigned_to.number', read_only=True)

    class Meta:
        model = Juz
        fields = ['id', 'juz_number', 'status', 'assigned_to']
        read_only_fields = ['id', 'assigned_to']
        
        
class KhitmahSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    created_by = serializers.CharField(source='created_by.number', read_only=True)
    juz_list = JuzSerializer(many=True, read_only=True)

    class Meta:
        model = Khitmah
        fields = ['id', 'khitmah_number', 'enddate', 'status', 'created_by', 'created_at', 'juz_list']
        read_only_fields = ['id', 'status', 'created_by', 'created_at', 'juz_list']
        
        
class NoticeboardPostSerializer(serializers.ModelSerializer):
    post_image = serializers.ImageField(required=False, allow_null=True)
    created_by = serializers.CharField(source='created_by.number', read_only=True)

    class Meta:
        model = NoticeboardPost
        fields = ['id', 'text', 'post_image', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']

    def validate(self, data):
        if not data.get('text') and not data.get('post_image'):
            raise serializers.ValidationError("Either 'text' or 'post_image' must be provided.")
        return data

    def validate_post_image(self, value):
        # Check file type
        if not value.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            raise serializers.ValidationError("Only .jpg, .jpeg, .png files are allowed.")
        return value


from rest_framework import serializers
from .models import Question

class QuestionSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.number', read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'question_title', 'description', 'status', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']


class QuestionUpdateSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Question
        fields = ['question_id', 'question_title', 'description', 'status']  # Include question_id
        extra_kwargs = {
            'question_title': {'required': False},
            'description': {'required': False},
            'status': {'required': False},
        }
        
class AnswerSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.number', read_only=True)
    
    class Meta:
        model = Answer
        fields = ['id', 'answer_text', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']

class UserQuestionSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.number', read_only=True)
    answer = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'question_title', 'description', 'status', 'created_by', 'created_at', 'answer']
        read_only_fields = ['id', 'created_by', 'created_at', 'answer']

    def get_answer(self, obj):
        # Get the first answer for the question, if any
        answer = obj.answers.first()
        if answer:
            return AnswerSerializer(answer).data
        else:
            return None