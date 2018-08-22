import datetime
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import APIException
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.views import JSONWebTokenAPIView

from accounts import tasks
from accounts.models import User, Token
from accounts.permissions import PublicEndpoint
from accounts.serializers import UserSerializer
from rest_framework.viewsets import ModelViewSet, ViewSet


class VerifyViewSet(JSONWebTokenAPIView):
    """
    API View that receives a POST with a user's email and password.
    Returns a JSON Web Token that can be used for authenticated requests.
    """

    queryset = User.objects.all()
    serializer_class = JSONWebTokenSerializer

    def validate(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            token = serializer.object.get('token')

            response_data = self.jwt_response_payload_handler(token, user)

            return Response(response_data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def jwt_response_payload_handler(token, user):
        user_data = UserSerializer(user).data

        return {
            'token': token,
            'user': user_data
        }


@permission_classes((AllowAny, ))
class RegisterViewSet(ViewSet):
    """
    API View that receives a POST with a new user's email and password
    Returns JSON that includes user ID, roles, etc...
    """

    serializer_class = UserSerializer
    permission_classes = (PublicEndpoint,)

    def create(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            tasks.message.delay('verify', recipient=request.data['email'])
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(ModelViewSet):
    """
    API View that receives a GET to query a user by ID
    Return User model as JSON
    """

    # TODO: Check user permissions to query users

    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRoleViewSet(ViewSet):
    """
    API View that receives POST, PUT, DELETE to changes a user's role
    Returns response code for success or failure
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer


class ConfirmUserViewSet(ViewSet):
    """
    Confirm a user's email address
    """

    queryset = Token.objects.all()
    lookup_field = 'id'
    permission_classes = (PublicEndpoint,)

    def confirm(self, request, *args, **kwargs):
        _id = request.query_params.get('id')
        token = get_object_or_404(self.queryset, pk=_id)

        # If token is older than expiration timestamp, it's expired, user must request a new token.
        # Reset current datetime to minus 5 hours to sync with Reelio's timezone
        if token.expires.replace(tzinfo=None) < datetime.datetime.now():
            raise APIException(detail='Token expired')

        token.user.is_verified = True
        token.user.save()

        # After user is verified, remove the token
        token.delete()

        return Response()


class ResetConfirmUserToken(ViewSet):
    """
    Request a new verification token for a User
    """

    queryset = User.objects.all()
    permission_classes = (PublicEndpoint,)

    def confirm(self, request, *args, **kwargs):
        email = request.data['email']

        user = get_object_or_404(self.queryset, email=email)

        tokens = Token.objects.filter(user=user)
        for token in tokens:
            token.delete()

        tasks.message.delay('verify', recipient=email)

        return Response()


class PasswordChangeRequestViewSet(ViewSet):
    """
    Request that a user's password be reset
    """

    queryset = User.objects.all()
    permission_classes = (PublicEndpoint,)

    def create(self, request, *args, **kwargs):
        email = request.data['email']

        get_object_or_404(self.queryset, email=email)

        tasks.message.delay('reset', recipient=email)

        return Response()


class PasswordChangeViewSet(ViewSet):
    """
    Change user's password
    """

    queryset = Token.objects.all()
    permission_classes = (PublicEndpoint,)

    def change(self, request, *args, **kwargs):
        _id = self.kwargs.get('id')
        password = request.data['password']

        token = get_object_or_404(self.queryset, pk=_id)

        # If token is older than expiration timestamp, it's expired, user must request a new token.
        if token.expires.replace(tzinfo=None) < datetime.datetime.now():
            raise APIException(detail='Token expired')

        token.user.set_password(password)

        token.user.save()

        token.delete()

        return Response()
