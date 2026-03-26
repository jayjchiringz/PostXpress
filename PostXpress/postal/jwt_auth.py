# PostXpress/postal/jwt_auth.py
import jwt
import logging
from django.conf import settings
from django.contrib.auth.models import User, Group
from rest_framework import authentication, exceptions
from rest_framework.authentication import BaseAuthentication

logger = logging.getLogger(__name__)

class FarmFuzionJWTAuthentication(BaseAuthentication):
    """
    Custom authentication that validates JWT tokens from FarmFuzion
    """
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        try:
            # Extract token (Bearer <token>)
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return None
            
            token = parts[1]
            
            # Decode and validate token
            payload = jwt.decode(
                token, 
                settings.FARMFUZION_JWT_SECRET,
                algorithms=['HS256'],
                options={'verify_aud': False}  # Allow for now, we'll add audience later
            )
            
            # Log the payload for debugging
            logger.info(f"JWT Payload received: {payload}")
            
            # Get or create user in Django based on FarmFuzion user data
            user = self.get_or_create_user(payload)
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise exceptions.AuthenticationFailed('Invalid token')
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise exceptions.AuthenticationFailed('Authentication failed')
    
    def get_or_create_user(self, payload):
        """
        Map FarmFuzion user to Django user
        """
        # Extract user information from JWT payload
        farmfuzion_user_id = payload.get('user_id')
        email = payload.get('email')
        username = payload.get('username') or (email.split('@')[0] if email else 'unknown')
        first_name = payload.get('first_name', '')
        last_name = payload.get('last_name', '')
        roles = payload.get('roles', [])
        
        if not email:
            logger.error("No email in JWT payload")
            raise exceptions.AuthenticationFailed('No email provided in token')
        
        # Get or create user in Django
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': f"{username}_{farmfuzion_user_id}" if farmfuzion_user_id else username,
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True,
            }
        )
        
        if created:
            logger.info(f"Created new user from FarmFuzion: {user.username} (ID: {user.id})")
        else:
            # Update user info if needed
            if user.first_name != first_name or user.last_name != last_name:
                user.first_name = first_name
                user.last_name = last_name
                user.save()
                logger.info(f"Updated user info for: {user.username}")
        
        # Store FarmFuzion user ID in user profile if available
        if hasattr(user, 'userprofile'):
            user.userprofile.farmfuzion_id = farmfuzion_user_id
            user.userprofile.save()
        
        # Assign groups based on FarmFuzion roles
        self.assign_groups(user, roles)
        
        return user
    
    def assign_groups(self, user, roles):
        """
        Map FarmFuzion roles to Django groups
        """
        # Get or create default groups
        farmer_group, _ = Group.objects.get_or_create(name='farmer')
        staff_group, _ = Group.objects.get_or_create(name='staff')
        admin_group, _ = Group.objects.get_or_create(name='admin')
        
        # Clear existing groups
        user.groups.clear()
        
        # Assign groups based on roles
        assigned_groups = []
        
        # Map FarmFuzion roles to Django groups
        if 'farmer' in roles or 'Farmer' in roles:
            assigned_groups.append(farmer_group)
        
        if 'staff' in roles or 'Staff' in roles:
            assigned_groups.append(staff_group)
        
        if 'admin' in roles or 'Admin' in roles:
            assigned_groups.append(admin_group)
        
        # If no specific roles assigned, default to farmer
        if not assigned_groups:
            assigned_groups.append(farmer_group)
            logger.info(f"User {user.username} assigned default farmer role")
        
        # Add all assigned groups
        for group in assigned_groups:
            user.groups.add(group)
            logger.info(f"User {user.username} added to group: {group.name}")
            