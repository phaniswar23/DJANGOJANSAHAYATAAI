"""
JanSahayata AI Database Adapter (SQLite & Django ORM)
Provides complete collection wrapper methods matching the PyMongo interface
backed 100% by Django ORM and local SQLite (db.sqlite3).
Zero external database dependencies (no MongoDB required).
"""

import os
import re
from datetime import datetime, date, timezone
import bcrypt
import jwt
from django.utils import timezone as dj_timezone
from django.db.models import Q

JWT_SECRET = os.getenv('JWT_SECRET', 'jansahayata_gov_secure_jwt_secret_key_2026_capstone_token')

# ==========================================
# Security: Password Hashing & Verification
# ==========================================
def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(10)
    return bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

# ==========================================
# Security: JWT Token Generation & Decode
# ==========================================
def generate_jwt_token(user: dict) -> str:
    user_id = str(user.get('_id') or user.get('id') or '')
    dept = user.get('department') or {}
    payload = {
        'userId': user_id,
        'email': user.get('email', ''),
        'role': user.get('role', 'CITIZEN'),
        'departmentId': dept.get('id') if isinstance(dept, dict) else None
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def decode_jwt_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])

# ==========================================
# Serialization Helper
# ==========================================
def serialize_doc(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        res = {}
        for k, v in doc.items():
            if k == '_id':
                res['_id'] = str(v)
                res['id'] = str(v)
            elif isinstance(v, datetime):
                res[k] = v.isoformat()
            elif isinstance(v, dict):
                res[k] = serialize_doc(v)
            elif isinstance(v, list):
                res[k] = serialize_doc(v)
            else:
                res[k] = v
        return res
    if hasattr(doc, 'to_dict'):
        return doc.to_dict()
    return doc


class InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = str(inserted_id)

class UpdateResult:
    def __init__(self, modified_count=1):
        self.modified_count = modified_count

class DeleteResult:
    def __init__(self, deleted_count=0):
        self.deleted_count = deleted_count


class MongoCursor:
    """Cursor that wraps list of dictionaries with MongoDB-like chaining."""
    def __init__(self, items):
        self.items = items

    def sort(self, key_or_list, direction=None):
        if not self.items:
            return self
        if isinstance(key_or_list, list):
            # E.g. [('createdAt', -1)]
            for key, d in reversed(key_or_list):
                reverse = (d == -1 or d == 'desc' or d == 'DESC')
                self.items.sort(key=lambda x: (x.get(key) is not None, str(x.get(key) or '')), reverse=reverse)
        elif isinstance(key_or_list, str):
            reverse = (direction == -1 or direction == 'desc')
            self.items.sort(key=lambda x: (x.get(key_or_list) is not None, str(x.get(key_or_list) or '')), reverse=reverse)
        return self

    def skip(self, n):
        self.items = self.items[n:]
        return self

    def limit(self, n):
        self.items = self.items[:n]
        return self

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]


def sanitize_json_val(val):
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, dict):
        return {k: sanitize_json_val(v) for k, v in val.items()}
    if isinstance(val, list):
        return [sanitize_json_val(v) for v in val]
    return val

class SQLiteCollectionAdapter:
    """Adapts a Django ORM model to look like a PyMongo collection."""
    def __init__(self, model_class):
        self.model = model_class

    def _matches_filter(self, doc, query):
        if not query:
            return True
        for k, v in query.items():
            if k == '$or':
                if not any(self._matches_filter(doc, sub_q) for sub_q in v):
                    return False
                continue
            if k == '$and':
                if not all(self._matches_filter(doc, sub_q) for sub_q in v):
                    return False
                continue

            val = doc.get(k)
            if k == '_id' or k == 'id':
                val = str(doc.get('_id') or doc.get('id') or '')
                v_str = str(v)
                if val != v_str:
                    return False
                continue

            # Nested dot notation: 'department.id'
            if '.' in k:
                parts = k.split('.')
                curr = doc
                for p in parts:
                    if isinstance(curr, dict):
                        curr = curr.get(p)
                    else:
                        curr = None
                        break
                val = curr

            if isinstance(v, dict):
                if '$regex' in v:
                    pattern = v['$regex']
                    options = v.get('$options', '')
                    flags = re.IGNORECASE if 'i' in options else 0
                    if not re.search(pattern, str(val or ''), flags):
                        return False
                elif '$ne' in v:
                    if str(val) == str(v['$ne']):
                        return False
                elif '$in' in v:
                    if val not in v['$in'] and str(val) not in [str(x) for x in v['$in']]:
                        return False
                elif '$nin' in v:
                    if val in v['$nin'] or str(val) in [str(x) for x in v['$nin']]:
                        return False
                elif '$exists' in v:
                    exists = (val is not None)
                    if exists != bool(v['$exists']):
                        return False
                elif '$gte' in v or '$lte' in v or '$gt' in v or '$lt' in v:
                    # Comparison logic
                    try:
                        c_val = str(val or '')
                        if '$gte' in v and not (c_val >= str(v['$gte'])): return False
                        if '$gt' in v and not (c_val > str(v['$gt'])): return False
                        if '$lte' in v and not (c_val <= str(v['$lte'])): return False
                        if '$lt' in v and not (c_val < str(v['$lt'])): return False
                    except Exception:
                        return False
            else:
                if str(val or '').strip().lower() != str(v or '').strip().lower():
                    return False
        return True

    def find_one(self, query=None, sort=None):
        query = query or {}
        # Direct lookup optimization
        if '_id' in query and len(query) == 1:
            try:
                obj = self.model.objects.get(id=int(str(query['_id'])))
                return obj.to_dict()
            except Exception:
                return None
        if 'email' in query and len(query) == 1 and hasattr(self.model, 'email'):
            try:
                obj = self.model.objects.get(email__iexact=str(query['email']).strip())
                return obj.to_dict()
            except Exception:
                return None
        if 'complaintId' in query and len(query) == 1 and hasattr(self.model, 'complaintId'):
            try:
                obj = self.model.objects.get(complaintId__iexact=str(query['complaintId']).strip())
                return obj.to_dict()
            except Exception:
                return None

        for obj in self.model.objects.all():
            doc = obj.to_dict()
            if self._matches_filter(doc, query):
                return doc
        return None

    def find(self, query=None, projection=None):
        query = query or {}
        results = []
        for obj in self.model.objects.all():
            doc = obj.to_dict()
            if self._matches_filter(doc, query):
                results.append(doc)
        return MongoCursor(results)

    def insert_one(self, doc_data):
        clean_data = dict(doc_data)
        clean_data.pop('_id', None)
        clean_data.pop('id', None)

        # Separate known model fields from dynamic extra fields
        model_fields = {f.name for f in self.model._meta.get_fields()}
        known_data = {}
        extra_data = {}

        for k, v in clean_data.items():
            if isinstance(v, datetime) and not hasattr(v, 'tzinfo'):
                v = dj_timezone.make_aware(v)
            elif isinstance(v, (dict, list)):
                v = sanitize_json_val(v)

            if k in model_fields:
                known_data[k] = v
            else:
                extra_data[k] = sanitize_json_val(v)

        if 'extraData' in model_fields and extra_data:
            known_data['extraData'] = sanitize_json_val(extra_data)

        obj = self.model(**known_data)
        obj.save()
        doc_data['_id'] = str(obj.id)
        doc_data['id'] = str(obj.id)
        return InsertOneResult(obj.id)

    def insert_many(self, docs):
        results = []
        for d in docs:
            results.append(self.insert_one(d))
        return results

    def update_one(self, query, update_dict, upsert=False, *args, **kwargs):
        target = self.find_one(query)
        if not target:
            if upsert:
                new_doc = dict(query)
                # Remove query operator keys if any
                new_doc = {k: v for k, v in new_doc.items() if not k.startswith('$')}
                sets = update_dict.get('$set', {})
                new_doc.update(sets)
                set_on_insert = update_dict.get('$setOnInsert', {})
                new_doc.update(set_on_insert)
                self.insert_one(new_doc)
                return UpdateResult(1)
            return UpdateResult(0)

        obj = self.model.objects.get(id=int(target['_id']))
        model_fields = {f.name for f in self.model._meta.get_fields()}

        sets = update_dict.get('$set', {})
        for k, v in sets.items():
            if isinstance(v, (dict, list)):
                v = sanitize_json_val(v)
            if '.' in k:
                # Nested update: e.g. 'feedback.rating' or 'department.name'
                parent, child = k.split('.', 1)
                curr_parent = getattr(obj, parent, {}) or {}
                if isinstance(curr_parent, dict):
                    curr_parent[child] = v
                    setattr(obj, parent, curr_parent)
            elif k in model_fields:
                if isinstance(v, datetime) and not hasattr(v, 'tzinfo'):
                    v = dj_timezone.make_aware(v)
                setattr(obj, k, v)
            elif hasattr(obj, 'extraData'):
                extra = getattr(obj, 'extraData', {}) or {}
                if isinstance(v, datetime):
                    v = v.isoformat()
                extra[k] = v
                obj.extraData = extra

        # Handle $unset
        unsets = update_dict.get('$unset', {})
        for k in unsets.keys():
            if hasattr(obj, 'extraData') and k in (obj.extraData or {}):
                obj.extraData.pop(k, None)
            elif hasattr(obj, k):
                setattr(obj, k, None)

        # Handle $push
        pushes = update_dict.get('$push', {})
        for k, v in pushes.items():
            if hasattr(obj, k):
                curr_list = getattr(obj, k, []) or []
                if isinstance(curr_list, list):
                    curr_list.append(v)
                    setattr(obj, k, curr_list)

        obj.save()
        return UpdateResult(1)

    def delete_many(self, query=None):
        if not query:
            count = self.model.objects.count()
            self.model.objects.all().delete()
            return DeleteResult(count)
        deleted = 0
        for obj in self.model.objects.all():
            if self._matches_filter(obj.to_dict(), query):
                obj.delete()
                deleted += 1
        return DeleteResult(deleted)

    def count_documents(self, query=None):
        query = query or {}
        if not query:
            return self.model.objects.count()
        return sum(1 for obj in self.model.objects.all() if self._matches_filter(obj.to_dict(), query))

    def create_index(self, *args, **kwargs):
        pass  # Handled natively by SQLite model db_index


# Lazy collection getters
def get_users_collection():
    from apps.authentication.models import User
    return SQLiteCollectionAdapter(User)

def get_complaints_collection():
    from apps.complaints.models import Complaint
    return SQLiteCollectionAdapter(Complaint)

def get_audit_logs_collection():
    from apps.complaints.models import AuditLog
    return SQLiteCollectionAdapter(AuditLog)

def get_email_change_requests_collection():
    from apps.authentication.models import EmailChangeRequest
    return SQLiteCollectionAdapter(EmailChangeRequest)

def init_db_indexes():
    pass

# Helper to generate unique complaint ID
def generate_complaint_id(dept_code='JNS') -> str:
    from apps.complaints.models import Complaint
    prefix = (dept_code or 'JNS').upper().strip()
    current_year = datetime.now().year
    count = Complaint.objects.count()
    seq = count + 1
    while True:
        candidate_id = f"{prefix}-{current_year}-{str(seq).zfill(6)}"
        if not Complaint.objects.filter(complaintId=candidate_id).exists():
            return candidate_id
        seq += 1

# Helper: System Audit Logger
def log_audit_action(action, performed_by=None, target_type='System', target_id='', details='', ip_address='127.0.0.1', metadata=None):
    try:
        from apps.complaints.models import AuditLog
        performed_by_doc = {
            'userId': str(performed_by.get('_id') or performed_by.get('id') or '') if performed_by else None,
            'name': performed_by.get('name', 'System') if performed_by else 'System',
            'email': performed_by.get('email', '') if performed_by else '',
            'role': performed_by.get('role', 'SYSTEM') if performed_by else 'SYSTEM'
        }
        AuditLog.objects.create(
            action=action,
            performedBy=performed_by_doc,
            targetType=target_type,
            targetId=str(target_id),
            details=details,
            ipAddress=ip_address,
            metadata=metadata or {}
        )
    except Exception as e:
        print(f"[AuditLog Error] Could not record log: {e}")
