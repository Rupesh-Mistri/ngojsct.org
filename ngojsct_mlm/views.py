from django.shortcuts import render,redirect
from . forms import *
from django.http import JsonResponse
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import login, logout, authenticate
from .models import *
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
import json
from .utilities import login_req
from decimal import Decimal

from django.contrib.auth import get_user_model

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        form = MemberLoginForm(request.POST)
        if form.is_valid():
            username_input = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Try to find user by email or memberID
            try:
                if '@' in username_input:
                    user_obj = User.objects.get(email=username_input)
                else:
                    user_obj = User.objects.get(memberID=username_input)
            except User.DoesNotExist:
                user_obj = None

            if user_obj:
                user = authenticate(request, email=user_obj.email, password=password)
                if user:
                    member=MemberModel.objects.filter(user_detail_id=user.id).first()
                    login(request, user)
                    if user.is_superuser == False and member.mode_of_payment=='Online':
                        return redirect(f'/checkout/{member.id}')
                    else:
                        return redirect('dashboard')
                else:
                    form.add_error(None, 'Invalid credentials')
            else:
                form.add_error(None, 'No user found with this Email or Member ID')
    else:
        form = MemberLoginForm()

    return render(request, 'login_view.html', {'form': form})

# def register_view(request):
#     form= MemberRegistrationForm()
#     if form.is_valid():
#         form.save()
#     else:
#         print(form.errors)
#     return render(request,'register_view.html',{'form':form})

def register_view(request):
    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST)

        latest_member = CustomUser.objects.last()

        if latest_member:
            # Assuming the format is 'TPD<Number>'
            split_number_part = int(latest_member.memberID[4:])  # Extract number part
            memberID = f"JSCT{split_number_part + 1:06d}"  # Increment and pad with zeros
        else:
            memberID = "JSCT000001"  # Start with this if no records exist

        if form.is_valid():
            member = form.save(commit=False)

            # Determine sponsor
            senior_ID = request.POST.get('senior_ID')
            sponsor_member = MemberModel.objects.filter(user_detail__memberID=senior_ID).first()
            member_count = MemberModel.objects.count()

            if sponsor_member or member_count == 0:
                # Link sponsor
                member.sponser_member = sponsor_member if member_count != 0 else None
                member.rank = 'Not Available'
                member.registration_fee = 1551
                member.save()

                # Do distribution + referral
                distribution_of_amount(request, member.id)
                if memberID != "JSCT000001":
                    member_refferal_benefits(request, member.id)
                    DonationsModel.objects.create(
                        member_id       = member.id,
                        amount          = 1551,
                        slip_for        ='Registration'
                    )
                messages.success(request, "Registration successful! You can now log in.")

                # Login the user
                user = member.user_detail
                print('User:', user)
                # user.backend = 'cmsapp.backends.CustomUserAuthenticationBackend'
                # login(request, user)
                if member.mode_of_payment=='Online':
                     return redirect(f'/checkout/{member.id}')
                else:
                    return redirect('login')

            else:
                messages.error(request, "This sponsor ID is not valid")
                print("This sponsor ID is not valid")
        else:
            print(form.errors)
    else:
        form = MemberRegistrationForm()

    return render(request, 'register_view.html', {'form': form})


def distribution_of_amount(request, member_id):
    user_type = request.GET.get('user_type', 'individual')  # or get it from authenticated user
    print(f'member_id:{member_id}')
    # Fixed values
    total_amount = 1551
    leader_expense = 50
    tour = 50
    board_members = 25
    admin_expense = 110
    social_work = 15
    misc = 10
    product_cost = 440
    karykarta_fund = 25

    ngo_reserve_fund = 526

    # Create the expense record
    expanse = ExpanseModel.objects.create(
        member_id=member_id,
        # user_type=user_type,
        total_amount=total_amount,
        leader_expense=leader_expense,
        tour=tour,
        board_members=board_members,
        admin_expense=admin_expense,
        social_work=social_work,
        misc=misc,
        product_cost=product_cost,
        karykarta_fund=karykarta_fund,
        ngo_reserve_fund=ngo_reserve_fund
    )
    level_income(request,member_id)
    


    # return JsonResponse({'status': 'success', 'expanse_id': expanse.id})
def get_all_upliners(user_id):
    member = MemberModel.objects.filter(user_detail_id=user_id).first()
    upliners = []
    while member and member.sponser_member:
        member = member.sponser_member
        upliners.append(member)
    return upliners

def level_income(request, member_id):
    level_income_values = {
        '1': 100,
        '2': 70,
        '3': 40,
        '4': 25,
        '5': 15,
        '6': 10,
        '7': 10,
        '8': 10,
        '9': 10,
        '10': 10,
    }

    upliners = get_all_upliners(member_id)
    referee = MemberModel.objects.get(id=member_id)

    for idx, upliner in enumerate(upliners[:10]):  # Limit to 10 levels
        level = str(idx + 1)
        commission_earned = level_income_values.get(level, 0)

        # Eligibility check for levels 6 to 10
        if int(level) >= 6:
            # Check if upliner has enough direct referrals
            direct_refs = MemberModel.objects.filter(sponser_member=upliner, is_active=True)
            if direct_refs.count() < int(level):
                continue  # Not enough direct referrals

            # Get the nth direct referral (0-based index)
            try:
                nth_direct_ref = direct_refs.order_by('id')[int(level) - 1]
            except IndexError:
                continue  # Direct referral not found

            # Check if nth_direct_ref has at least 5 active direct referrals
            level1_refs = MemberModel.objects.filter(sponser_member=nth_direct_ref, is_active=True)
            if level1_refs.count() < 5:
                continue  # Not eligible for income

        # Passed eligibility checks (or not required for level < 6)
        LevelIncomeDistributionModel.objects.create(
            referrer=upliner,
            referee=referee,
            level=level,
            income=commission_earned,
            created_at=now(),
            updated_at=now(),
            status=1
        )

        

def log_fund_distribution(member, amount, reason):
    """
    Logs fund distribution to a member.
    """
    FundDistributionModel.objects.create(
        member=member,
        amount=amount,
        reason=reason,
        status=True
    )

def get_downliners(member_id, level=5, current_level=1, visited=None):
    """
    Recursively fetches downline members up to a given level.
    
    Args:
        member_id (int): The ID of the member whose downline to retrieve.
        level (int): Maximum level depth to retrieve.
        current_level (int): Used internally to track recursion depth.
        visited (set): Set of visited member IDs to avoid cycles.

    Returns:
        List[MemberModel]: A flat list of downline members up to the given level.
    """
    if visited is None:
        visited = set()

    if current_level > level:
        return []

    visited.add(member_id)

    # Get direct downline members
    downliners = MemberModel.objects.filter(sponser_member_id=member_id, is_active=True)

    all_downliners = list(downliners)

    # Recurse for each downliner
    for member in downliners:
        if member.id not in visited:
            all_downliners += get_downliners(member.id, level, current_level + 1, visited)

    return all_downliners


def member_refferal_benefits(request, member_id):
    print('member_id:',member_id)
    referee = MemberModel.objects.get(user_detail_id=member_id)
    referrer=MemberModel.objects.get(user_detail_id=referee.sponser_member_id)
    upliners = get_all_upliners(member_id)
    print("TYTUUUUUUUUUUUU")
    now = timezone.now()
    joining_deadline = referrer.joining_date + timedelta(days=30)

    # Count active members within level 5 under this member
    active_downliners = get_downliners(referrer.sponser_member_id, level=5)
    active_within_30_days = [
        m for m in active_downliners if m.is_active and m.joining_date <= joining_deadline
    ]
    print('ASFE:',active_within_30_days)
    print('LEngth:',len(active_within_30_days))
    print('RRRARA',referrer.rank )
    # Condition 1: पंचायत को-ऑर्डिनटोर
    if referrer.rank == 'Not Available' and len(active_within_30_days) >= 1500:
        print('NNNNNNNNNNNNNNNNNN')
        referrer.rank = 'panchayat_coordinator'
        referrer.save()
        # Log ₹10 benefit
        log_fund_distribution(referee, 10, 'Upon becoming the Panchayat Coordinator')

    # Condition 2: ब्लॉक को-ऑर्डिनटोर
    if referrer.rank == 'panchayat_coordinator':
        count = MemberModel.objects.filter(sponser_member_id=referrer.user_detail_id, rank='panchayat_coordinator').count()
        if count >= 15:
            referrer.rank = 'block_coordinator'
            referrer.save()
            log_fund_distribution(referee, 7, 'Upon becoming the Block Coordinator')

    # Condition 3: डिस्ट्रिक्ट को-ऑर्डिनटोर
    if referrer.rank == 'block_coordinator':
        count = MemberModel.objects.filter(sponser_member_id=referrer.user_detail_id, rank='block_coordinator').count()
        if count >= 15:
            referrer.rank = 'district_coordinator'
            referrer.save()
            log_fund_distribution(referee, 5, 'Upon becoming the Distric Coordinator')

    # Condition 4: स्टेट को-ऑर्डिनटोर
    if referrer.rank == 'district_coordinator':
        count = MemberModel.objects.filter(sponser_member_id=referrer.user_detail_id, rank='district_coordinator').count()
        if count >= 15:
            referrer.rank = 'state_coordinator'
            referrer.save()
            log_fund_distribution(referee, 3, 'Upon becoming the State Coordinator')
        
    # LevelIncomeDistributionModel.objects.create(
        
    # )  # Clear previous data
    # Get all members




def cascade_ajax(request):
    if request.method == 'POST':
        level = request.POST.get('level')  # Get the current level (e.g., 'district', 'block', etc.)
        value = request.POST.get('value')  # Get the selected value from the previous dropdown

        if not level or not value:
            return JsonResponse([], safe=False)  # Return an empty list if parameters are missing
        if level == 'state':
            record = StateModel.objects.filter(name=value).first()
            if record:
                results = CityModel.objects.filter(state_id=record.id)
        else:
            return JsonResponse([], safe=False)  # Return empty if the level is invalid

        # Prepare the results as a list of dictionaries
        if results:
            data = [{"name": item.name} for item in results]
        else:
            data = []

        return JsonResponse(data, safe=False)

    return JsonResponse([], safe=False)  # Return empty list for non-POST requests

def get_sponser_name_ajax(request):
    if request.method == 'POST':
        sponserID= request.POST.get('sponserID')
        user= CustomUser.objects.filter(memberID=sponserID).first()
        if user:
           data={"name": user.applicant_name,"status":True}
        #    print(data)
           return JsonResponse(data, safe=False) 
    return JsonResponse([],safe=False)


@login_req
def dashboard(request):
    user=request.user
    user_id=user.id
    print(user_id)
    member_dtl= MemberModel.objects.filter(user_detail_id=user_id).first()
    level_income=LevelIncomeDistributionModel.objects.filter(referrer=member_dtl.id).aggregate(total=Sum('income'))['total'] or 0
    total_no_of_member_reffered= MemberModel.objects.filter(sponser_member=user_id).count()
    position_income=FundDistributionModel.objects.filter(member_id=user_id).first()
    if position_income:
        position_income = position_income.amount
    else:
        position_income = 0
    total_balance= level_income+ position_income
    
    return render(request,'dashboard.html',
                  {'level_income':level_income,'member_dtl':member_dtl,'total_no_of_member_reffered':total_no_of_member_reffered,'position_income':position_income
                   
                   ,'total_balance':total_balance}
                  )


def logout_view(request):
    """
    Logs out the currently logged-in user and redirects to the homepage.
    """
    logout(request)
    return redirect('login')  # Redirect to the login page after logout

@login_req
def donation_slip_list(request):
    user=request.user
    user_id=user.id
    member_dtl= MemberModel.objects.filter(user_detail_id=user_id).first()
    print('Member Details:', member_dtl.id)
    donation_list=DonationsModel.objects.filter(member_id=member_dtl.id)
    return render(request,'donation_slip_list.html',{'donation_list':donation_list})

def donation_slip(request,id):
    """
    Renders the donation slip page.
    """
    slip_dtl=DonationsModel.objects.filter(id=id).first()
    member_dtl=MemberModel.objects.filter(id=slip_dtl.member_id).first()
    return render(request, 'donation_slip.html',{'slip_dtl':slip_dtl,'member_dtl':member_dtl})

@login_req
def level_data(request):
    user=request.user
    user_id=user.id
    tree= build_tree(user_id)
    # print(tree)
    return render(request,'level_data.html',{'tree':json.dumps(tree)})

def build_tree(id):
    user=CustomUser.objects.filter(id=id).first()
    member = MemberModel.objects.filter(id=id).first()
    if not member:
        return None

    # Query for children where the current member is the sponsor
    children = MemberModel.objects.filter(sponser_member_id=member.id)
    tree = {
        'member': {'name':member.applicant_name,'memberID':user.memberID,'rank':member.rank,'is_active':member.is_active},
        'children': []
    }

    # Recursively build the tree for each child
    for child in children:
        subtree = build_tree(child.id)
        if subtree:
            tree['children'].append(subtree)

    return tree


@login_req
def profile(request):
    """
    Displays the user profile.
    """
    user_details = request.user  # Use Django's built-in user handling
    member_details = MemberModel.objects.filter(user_detail_id=user_details.id).first()
    return render(request, 'profile.html', {'member_details': member_details})


from django.db.models import Sum, F, Value as V, DecimalField
from django.db.models.functions import Coalesce

@login_req
def wallet(request):
    user = request.user

    aggregates = WalletModel.objects.filter(member_id=user.id).aggregate(
        credited=Coalesce(Sum('credited'), Decimal(0), output_field=DecimalField()),
        debited=Coalesce(Sum('debited'), Decimal(0), output_field=DecimalField()),
    )
    total_balance = aggregates['credited'] - aggregates['debited']

    dropdown_options = build_flat_tree(id=user.id)  # For transfer recipient select

    if request.method == 'POST':
        credited = request.POST.get('credited')
        print('hgjfdsg')
        # If Transfer button clicked
        if 'transfer_btn' in request.POST and user.is_superuser==True:
            member = request.POST.get('member')
            print('hgjg')
            if not member:
                messages.error(request, "Please select a recipient member.")
                return redirect('wallet')
            
            try:
                credited_amount = Decimal(credited)
            except:
                messages.error(request, "Invalid amount entered.")
                return redirect('wallet')

            if total_balance < credited_amount:
                messages.error(request, "Insufficient balance to transfer this amount.")
                return redirect('wallet')

            # Credit to recipient
            WalletModel.objects.create(
                member_id=member,
                credited=credited_amount,
                debited=Decimal(0),
            )

            # Debit from sender
            WalletModel.objects.create(
                member_id=user.id,
                credited=Decimal(0),
                debited=credited_amount,
            )

            messages.success(request, "Amount transferred successfully!")
            return redirect('wallet')

        # If Add Fund button clicked
        elif 'fund_add_btn' in request.POST and user.is_superuser==True:
            try:
                credited_amount = Decimal(credited)
            except:
                messages.error(request, "Invalid amount entered.")
                return redirect('wallet')

            WalletModel.objects.create(
                member_id=user.id,
                credited=credited_amount,
                debited=Decimal(0),
            )

            messages.success(request, "Funds added successfully!")
            return redirect('wallet')

    return render(request, 'wallet.html', {
        'total_balance': total_balance,
        'dropdown_options': dropdown_options
    })


def build_flat_tree(id, depth=0, result=None):
    if result is None:
        result = []

    user = CustomUser.objects.filter(id=id).first()
    member = MemberModel.objects.filter(id=id).first()

    if not member or not user:
        return result
    if user.memberID != 'JSCT000001':
        label = f"{'--' * depth} {member.applicant_name} ({user.memberID})"
        result.append({'value': user.id, 'label': label})

    # Get direct children of this member (sponsored members)
    children = MemberModel.objects.filter(sponser_member_id=member.id)

    for child in children:
        result = build_flat_tree(child.id, depth + 1, result)

    return result
@login_req
def activate_member(request):
    user_dtl = request.user
    dropdown_options = build_flat_tree(id=request.user.id)
    aggregates = WalletModel.objects.filter(member_id=user_dtl.id).aggregate(
        credited=Coalesce(Sum('credited'), Decimal(0), output_field=DecimalField()),
        debited=Coalesce(Sum('debited'), Decimal(0), output_field=DecimalField()),
    )
    total_balance = aggregates['credited'] - aggregates['debited']

    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        print('Member ID:', member_id)
        member = MemberModel.objects.filter(user_detail__id=member_id).first()
        
        if member:


            if total_balance < 1551:
                messages.error(request, "Insufficient balance to transfer this amount.")
                return redirect('activate_member')
            

            debited= WalletModel.objects.create(
                member_id=user_dtl.id,
                credited=0.00,
                debited=1551.00,
                member_whom_activated=member_id,
                member_activated_by=member_id,
            )

            credits= WalletModel.objects.create(
                member_id=member_id,
                credited=1551.00,
                debited=0.00,
                member_whom_activated=member_id,
                member_activated_by=user_dtl.id,

            )
            member.is_active = True
            member.status=2
            member.save()

            messages.success(request, f"Member {member.applicant_name} activated successfully.")
        else:
            messages.error(request, "Member not found.")
    return render(request, 'activate_member.html',{'dropdown_options':dropdown_options,'total_balance':total_balance})


@login_req
def deactivate_member(request):
    user_dtl = request.user
    dropdown_options = build_flat_tree(id=request.user.id)
    # aggregates = WalletModel.objects.filter(member_id=user_dtl.id).aggregate(
    #     credited=Coalesce(Sum('credited'), Decimal(0), output_field=DecimalField()),
    #     debited=Coalesce(Sum('debited'), Decimal(0), output_field=DecimalField()),
    # )
    # total_balance = aggregates['credited'] - aggregates['debited']

    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        print('Member ID:', member_id)
        member = MemberModel.objects.filter(user_detail__id=member_id).first()
        
        if member:


            # debited= WalletModel.objects.create(
            #     member_id=user_dtl.id,
            #     credited=0.00,
            #     debited=1551.00,
            #     # reason='Amount Credited',
            # )

            # credits= WalletModel.objects.create(
            #     member_id=member_id,
            #     credited=1551.00,
            #     debited=0.00,
            #     # reason='Amount Credited',
            # )
            member.is_active = False
            member.status=0
            member.save()

            messages.success(request, f"Member {member.applicant_name} activated successfully.")
        else: 
            messages.error(request, "Member not found.")
    return render(request, 'deactivate_member.html',{'dropdown_options':dropdown_options,})
    


