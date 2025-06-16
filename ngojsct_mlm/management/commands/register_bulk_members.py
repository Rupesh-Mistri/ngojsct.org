from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ngojsct_mlm.models import MemberModel
from ngojsct_mlm.forms import CustomUserCreationForm, MemberModelForm
from django.test.client import RequestFactory
from django.contrib.auth import login
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from ngojsct_mlm.views import distribution_of_amount

User = get_user_model()

class Command(BaseCommand):
    help = "Bulk register 1500 members"

    def handle(self, *args, **kwargs):
        factory = RequestFactory()
        total_created = 0

        for i in range(16):
            latest_user = User.objects.last()
            number = int(latest_user.memberID[4:]) + 1 if latest_user else 1
            memberID = f"JSCT{number:06d}"

            sponsor_user = User.objects.filter(memberID='JSCT000002').first()
            sponsor_member = MemberModel.objects.filter(user_detail=sponsor_user).first()

            email = f"user{number}@example.com"
            phone = str(9000000000 + i)  # Unique number
            name = f"User{number}"

            post_data = {
                'email': email,
                'name': name,
                'password1': 'Test@123',
                'password2': 'Test@123',
                'user_type': 'Individual',
                'phone_number': phone,
                'address': f"Address {number}",
                'sponserID': sponsor_user.memberID if sponsor_user else '',
                'sponsorName': 'Tst',
                'aadhaar': "876543213454",
                'pincode': "543216",
                'registration_fee': 1551,
                'pan_no': 'EMDEE4321T',
            }

            # Create a fake POST request with session and messages
            request = factory.post('/register/', data=post_data)
            request.user = AnonymousUser()

            # Add session middleware support
            middleware = SessionMiddleware(lambda req: None)
            middleware.process_request(request)
            request.session.save()

            # Attach messages framework
            messages = FallbackStorage(request)
            setattr(request, '_messages', messages)

            form = CustomUserCreationForm(post_data)
            mform = MemberModelForm(post_data)

            if (sponsor_member or i == 0) and form.is_valid() and mform.is_valid():
                user = form.save(commit=False)
                user.memberID = memberID
                user.save()

                member = mform.save(commit=False)
                member.user_detail = user
                member.name = user.name
                member.address = user.address
                member.sponser_member = sponsor_member if sponsor_member else None
                member.rank = 'Not Available'
                member.save()

                if member.id:
                    distribution_of_amount(request, member.id)
                    total_created += 1
                    print(f"[{total_created}/1500] Registered: {user.memberID}")
            else:
                print(f"❌ Failed to create user {memberID}")
                print("User form errors:", form.errors)
                print("Member form errors:", mform.errors)

        print(f"\n✅ Finished. Total members registered: {total_created}")
