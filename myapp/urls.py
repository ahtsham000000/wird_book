
from django.urls import path
from .views import RegisterPhoneNumberAPI ,VerifyOTPAPI,JoinCommunityAPI,CommunityMemberPendingListAPI,CommunityMemberStatusUpdateAPI,KhitmahAPI,KhitmahStatusAPI,KhitmahStatusUpdateAPI,NoticeboardPostAPI,NoticeboardPostListAPI,QuestionPostAPI,AdminQuestionListAPI,AdminQuestionUpdateAPI,AdminAnswerPostAPI,UserQuestionListAPI


urlpatterns = [
    path('register-phone/', RegisterPhoneNumberAPI.as_view(), name='register-phone'),
    path('verify-otp/', VerifyOTPAPI.as_view(), name='verify-otp'),
    path('join-community/', JoinCommunityAPI.as_view(), name='join-community'),
     path('community-member-pending/',CommunityMemberPendingListAPI.as_view(), name='community_member_pending'),
    path('community-member-status-update/', CommunityMemberStatusUpdateAPI.as_view(), name='community_member_status_update'),
    path('khitmah/', KhitmahAPI.as_view(), name='khitmah'),
    path('khitmahstatus/', KhitmahStatusAPI.as_view(), name='KhitmahStatusAPI'),
    path('khitmah/update-status/', KhitmahStatusUpdateAPI.as_view(), name='khitmah_status_update'),
    path('noticeboard/do-post/', NoticeboardPostAPI.as_view(), name='noticeboard_post'),
    path('noticeboard/posts/', NoticeboardPostListAPI.as_view(), name='noticeboard_posts'), 
    path('question/do-post/', QuestionPostAPI.as_view(), name='QuestionPostAPI'), 
    path('question/posts/', AdminQuestionListAPI.as_view(), name='QuestionPostAPI'),
    path('questions/admin/update/', AdminQuestionUpdateAPI.as_view(), name='AdminQuestionUpdateAPI'), 
    path('questions/admin/answer/', AdminAnswerPostAPI.as_view(), name='AdminAnswerPostAPI'),
    path('questions/user/', UserQuestionListAPI.as_view(), name='UserQuestionListAPI'),
    
     
]
