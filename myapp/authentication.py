# authentication.py

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import PhoneNumber, Token

class PhoneNumberJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None  # No authentication header provided

        try:
            prefix, token = auth_header.split(' ')
            if prefix.lower() != 'bearer':
                raise AuthenticationFailed('Invalid token prefix.')
        except ValueError:
            raise AuthenticationFailed('Invalid token header. No credentials provided.')

        try:
            # Decode the token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            number = payload.get('number')
            if not number:
                raise AuthenticationFailed('Invalid token payload.')

            phone_number = PhoneNumber.objects.get(number=number)

            # Verify that the token matches the one stored in the database
            token_instance = Token.objects.get(phone_number=phone_number)
            if token != token_instance.jwt_token:
                raise AuthenticationFailed('Invalid or expired token.')

            # Return the phone_number and payload
            return (phone_number, payload)

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired.')
        except jwt.DecodeError:
            raise AuthenticationFailed('Error decoding token.')
        except PhoneNumber.DoesNotExist:
            raise AuthenticationFailed('Phone number does not exist.')
        except Token.DoesNotExist:
            raise AuthenticationFailed('Token does not exist.')
