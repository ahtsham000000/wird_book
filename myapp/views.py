# views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.conf import settings
import jwt
from .models import PhoneNumber, CommunityMember, Token ,Juz ,NoticeboardPost ,Question
from .serializers import PhoneNumberSerializer, JoinCommunitySerializer, CommunityMemberSerializer,NoticeboardPostSerializer,QuestionSerializer ,QuestionUpdateSerializer,AnswerSerializer ,UserQuestionSerializer
from .authentication import PhoneNumberJWTAuthentication
from django.db.models import Q, Count
from datetime import datetime,timedelta
from .models import Khitmah, PhoneNumber
from .serializers import KhitmahSerializer
from rest_framework.parsers import MultiPartParser, FormParser
import datetime
from django.db import transaction

class RegisterPhoneNumberAPI(APIView):
    def post(self, request, *args, **kwargs):
        number = request.data.get('number')
        if not number:
            return Response({"error": "Number is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            phone_number = PhoneNumber.objects.get(number=number)
            community_members = CommunityMember.objects.filter(phone_number=phone_number)
            if community_members.filter(status__in=['pending', 'rejected']).exists():
                status_member = community_members.filter(status__in=['pending', 'rejected']).first()
                if status_member.status == 'pending':
                    return Response(
                        {"message": "Your account is pending approval. Please wait until your request is processed."},
                        status=status.HTTP_403_FORBIDDEN
                    )
                elif status_member.status == 'rejected':
                    return Response(
                        {"message": "Your account request has been rejected. You cannot log in."},
                        status=status.HTTP_403_FORBIDDEN
                    )
        except PhoneNumber.DoesNotExist:
            pass  
        try:
            phone_number = PhoneNumber.objects.get(number=number)
            if phone_number.is_verified:
                try:
                    community_member = CommunityMember.objects.get(phone_number=phone_number)
                    role = community_member.get_role_display()
                except CommunityMember.DoesNotExist:
                    role = phone_number.get_role_display()
                return Response(
                    {
                        "message": "The OTP is sent to your number",
                        "number": phone_number.number,
                        "number_id": phone_number.id,
                        "role": role
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "message": "The OTP is sent to your number",
                        "number": phone_number.number,
                        "number_id": phone_number.id
                    },
                    status=status.HTTP_200_OK
                )
        except PhoneNumber.DoesNotExist:
            serializer = PhoneNumberSerializer(data=request.data)
            if serializer.is_valid():
                phone_number = serializer.save()
                return Response(
                    {
                        "message": "The OTP is sent to your number",
                        "number": phone_number.number,
                        "number_id": phone_number.id
                    },
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPAPI(APIView):
    def post(self, request, *args, **kwargs):
        number = request.data.get("number")
        otp = request.data.get("otp")

        try:
            phone_instance = PhoneNumber.objects.get(number=number)
        except PhoneNumber.DoesNotExist:
            return Response({"message": "Phone number not found."}, status=status.HTTP_404_NOT_FOUND)

        if phone_instance.is_verified:
            jwt_token = self.generate_jwt(phone_instance)
            community_data = self.get_community_data(phone_instance)
            return Response(
                {
                    "message": "The number is already verified",
                    "jwt": jwt_token,
                    **community_data
                },
                status=status.HTTP_200_OK
            )

        if otp == "0000":
            phone_instance.is_verified = True
            phone_instance.save()
            jwt_token = self.generate_jwt(phone_instance)
            community_data = self.get_community_data(phone_instance)
            return Response(
                {
                    "message": "The user is verified now",
                    "jwt": jwt_token,
                    **community_data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def generate_jwt(phone_instance):
        # Refresh the phone_instance to get the latest data from the database
        phone_instance.refresh_from_db()

        # Retrieve the community information from CommunityMember
        try:
            community_member = CommunityMember.objects.get(phone_number=phone_instance)
            community = community_member.community
        except CommunityMember.DoesNotExist:
            community = None  # Handle the case where the user is not associated with a community

        # Ensure you have imported datetime and timedelta
        from datetime import datetime, timedelta

        payload = {
            'number': phone_instance.number,
            'role': phone_instance.role,
            'community': community,
            'exp': datetime.utcnow() + timedelta(hours=175200)
        }

        jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        Token.objects.update_or_create(
            phone_number=phone_instance,
            defaults={'jwt_token': jwt_token}
        )
        return jwt_token

    @staticmethod
    def get_community_data(phone_instance):
        try:
            community_member = CommunityMember.objects.get(phone_number=phone_instance)
            profile_image_url = community_member.profile_image.url if community_member.profile_image else None
            return {
                "phone_number": phone_instance.number,
                "name": community_member.name,
                "community": dict(CommunityMember.COMMUNITY_CHOICES).get(community_member.community),
                "profile_image": profile_image_url,
                "role": community_member.get_role_display()
            }
        except CommunityMember.DoesNotExist:
            return {
                "phone_number": phone_instance.number,
                "name": "",
                "community": "",
                "profile_image": None,
                "role": phone_instance.get_role_display()
            }

            
            

class JoinCommunityAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # Adjust role check if necessary
        if request.user.role not in ['user', 'admin']:
            return Response({"message": "You do not have permission to join a community."}, status=status.HTTP_403_FORBIDDEN)

        serializer = JoinCommunitySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            with transaction.atomic():
                community_member = serializer.save()

            profile_image_url = community_member.profile_image.url if community_member.profile_image else None

            return Response(
                {
                    "message": "Your data and request has been sent",
                    "phone_number": request.user.number,
                    "name": community_member.name,
                    "community": community_member.get_community_display(),
                    "profile_image": profile_image_url,
                    "role": community_member.get_role_display(),
                    "status": community_member.get_status_display()
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class CommunityMemberPendingListAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'admin':
            return Response({"message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        admin_memberships = CommunityMember.objects.filter(phone_number=request.user, role='admin')

        if not admin_memberships.exists():
            return Response({"message": "Admin community not found"}, status=status.HTTP_403_FORBIDDEN)

        admin_communities = admin_memberships.values_list('community', flat=True)

        # Exclude the admin's own pending request
        pending_members = CommunityMember.objects.filter(
            status='pending',
            community__in=admin_communities
        ).exclude(phone_number=request.user)

        serializer = CommunityMemberSerializer(pending_members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)




    
    

class CommunityMemberStatusUpdateAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Verify the user is an admin
        if request.user.role != 'admin':
            return Response({"message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        number = request.data.get('number')
        status_update = request.data.get('status')

        if status_update not in ['accepted', 'rejected']:
            return Response({"message": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        # Get the admin's community memberships
        admin_memberships = CommunityMember.objects.filter(phone_number=request.user, role='admin')

        if not admin_memberships.exists():
            return Response({"message": "Admin community not found"}, status=status.HTTP_403_FORBIDDEN)

        admin_communities = admin_memberships.values_list('community', flat=True)

        try:
            phone_number = PhoneNumber.objects.get(number=number)
            if phone_number == request.user:
                return Response({"message": "You cannot update your own request."}, status=status.HTTP_400_BAD_REQUEST)

            community_member = CommunityMember.objects.get(phone_number=phone_number)

            if community_member.status != 'pending':
                return Response({"message": "Request has already been processed."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the community member's community matches the admin's communities
            if community_member.community not in admin_communities:
                return Response({"message": "You cannot process requests for other communities."}, status=status.HTTP_403_FORBIDDEN)

            # Update the status
            community_member.status = status_update
            community_member.save()

            if status_update == 'accepted':
                # Update the role in PhoneNumber model
                phone_number.role = community_member.role
                phone_number.save()

            return Response({"message": f"Request has been {status_update}"}, status=status.HTTP_200_OK)
        except PhoneNumber.DoesNotExist:
            return Response({"message": "Phone number not found"}, status=status.HTTP_404_NOT_FOUND)
        except CommunityMember.DoesNotExist:
            return Response({"message": "Community member not found"}, status=status.HTTP_404_NOT_FOUND)



class KhitmahAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # This is the PhoneNumber instance

        # Check if the user is admin
        if user.role != 'admin':
            return Response({"message": "Only admins can post khitmah."}, status=status.HTTP_403_FORBIDDEN)

        # Get the community from the JWT token payload
        payload = request.auth  # This is the decoded JWT payload
        community = payload.get('community')

        if community != 1:
            return Response({"message": "Only admins of community 'shared dhikr' can post khitmah."}, status=status.HTTP_403_FORBIDDEN)

        # Now, get 'numberofkhitmah' and 'enddate' from request data
        numberofkhitmah = request.data.get('numberofkhitmah')
        enddate = request.data.get('enddate')

        # Validate 'numberofkhitmah' is positive integer
        try:
            numberofkhitmah = int(numberofkhitmah)
            if numberofkhitmah <= 0:
                return Response({"message": "'numberofkhitmah' must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({"message": "'numberofkhitmah' must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate 'enddate' is a valid date in format 'DD-MM-YYYY'
        try:
            enddate = datetime.datetime.strptime(enddate, '%d-%m-%Y').date()
        except ValueError:
            return Response({"message": "'enddate' must be a date in the format 'DD-MM-YYYY' (e.g., '25-11-2024')."}, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing incomplete khitmah entries with future end dates
        today = datetime.date.today()
        existing_khitmah = Khitmah.objects.filter(
            created_by=user,
            status__in=['none', 'inprocess'],
            enddate__gte=today
        )

        if existing_khitmah.exists():
            return Response({"message": "You cannot post new khitmah until all previous khitmah are completed or the end date has passed."}, status=status.HTTP_400_BAD_REQUEST)

        khitmah_list = []

        with transaction.atomic():
            for i in range(1, numberofkhitmah + 1):
                khitmah = Khitmah.objects.create(
                    khitmah_number=i,
                    enddate=enddate,
                    created_by=user,
                    status='inprocess'  # Set initial status to 'inprocess'
                )

                # Create 30 juz entries for this khitmah
                juz_objects = [Juz(khitmah=khitmah, juz_number=j) for j in range(1, 31)]
                Juz.objects.bulk_create(juz_objects)

                khitmah_list.append(khitmah)

        # Serialize the khitmah entries
        serializer = KhitmahSerializer(khitmah_list, many=True)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
class KhitmahStatusAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = request.auth  
        community = payload.get('community')
        if community != 1:
            return Response({"message": "You do not have access to this resource."}, status=status.HTTP_403_FORBIDDEN)

        khitmah_list = Khitmah.objects.filter(
            status__in=['none', 'inprocess']
        ).order_by('khitmah_number')

        if not khitmah_list.exists():
            return Response({"message": "No active khitmah found."}, status=status.HTTP_404_NOT_FOUND)

        while khitmah_list.exists():
            current_khitmah = khitmah_list.first()
            juz_counts = current_khitmah.juz_list.aggregate(
                total_juz=Count('id'),
                juz_completed=Count('id', filter=Q(status='completed')),
                juz_inprocess=Count('id', filter=Q(status='inprocess')),
                juz_incomplete=Count('id', filter=Q(status='incomplete')),
            )

            total_count = juz_counts['total_juz'] or 0
            juz_completed = juz_counts['juz_completed'] or 0

            if juz_completed == total_count and total_count != 0:
                current_khitmah.status = 'completed'
                current_khitmah.save()
                khitmah_list = khitmah_list.exclude(id=current_khitmah.id)
                continue  
            else:
                data = {
                    "juz_inprocess": juz_counts['juz_inprocess'] or 0,
                    "total_count": total_count,  # Should be 30
                    "juz_completed": juz_completed,
                    "khitmah_number": current_khitmah.khitmah_number,
                    "start_date": current_khitmah.created_at.date(),
                    "end_date": current_khitmah.enddate
                }

                return Response(data, status=status.HTTP_200_OK)

        # If all khitmahs are completed
        return Response({"message": "No active khitmah found."}, status=status.HTTP_404_NOT_FOUND)




class KhitmahStatusUpdateAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # The authenticated user

        # Get data from request
        khitmah_number = request.data.get('khitmah_number')
        juz_number = request.data.get('juz_number')
        status_update = request.data.get('status')

        # Validate status
        if status_update not in ['inprocess', 'completed']:
            return Response({"message": "Invalid status. Allowed statuses are 'inprocess' and 'completed'."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate khitmah_number and juz_number
        if not khitmah_number or not juz_number:
            return Response({"message": "'khitmah_number' and 'juz_number' are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            khitmah_number = int(khitmah_number)
            juz_number = int(juz_number)
        except ValueError:
            return Response({"message": "'khitmah_number' and 'juz_number' must be integers."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the khitmah
        try:
            khitmah = Khitmah.objects.get(khitmah_number=khitmah_number, status__in=['none', 'inprocess'])
        except Khitmah.DoesNotExist:
            return Response({"message": "Khitmah not found or already completed."}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve the juz
        try:
            juz = Juz.objects.get(khitmah=khitmah, juz_number=juz_number)
        except Juz.DoesNotExist:
            return Response({"message": "Juz not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user has another juz in 'inprocess' status
        user_inprocess_juz = Juz.objects.filter(
            khitmah=khitmah,
            status='inprocess',
            assigned_to=user
        ).exclude(id=juz.id)

        if status_update == 'inprocess':
            # Allow the user to set a juz to 'inprocess' if they don't have another juz in 'inprocess' status
            if user_inprocess_juz.exists():
                return Response({"message": "You can only have one juz in process at a time."}, status=status.HTTP_400_BAD_REQUEST)

            if juz.status == 'incomplete':
                # Update the status to 'inprocess' and assign to the user
                juz.status = 'inprocess'
                juz.assigned_to = user
                juz.save()
                return Response({"message": f"Juz {juz_number} of Khitmah {khitmah_number} is now in process by you."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": f"Juz {juz_number} is already in process or completed."}, status=status.HTTP_400_BAD_REQUEST)

        elif status_update == 'completed':
            if juz.status == 'inprocess' and juz.assigned_to == user:
                # Update the status to 'completed'
                juz.status = 'completed'
                juz.save()

                # Check if all juz in the khitmah are completed
                incomplete_juz = khitmah.juz_list.filter(~Q(status='completed')).exists()
                if not incomplete_juz:
                    khitmah.status = 'completed'
                    khitmah.save()

                return Response({"message": f"Juz {juz_number} of Khitmah {khitmah_number} has been completed by you."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "You can only complete a juz that is in process and assigned to you."}, status=status.HTTP_400_BAD_REQUEST)




# views.py



class NoticeboardPostAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        user = request.user  # The authenticated PhoneNumber instance
        payload = request.auth  # JWT payload

        # Get the community from the JWT payload
        community = payload.get('community')

        # Check if the user belongs to community 2 ('Noticeboard')
        if community != 2:
            return Response(
                {"message": "You do not have access to this community."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = NoticeboardPostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NoticeboardPostListAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # The authenticated PhoneNumber instance

        # Check if the user belongs to community 2 ('Noticeboard')
        community_member = CommunityMember.objects.filter(
            phone_number=user, 
            community=2, 
            status='accepted'
        ).first()

        if not community_member:
            return Response(
                {"message": "You do not have access to this community."},
                status=403
            )

        # Retrieve all posts, ordered by creation date (most recent first)
        posts = NoticeboardPost.objects.order_by('-created_at')

        serializer = NoticeboardPostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data, status=200)


class QuestionPostAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # This should be a PhoneNumber instance

        # Check if the user belongs to community 3 ('Question/Answer')
        community_member = CommunityMember.objects.filter(
            phone_number=user,
            community=3,
            status='accepted'
        ).first()

        if not community_member:
            return Response(
                {"message": "You do not have access to this community."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=user)  # Assign the PhoneNumber instance
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
class AdminQuestionListAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # The authenticated PhoneNumber instance

        # Check if the user is an admin of community 3 ('Question/Answer')
        community_member = CommunityMember.objects.filter(
            phone_number=user,
            community=3,
            role='admin',
            status='accepted'  # Use 'accepted' or 'approved' based on your STATUS_CHOICES
        ).first()

        if not community_member:
            return Response(
                {"message": "You do not have permission to view these questions."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Retrieve all questions, regardless of status
        questions = Question.objects.all().order_by('-created_at')

        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class AdminQuestionUpdateAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # The authenticated PhoneNumber instance

        # Check if the user is an admin of community 3 ('Question/Answer')
        community_member = CommunityMember.objects.filter(
            phone_number=user,
            community=3,
            role='admin',
            status='accepted'
        ).first()

        if not community_member:
            return Response(
                {"message": "You do not have permission to update questions."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Retrieve question_id from request data
        question_id = request.data.get('question_id')
        if not question_id:
            return Response(
                {"message": "question_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate that question_id is an integer
        try:
            question_id = int(question_id)
        except ValueError:
            return Response(
                {"message": "question_id must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the question instance
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response(
                {"message": "Question not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Serialize and validate the data
        serializer = QuestionUpdateSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Question updated successfully.",
                    "question": {
                        "id": question.id,
                        "question_title": question.question_title,
                        "description": question.description,
                        "status": question.status,
                    }
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
class AdminAnswerPostAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # The authenticated PhoneNumber instance

        # Check if the user is an admin of community 3 ('Question/Answer')
        community_member = CommunityMember.objects.filter(
            phone_number=user,
            community=3,
            role='admin',
            status='accepted'
        ).first()

        if not community_member:
            return Response(
                {"message": "You do not have permission to answer questions."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AnswerSerializer(data=request.data)
        if serializer.is_valid():
            # Retrieve question_id from validated data
            question_id = serializer.validated_data.pop('question_id')
            try:
                question = Question.objects.get(id=question_id)
            except Question.DoesNotExist:
                return Response(
                    {"message": "Question not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Create the answer
            serializer.save(created_by=user, question=question)
            return Response(
                {
                    "message": "Answer posted successfully.",
                    "answer": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class UserQuestionListAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # The authenticated PhoneNumber instance

        # Check if the user belongs to community 3 ('Question/Answer')
        community_member = CommunityMember.objects.filter(
            phone_number=user,
            community=3,
            status='accepted'
        ).first()

        if not community_member:
            return Response(
                {"message": "You do not have access to this community."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Retrieve public questions and user's private questions
        questions = Question.objects.filter(
            Q(status='public') |
            Q(status='private', created_by=user)
        ).order_by('-created_at')

        serializer = UserQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)