"""
Authentication Controller & Endpoints
Handles Citizen & Staff Authentication, RBAC, Multi-Channel OTPs, and Dual-OTP Email Change.
"""

import os
import json
import random
import re
import threading
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from jansahayata.db import (
    get_users_collection,
    get_email_change_requests_collection,
    hash_password,
    verify_password,
    generate_jwt_token,
    serialize_doc,
    log_audit_action
)
from jansahayata.auth_middleware import jwt_required
from services.email_service import (
    send_citizen_welcome_email,
    send_account_confirmation_otp_email,
    send_otp_verification_email,
    send_password_changed_confirmation,
    send_citizen_old_email_change_otp,
    send_citizen_new_email_verification_otp,
    send_citizen_email_change_dual_notice
)
from services.messaging_service import send_otp_sms, send_otp_whatsapp, format_phone_number

def parse_body(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception:
        return {}

def is_expired(exp, now=None):
    if not exp:
        return True
    if now is None:
        now = datetime.now(timezone.utc)
    if isinstance(exp, str):
        try:
            exp_dt = datetime.fromisoformat(exp.replace('Z', '+00:00'))
        except Exception:
            return True
    else:
        exp_dt = exp
    if not hasattr(exp_dt, 'tzinfo') or exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
    return exp_dt < now

@csrf_exempt
def register_citizen(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirmPassword', '')

    if not name or not email or not password:
        return JsonResponse({'success': False, 'message': 'Please enter your name, email, and password.'}, status=400)

    if len(name) < 3 or not re.match(r'^[a-zA-Z\s.]+$', name):
        return JsonResponse({'success': False, 'field': 'regName', 'message': 'Full name must have at least 3 letters and contain only letters.'}, status=400)

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return JsonResponse({'success': False, 'field': 'regEmail', 'message': 'Please enter a valid email address.'}, status=400)

    if len(password) < 8:
        return JsonResponse({'success': False, 'field': 'regPassword', 'message': 'Password must be at least 8 characters long.'}, status=400)

    if not re.search(r'\d', password):
        return JsonResponse({'success': False, 'field': 'regPassword', 'message': 'Password must include at least one number.'}, status=400)

    if confirm_password and password != confirm_password:
        return JsonResponse({'success': False, 'field': 'regConfirmPassword', 'message': 'Passwords do not match. Please re-enter the same password.'}, status=400)

    users = get_users_collection()
    if users.find_one({'email': email}):
        return JsonResponse({'success': False, 'field': 'regEmail', 'message': 'This email is already registered. Please sign in instead.'}, status=409)

    sanitized_phone = phone
    if phone:
        clean = re.sub(r'\D', '', phone)
        if clean.startswith('91') and len(clean) == 12:
            clean = clean[2:]
        if len(clean) == 10:
            sanitized_phone = f"+91 {clean[:5]} {clean[5:]}"

    now = datetime.now(timezone.utc)
    new_user = {
        'name': name,
        'email': email,
        'phone': sanitized_phone,
        'passwordHash': hash_password(password),
        'role': 'CITIZEN',
        'status': 'Active',
        'createdAt': now,
        'updatedAt': now
    }
    result = users.insert_one(new_user)
    new_user['_id'] = result.inserted_id

    try:
        send_citizen_welcome_email(name, email)
    except Exception as e:
        print(f"[Register Error] Could not send welcome email: {e}")

    token = generate_jwt_token(new_user)
    serialized = serialize_doc(new_user)
    serialized.pop('passwordHash', None)

    log_audit_action('CITIZEN_REGISTER', performed_by=new_user, target_type='User', target_id=new_user['_id'], details=f"New citizen registered: {email}")

    return JsonResponse({
        'success': True,
        'message': 'Registration successful! Welcome to JanSahayata.',
        'token': token,
        'user': serialized
    }, status=201)

@csrf_exempt
def register_send_otp(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    email = data.get('email', '').strip().lower()
    name = data.get('name', 'Citizen').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')

    if not email:
        return JsonResponse({'success': False, 'field': 'regEmail', 'message': 'Please enter your email address.'}, status=400)

    if not name or len(name) < 3:
        return JsonResponse({'success': False, 'field': 'regName', 'message': 'Full name must have at least 3 letters.'}, status=400)

    if len(password) < 8:
        return JsonResponse({'success': False, 'field': 'regPassword', 'message': 'Password must be at least 8 characters long.'}, status=400)

    if not re.search(r'\d', password):
        return JsonResponse({'success': False, 'field': 'regPassword', 'message': 'Password must include at least one number.'}, status=400)

    users = get_users_collection()
    existing = users.find_one({'email': email})
    if existing and existing.get('status') == 'Active':
        return JsonResponse({'success': False, 'field': 'regEmail', 'message': 'This email is already registered. Please sign in instead.'}, status=409)

    otp = str(random.randint(100000, 999999))
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    update_payload = {
        'emailVerificationOtp': otp,
        'emailVerificationOtpExpires': expires,
        'name': name or (existing.get('name') if existing else 'Citizen'),
        'role': 'CITIZEN',
    }
    if phone:
        update_payload['phone'] = phone
    if password:
        update_payload['passwordHash'] = hash_password(password)

    # Save OTP and credentials to user record or staging
    if existing:
        users.update_one({'_id': existing['_id']}, {'$set': update_payload})
    else:
        update_payload['status'] = 'Pending'
        users.update_one({'email': email}, {'$set': update_payload}, upsert=True)

    send_account_confirmation_otp_email(email, otp, name)

    resp_data = {
        'success': True,
        'message': f"A 6-digit confirmation code has been dispatched to {email}."
    }
    if not os.getenv('GMAIL_USER'):
        resp_data['debugOtp'] = otp
        print(f"\n[JANSAHAYATA OTP] Registration OTP for {email}: {otp}\n")

    return JsonResponse(resp_data)

@csrf_exempt
def register_verify_otp(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    email = data.get('email', '').strip().lower()
    otp = data.get('otp', '').strip()
    name = data.get('name', '').strip()
    password = data.get('password', '')
    phone = data.get('phone', '').strip()

    if not email or not otp:
        return JsonResponse({'success': False, 'message': 'Email and verification code are required.'}, status=400)

    users = get_users_collection()
    user = users.find_one({'email': email})
    if not user or not user.get('emailVerificationOtp'):
        return JsonResponse({'success': False, 'message': 'No pending OTP verification found for this email.'}, status=400)

    if user.get('emailVerificationOtp') != otp:
        return JsonResponse({'success': False, 'message': 'Invalid verification code. Please check and try again.'}, status=400)

    now = datetime.now(timezone.utc)
    exp = user.get('emailVerificationOtpExpires')
    if is_expired(exp, now):
        return JsonResponse({'success': False, 'message': 'Verification code has expired. Please request a new one.'}, status=400)

    # Finalize registration
    update_fields = {
        'status': 'Active',
        'emailVerificationOtp': None,
        'emailVerificationOtpExpires': None,
        'updatedAt': now
    }
    if password:
        update_fields['passwordHash'] = hash_password(password)
    if name:
        update_fields['name'] = name
    if phone:
        update_fields['phone'] = phone

    users.update_one({'_id': user['_id']}, {'$set': update_fields})
    updated_user = users.find_one({'_id': user['_id']})

    token = generate_jwt_token(updated_user)
    serialized = serialize_doc(updated_user)
    serialized.pop('passwordHash', None)

    try:
        send_citizen_welcome_email(updated_user.get('name', 'Citizen'), email)
    except Exception:
        pass

    return JsonResponse({
        'success': True,
        'message': 'Account verified and activated successfully!',
        'token': token,
        'user': serialized
    })

@csrf_exempt
def login_citizen(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    identifier = (data.get('email') or data.get('identifier', '')).strip()
    clean_identifier = identifier.lower()
    password = data.get('password', '')

    if not identifier:
        return JsonResponse({'success': False, 'field': 'email', 'message': 'Please enter your email address or mobile number.'}, status=400)

    if not password:
        return JsonResponse({'success': False, 'field': 'password', 'message': 'Please enter your password.'}, status=400)

    if len(password) < 8:
        return JsonResponse({'success': False, 'field': 'password', 'message': 'Password must be at least 8 characters long.'}, status=400)

    users = get_users_collection()
    if '@' in clean_identifier:
        user = users.find_one({'email': clean_identifier})
    else:
        phone_digits = re.sub(r'\D', '', identifier)
        phone_10 = phone_digits[-10:] if len(phone_digits) >= 10 else phone_digits
        user = users.find_one({
            '$or': [
                {'phone': identifier},
                {'phone': phone_digits},
                {'phone': phone_10},
                {'phone': f"+91 {phone_10}"},
                {'phone': f"+91{phone_10}"}
            ]
        })
    if not user:
        return JsonResponse({'success': False, 'field': 'email', 'message': 'No account found with this email or mobile. Please check or register.'}, status=401)

    if not verify_password(password, user.get('passwordHash', '')):
        return JsonResponse({'success': False, 'field': 'password', 'message': 'Password is wrong. Please enter the correct password.'}, status=401)

    if user.get('status') == 'Disabled':
        return JsonResponse({'success': False, 'message': 'Your account has been deactivated. Please contact support.'}, status=403)

    token = generate_jwt_token(user)
    serialized = serialize_doc(user)
    serialized.pop('passwordHash', None)

    return JsonResponse({
        'success': True,
        'message': 'Login successful.',
        'token': token,
        'user': serialized
    })

@csrf_exempt
def login_staff(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email:
        return JsonResponse({'success': False, 'field': 'identifier', 'message': 'Please enter your official email or employee ID.'}, status=400)

    if not password:
        return JsonResponse({'success': False, 'field': 'staffPassword', 'message': 'Please enter your password.'}, status=400)

    if len(password) < 8:
        return JsonResponse({'success': False, 'field': 'staffPassword', 'message': 'Password must be at least 8 characters long.'}, status=400)

    users = get_users_collection()
    user = users.find_one({'$or': [{'email': email}, {'employeeId': data.get('email', '').strip()}]})

    if not user:
        return JsonResponse({'success': False, 'field': 'identifier', 'message': 'Official record not found. Please check your email or employee ID.'}, status=401)

    if user.get('role') not in ('EMPLOYEE', 'SUPER_ADMIN'):
        return JsonResponse({'success': False, 'message': 'Unauthorized. This portal is strictly for Government Personnel.'}, status=403)

    if not verify_password(password, user.get('passwordHash', '')):
        return JsonResponse({'success': False, 'field': 'staffPassword', 'message': 'Password is wrong. Please enter the correct password.'}, status=401)

    if user.get('status') == 'Disabled':
        return JsonResponse({'success': False, 'message': 'Your official account is deactivated. Contact Department Administrator.'}, status=403)

    token = generate_jwt_token(user)
    serialized = serialize_doc(user)
    serialized.pop('passwordHash', None)

    return JsonResponse({
        'success': True,
        'message': 'Authentication successful. Welcome Officer.',
        'token': token,
        'user': serialized,
        'mustResetPassword': bool(user.get('mustResetPassword', False))
    })

@csrf_exempt
@jwt_required
def get_current_user(request):
    user = request.current_user
    serialized = serialize_doc(user)
    serialized.pop('passwordHash', None)
    return JsonResponse({'success': True, 'user': serialized})

@csrf_exempt
@jwt_required
def logout_user(request):
    return JsonResponse({'success': True, 'message': 'Successfully logged out.'})

@csrf_exempt
@jwt_required
def first_time_reset_password(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    new_password = data.get('newPassword', '')
    confirm_password = data.get('confirmPassword', '')

    if not new_password or len(new_password) < 8:
        return JsonResponse({'success': False, 'message': 'New password must be at least 8 characters long.'}, status=400)

    if confirm_password and new_password != confirm_password:
        return JsonResponse({'success': False, 'message': 'Passwords do not match.'}, status=400)

    users = get_users_collection()
    users.update_one(
        {'_id': request.current_user['_id']},
        {'$set': {'passwordHash': hash_password(new_password), 'mustResetPassword': False, 'updatedAt': datetime.now(timezone.utc)}}
    )

    return JsonResponse({'success': True, 'message': 'Password successfully reset.'})

@csrf_exempt
@jwt_required
def send_password_otp(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    channel = data.get('channel', 'email')
    user = request.current_user

    otp = str(random.randint(100000, 999999))
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    users = get_users_collection()
    users.update_one(
        {'_id': user['_id']},
        {'$set': {'resetPasswordOtp': otp, 'resetPasswordOtpExpires': expires}}
    )

    if channel == 'sms' and user.get('phone'):
        send_otp_sms(user['phone'], otp, user.get('name', 'User'))
    elif channel == 'whatsapp' and user.get('phone'):
        send_otp_whatsapp(user['phone'], otp, user.get('name', 'User'))
    else:
        send_otp_verification_email(user['email'], otp, user.get('name', 'User'), action="Password Change")

    resp_data = {'success': True, 'message': f'Verification OTP dispatched via {channel.upper()}.'}
    if not os.getenv('GMAIL_USER'):
        resp_data['debugOtp'] = otp
        print(f"\n[JANSAHAYATA OTP] Password Reset OTP for {user.get('email')}: {otp}\n")

    return JsonResponse(resp_data)

@csrf_exempt
@jwt_required
def change_password_with_otp(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    otp = data.get('otp', '').strip()
    new_password = data.get('newPassword', '')

    user = request.current_user
    if not user.get('resetPasswordOtp') or user.get('resetPasswordOtp') != otp:
        return JsonResponse({'success': False, 'message': 'Invalid verification code.'}, status=400)

    now = datetime.now(timezone.utc)
    exp = user.get('resetPasswordOtpExpires')
    if is_expired(exp, now):
        return JsonResponse({'success': False, 'message': 'OTP has expired. Please request a new one.'}, status=400)

    users = get_users_collection()
    users.update_one(
        {'_id': user['_id']},
        {'$set': {'passwordHash': hash_password(new_password), 'resetPasswordOtp': None, 'resetPasswordOtpExpires': None, 'updatedAt': now}}
    )

    try:
        send_password_changed_confirmation(user['email'], user.get('name', 'User'))
    except Exception:
        pass

    return JsonResponse({'success': True, 'message': 'Password successfully changed!'})

# ==========================================
# Public Forgot Password & Password Recovery
# ==========================================
def mask_email(email_str):
    if not email_str or '@' not in email_str:
        return email_str or ''
    name_part, domain_part = email_str.split('@', 1)
    if len(name_part) <= 2:
        masked_name = name_part[0] + '***'
    else:
        masked_name = name_part[0] + '***' + name_part[-1]
    return f"{masked_name}@{domain_part}"

@csrf_exempt
def forgot_password_send_otp(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    identifier = data.get('email', '').strip()
    if not identifier:
        return JsonResponse({'success': False, 'message': 'Please enter your registered email address or official ID.'}, status=400)

    users = get_users_collection()
    query = {
        '$or': [
            {'email': {'$regex': f"^{re.escape(identifier)}$", '$options': 'i'}},
            {'employeeId': {'$regex': f"^{re.escape(identifier)}$", '$options': 'i'}},
            {'phone': identifier}
        ]
    }
    user = users.find_one(query)
    if not user:
        return JsonResponse({'success': False, 'message': 'No registered account found matching this email or ID.'}, status=404)

    if user.get('status') == 'Disabled':
        return JsonResponse({'success': False, 'message': 'This account has been deactivated. Please contact the administrator.'}, status=403)

    user_email = user.get('email', '').strip()
    if not user_email:
        return JsonResponse({'success': False, 'message': 'No email address registered for this account.'}, status=400)

    otp = str(random.randint(100000, 999999))
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    users.update_one(
        {'_id': user['_id']},
        {'$set': {
            'resetPasswordOtp': otp,
            'resetPasswordOtpExpires': expires
        }}
    )

    user_name = user.get('name', 'User')
    def _dispatch_email():
        try:
            send_otp_verification_email(user_email, otp, user_name, action="Password Reset")
        except Exception as e:
            print(f"[Email Warning] Forgot password OTP dispatch error: {e}")

    threading.Thread(target=_dispatch_email, daemon=True).start()

    resp_data = {
        'success': True,
        'message': '6-digit OTP has been sent to your registered email.',
        'email': user_email,
        'destinationLabel': mask_email(user_email)
    }

    if not os.getenv('GMAIL_USER'):
        resp_data['debugOtp'] = otp
        print(f"\n[FORGOT PASSWORD OTP] Reset OTP for {user_email}: {otp}\n")

    return JsonResponse(resp_data)

@csrf_exempt
def forgot_password_verify_otp(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    identifier = data.get('email', '').strip()
    otp = data.get('otp', '').strip()

    if not identifier or not otp:
        return JsonResponse({'success': False, 'message': 'Email address and 6-digit OTP code are required.'}, status=400)

    users = get_users_collection()
    query = {
        '$or': [
            {'email': {'$regex': f"^{re.escape(identifier)}$", '$options': 'i'}},
            {'employeeId': {'$regex': f"^{re.escape(identifier)}$", '$options': 'i'}},
            {'phone': identifier}
        ]
    }
    user = users.find_one(query)
    if not user:
        return JsonResponse({'success': False, 'message': 'Account not found.'}, status=404)

    stored_otp = user.get('resetPasswordOtp')
    if not stored_otp or str(stored_otp).strip() != otp:
        return JsonResponse({'success': False, 'message': 'Invalid verification code. Please check and try again.'}, status=400)

    now = datetime.now(timezone.utc)
    exp = user.get('resetPasswordOtpExpires')
    if is_expired(exp, now):
        return JsonResponse({'success': False, 'message': 'Verification code has expired. Please request a new one.'}, status=400)

    return JsonResponse({'success': True, 'message': 'Verification code verified successfully.'})

@csrf_exempt
def forgot_password_reset_password(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    identifier = data.get('email', '').strip()
    otp = data.get('otp', '').strip()
    new_password = data.get('newPassword', '')

    if not identifier or not otp or not new_password:
        return JsonResponse({'success': False, 'message': 'All fields are required.'}, status=400)

    if len(new_password) < 8:
        return JsonResponse({'success': False, 'message': 'New password must be at least 8 characters long.'}, status=400)

    if not re.search(r'\d', new_password):
        return JsonResponse({'success': False, 'message': 'New password must contain at least one numeric digit (0-9).'}, status=400)

    users = get_users_collection()
    query = {
        '$or': [
            {'email': {'$regex': f"^{re.escape(identifier)}$", '$options': 'i'}},
            {'employeeId': {'$regex': f"^{re.escape(identifier)}$", '$options': 'i'}},
            {'phone': identifier}
        ]
    }
    user = users.find_one(query)
    if not user:
        return JsonResponse({'success': False, 'message': 'Account not found.'}, status=404)

    stored_otp = user.get('resetPasswordOtp')
    if not stored_otp or str(stored_otp).strip() != otp:
        return JsonResponse({'success': False, 'message': 'Invalid verification code.'}, status=400)

    now = datetime.now(timezone.utc)
    exp = user.get('resetPasswordOtpExpires')
    if is_expired(exp, now):
        return JsonResponse({'success': False, 'message': 'Verification code has expired. Please request a new one.'}, status=400)

    users.update_one(
        {'_id': user['_id']},
        {
            '$set': {
                'passwordHash': hash_password(new_password),
                'resetPasswordOtp': None,
                'resetPasswordOtpExpires': None,
                'mustResetPassword': False,
                'updatedAt': now
            }
        }
    )

    user_email = user.get('email')
    user_name = user.get('name', 'User')
    if user_email:
        def _dispatch_confirmation():
            try:
                send_password_changed_confirmation(user_email, user_name)
            except Exception as e:
                print(f"[Email Warning] Confirmation email error: {e}")
        threading.Thread(target=_dispatch_confirmation, daemon=True).start()

    log_audit_action(
        'FORGOT_PASSWORD_RESET',
        performed_by={'userId': str(user['_id']), 'name': user_name, 'email': user_email, 'role': user.get('role', 'CITIZEN')},
        target_type='User',
        target_id=str(user['_id']),
        details=f"Password successfully reset via forgot password verification flow for {user_email}"
    )

    return JsonResponse({'success': True, 'message': 'Password successfully changed! You can now sign in with your new password.'})

# ==========================================
# Citizen Email Change (Dual OTP & Admin Approval)
# ==========================================
@csrf_exempt
@jwt_required
def send_citizen_current_email_otp(request):
    user = request.current_user
    otp = str(random.randint(100000, 999999))
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    users = get_users_collection()
    users.update_one(
        {'_id': user['_id']},
        {'$set': {'currentEmailOtp': otp, 'currentEmailOtpExpires': expires, 'emailChangeCurrentVerified': False}}
    )

    send_citizen_old_email_change_otp(user['email'], otp, user.get('name', 'Citizen'))
    return JsonResponse({'success': True, 'message': f"Verification code sent to current email {user['email']}."})

@csrf_exempt
@jwt_required
def verify_citizen_current_email_otp(request):
    data = parse_body(request)
    otp = data.get('otp', '').strip()
    user = request.current_user

    if not user.get('currentEmailOtp') or user.get('currentEmailOtp') != otp:
        return JsonResponse({'success': False, 'message': 'Invalid OTP.'}, status=400)

    now = datetime.now(timezone.utc)
    exp = user.get('currentEmailOtpExpires')
    if is_expired(exp, now):
        return JsonResponse({'success': False, 'message': 'OTP has expired.'}, status=400)

    users = get_users_collection()
    users.update_one(
        {'_id': user['_id']},
        {'$set': {'emailChangeCurrentVerified': True, 'currentEmailOtp': None}}
    )
    return JsonResponse({'success': True, 'message': 'Current email ownership verified successfully.'})

@csrf_exempt
@jwt_required
def send_citizen_new_email_otp(request):
    data = parse_body(request)
    new_email = data.get('newEmail', '').strip().lower()
    user = request.current_user

    if not user.get('emailChangeCurrentVerified'):
        return JsonResponse({'success': False, 'message': 'Please verify current email first.'}, status=400)

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email):
        return JsonResponse({'success': False, 'message': 'Invalid new email format.'}, status=400)

    users = get_users_collection()
    if users.find_one({'email': new_email}):
        return JsonResponse({'success': False, 'message': 'This new email is already registered.'}, status=409)

    otp = str(random.randint(100000, 999999))
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    users.update_one(
        {'_id': user['_id']},
        {'$set': {'pendingNewEmail': new_email, 'newEmailOtp': otp, 'newEmailOtpExpires': expires}}
    )

    send_citizen_new_email_verification_otp(new_email, otp, user.get('name', 'Citizen'))
    return JsonResponse({'success': True, 'message': f"Verification code sent to new email {new_email}."})

@csrf_exempt
@jwt_required
def confirm_citizen_new_email(request):
    data = parse_body(request)
    otp = data.get('otp', '').strip()
    user = request.current_user

    if not user.get('newEmailOtp') or user.get('newEmailOtp') != otp:
        return JsonResponse({'success': False, 'message': 'Invalid OTP for new email.'}, status=400)

    now = datetime.now(timezone.utc)
    exp = user.get('newEmailOtpExpires')
    if is_expired(exp, now):
        return JsonResponse({'success': False, 'message': 'OTP has expired.'}, status=400)

    old_email = user.get('email')
    new_email = user.get('pendingNewEmail')

    users = get_users_collection()
    users.update_one(
        {'_id': user['_id']},
        {
            '$set': {
                'email': new_email,
                'pendingNewEmail': None,
                'newEmailOtp': None,
                'newEmailOtpExpires': None,
                'emailChangeCurrentVerified': False,
                'updatedAt': now
            }
        }
    )

    try:
        send_citizen_email_change_dual_notice(old_email, new_email, user.get('name', 'Citizen'))
    except Exception:
        pass

    log_audit_action('CITIZEN_EMAIL_CHANGE', performed_by=user, target_type='User', target_id=user['_id'], details=f"Email changed from {old_email} to {new_email}")

    updated_user = users.find_one({'_id': user['_id']})
    token = generate_jwt_token(updated_user)
    serialized = serialize_doc(updated_user)
    serialized.pop('passwordHash', None)

    return JsonResponse({
        'success': True,
        'message': 'Email updated successfully!',
        'token': token,
        'user': serialized
    })

@csrf_exempt
@jwt_required
def request_citizen_admin_email_change(request):
    data = parse_body(request)
    new_email = data.get('newEmail', '').strip().lower()
    reason = data.get('reason', '').strip()
    user = request.current_user

    if not new_email or not reason:
        return JsonResponse({'success': False, 'message': 'New email and justification reason are required.'}, status=400)

    requests_col = get_email_change_requests_collection()
    now = datetime.now(timezone.utc)
    req_doc = {
        'role': 'CITIZEN',
        'user': user['_id'],
        'citizenName': user.get('name', 'Citizen'),
        'currentEmail': user.get('email'),
        'requestedEmail': new_email,
        'reason': reason,
        'contactPhone': user.get('phone', ''),
        'status': 'PENDING',
        'createdAt': now,
        'updatedAt': now
    }
    requests_col.insert_one(req_doc)

    return JsonResponse({'success': True, 'message': 'Email change request submitted for Administrator review.'})

@csrf_exempt
@jwt_required
def get_citizen_email_change_status(request):
    user = request.current_user
    requests_col = get_email_change_requests_collection()
    pending = requests_col.find_one({'user': user['_id']}, sort=[('createdAt', -1)])
    return JsonResponse({'success': True, 'request': serialize_doc(pending)})

@csrf_exempt
@jwt_required
def change_password(request):
    """Direct password change for logged-in citizen, officer, or super admin with current password verification."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    data = parse_body(request)
    current_password = data.get('currentPassword', '')
    new_password = data.get('newPassword', '')
    confirm_password = data.get('confirmPassword', '')

    if not current_password or not new_password:
        return JsonResponse({'success': False, 'message': 'Current password and new password are required.'}, status=400)

    user = request.current_user
    if not verify_password(current_password, user.get('passwordHash', '')):
        return JsonResponse({'success': False, 'message': 'Incorrect current password.'}, status=400)

    if len(new_password) < 6:
        return JsonResponse({'success': False, 'message': 'New password must be at least 6 characters long.'}, status=400)

    if confirm_password and new_password != confirm_password:
        return JsonResponse({'success': False, 'message': 'New passwords do not match.'}, status=400)

    users = get_users_collection()
    users.update_one(
        {'_id': user['_id']},
        {'$set': {
            'passwordHash': hash_password(new_password),
            'mustResetPassword': False,
            'updatedAt': datetime.now(timezone.utc)
        }}
    )
    log_audit_action('PASSWORD_CHANGED', performed_by=user, target_type='User', target_id=user['_id'], details=f"{user.get('role')} updated account password")
    return JsonResponse({'success': True, 'message': 'Account password has been successfully updated.'})

@csrf_exempt
@jwt_required
def change_email(request):
    """Direct email change for logged-in citizen or officer with password verification. Super Admin is restricted."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    user = request.current_user
    if user.get('role') == 'SUPER_ADMIN':
        return JsonResponse({'success': False, 'message': 'Super Administrator email address cannot be changed.'}, status=403)

    data = parse_body(request)
    new_email = data.get('newEmail', '').strip().lower()
    current_password = data.get('currentPassword', '')

    if not new_email or not current_password:
        return JsonResponse({'success': False, 'message': 'New email and current password are required.'}, status=400)

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email):
        return JsonResponse({'success': False, 'message': 'Please enter a valid email address.'}, status=400)

    if not verify_password(current_password, user.get('passwordHash', '')):
        return JsonResponse({'success': False, 'message': 'Incorrect password.'}, status=400)

    if new_email == user.get('email', '').lower():
        return JsonResponse({'success': False, 'message': 'New email must be different from your current email.'}, status=400)

    users = get_users_collection()
    existing = users.find_one({'email': new_email})
    if existing and str(existing.get('_id')) != str(user.get('_id')):
        return JsonResponse({'success': False, 'message': 'An account with this email address already exists.'}, status=409)

    now = datetime.now(timezone.utc)
    users.update_one(
        {'_id': user['_id']},
        {'$set': {
            'email': new_email,
            'updatedAt': now
        }}
    )
    user['email'] = new_email
    new_token = generate_jwt_token(user)
    serialized = serialize_doc(user)
    serialized.pop('passwordHash', None)

    log_audit_action('EMAIL_CHANGED', performed_by=user, target_type='User', target_id=user['_id'], details=f"{user.get('role')} changed email to {new_email}")
    return JsonResponse({
        'success': True,
        'message': 'Email address successfully updated.',
        'user': serialized,
        'token': new_token
    })

