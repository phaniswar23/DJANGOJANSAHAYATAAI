"""
Database Seeder for JanSahayata AI (Django & SQLite)
Seeds Super Admin, All 8 Department Grievance Officers, 3 Citizen Accounts,
and realistic Complaints across every department with rich timelines and statuses.
"""

import os
import django
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jansahayata.settings')
django.setup()

from jansahayata.db import (
    get_users_collection,
    get_complaints_collection,
    get_audit_logs_collection,
    get_email_change_requests_collection,
    hash_password,
    init_db_indexes
)

def run_seed():
    print("[Seed] Initializing SQLite database connection...")
    init_db_indexes()

    users_col = get_users_collection()
    complaints_col = get_complaints_collection()
    audit_col = get_audit_logs_collection()
    requests_col = get_email_change_requests_collection()

    # Clear existing collections
    users_col.delete_many({})
    complaints_col.delete_many({})
    audit_col.delete_many({})
    requests_col.delete_many({})
    print("[Seed] Cleared existing User, Complaint, and Audit collections.")

    now = datetime.now(timezone.utc)
    officer_pass = hash_password('Officer@2026!')
    citizen_pass = hash_password('Citizen@2026!')

    # 1. Super Admin Account
    admin_pass = os.getenv('SUPER_ADMIN_PASSWORD', 'Admin@JanSahayata2026!')
    admin_user = {
        'name': 'Phaniswar',
        'email': os.getenv('SUPER_ADMIN_EMAIL', 'admin@jansahayata.gov.in').lower(),
        'phone': '+91 94150 11223',
        'passwordHash': hash_password(admin_pass),
        'role': 'SUPER_ADMIN',
        'department': {
            'id': 'governance',
            'code': 'GOV',
            'name': 'Ministry of Public Grievance & Administrative Reforms'
        },
        'employeeId': 'DIR-ADM-0001',
        'designation': 'Principal Secretary / Chief Administrative Director',
        'status': 'Active',
        'mustResetPassword': False,
        'createdAt': now,
        'updatedAt': now
    }
    admin_res = users_col.insert_one(admin_user)
    admin_id = admin_res.inserted_id
    print(f"[Seed] Created Super Admin: {admin_user['email']}")

    # 2. Government Officers across all 8 Departments
    officers = [
        {
            'name': 'K. Kiran Sai Karthik',
            'email': 'officer.railway@jansahayata.gov.in',
            'phone': '+91 98480 22334',
            'passwordHash': officer_pass,
            'role': 'EMPLOYEE',
            'department': {'id': 'railway', 'code': 'RLY', 'name': 'Railway Department'},
            'employeeId': 'RLY-EMP-1001',
            'designation': 'Station Superintendent / Zonal Grievance Officer',
            'status': 'Active',
            'mustResetPassword': False,
            'createdAt': now,
            'updatedAt': now
        },
        {
            'name': 'P. Balaji Sri Ram',
            'email': 'officer.water@jansahayata.gov.in',
            'phone': '+91 97230 44556',
            'passwordHash': officer_pass,
            'role': 'EMPLOYEE',
            'department': {'id': 'water_supply', 'code': 'WTR', 'name': 'Water Supply & Sewerage Board'},
            'employeeId': 'WTR-EMP-2001',
            'designation': 'Assistant Executive Engineer (Water Works)',
            'status': 'Active',
            'mustResetPassword': False,
            'createdAt': now,
            'updatedAt': now
        },
        {
            'name': 'P. Balu Lakshman Pavan',
            'email': 'officer.muni@jansahayata.gov.in',
            'phone': '+91 98850 33445',
            'passwordHash': officer_pass,
            'role': 'EMPLOYEE',
            'department': {'id': 'municipality', 'code': 'MUN', 'name': 'Municipal Corporation'},
            'employeeId': 'MUN-EMP-3001',
            'designation': 'Chief Sanitary Inspector & Civic Nodal Officer',
            'status': 'Active',
            'mustResetPassword': False,
            'createdAt': now,
            'updatedAt': now
        },
        {
            'name': 'K. Pavan Kalyan',
            'email': 'officer.roads@jansahayata.gov.in',
            'phone': '+91 95020 66778',
            'passwordHash': officer_pass,
            'role': 'EMPLOYEE',
            'department': {'id': 'roads_infra', 'code': 'RDS', 'name': 'Roads & Infrastructure (PWD)'},
            'employeeId': 'RDS-EMP-4001',
            'designation': 'Assistant Engineer (Civil Infrastructure)',
            'status': 'Active',
            'mustResetPassword': False,
            'createdAt': now,
            'updatedAt': now
        },
        {
            'name': 'Allada Pavan',
            'email': 'officer.electricity@jansahayata.gov.in',
            'phone': '+91 94400 55667',
            'passwordHash': officer_pass,
            'role': 'EMPLOYEE',
            'department': {'id': 'electricity', 'code': 'ELE', 'name': 'Electricity Board (DISCOM)'},
            'employeeId': 'ELE-EMP-5001',
            'designation': 'Assistant Divisional Engineer (Power & Distribution)',
            'status': 'Active',
            'mustResetPassword': False,
            'createdAt': now,
            'updatedAt': now
        },
        {
            'name': 'Dr. Sunita Deshmukh',
            'email': 'officer.health@jansahayata.gov.in',
            'phone': '+91 94220 77889',
            'passwordHash': officer_pass,
            'role': 'EMPLOYEE',
            'department': {'id': 'health_sanitation', 'code': 'PHS', 'name': 'Public Health & Sanitation'},
            'employeeId': 'PHS-EMP-6001',
            'designation': 'District Health Officer / Vector Control Nodal',
            'status': 'Active',
            'mustResetPassword': False,
            'createdAt': now,
            'updatedAt': now
        },
        {
            'name': 'Ramesh Chandra Roy',
            'email': 'officer.education@jansahayata.gov.in',
            'phone': '+91 93310 88990',
            'passwordHash': officer_pass,
            'role': 'EMPLOYEE',
            'department': {'id': 'education', 'code': 'EDU', 'name': 'Department of Education'},
            'employeeId': 'EDU-EMP-7001',
            'designation': 'Block Education Officer / Infrastructure Audit',
            'status': 'Active',
            'mustResetPassword': False,
            'createdAt': now,
            'updatedAt': now
        },
        {
            'name': 'Vikramjeet Singh',
            'email': 'officer.transport@jansahayata.gov.in',
            'phone': '+91 98140 99001',
            'passwordHash': officer_pass,
            'role': 'EMPLOYEE',
            'department': {'id': 'public_transport', 'code': 'TRN', 'name': 'State Public Transport'},
            'employeeId': 'TRN-EMP-8001',
            'designation': 'Depot Traffic Manager / Passenger Redressal',
            'status': 'Active',
            'mustResetPassword': False,
            'createdAt': now,
            'updatedAt': now
        }
    ]
    users_col.insert_many(officers)
    print(f"[Seed] Created {len(officers)} Department Grievance Officers across all 8 departments.")

    # 3. Citizen Accounts (Demo Citizen + 2 New Citizen Accounts)
    citizens = [
        {
            'name': 'Ravi Teja Sharma',
            'email': 'citizen@gmail.com',
            'phone': '+91 98765 43210',
            'passwordHash': citizen_pass,
            'role': 'CITIZEN',
            'status': 'Active',
            'createdAt': now,
            'updatedAt': now
        },
        {
            'name': 'Pooja Verma',
            'email': 'citizen.pooja@gmail.com',
            'phone': '+91 98123 45678',
            'passwordHash': citizen_pass,
            'role': 'CITIZEN',
            'status': 'Active',
            'createdAt': now,
            'updatedAt': now
        },
        {
            'name': 'Amit Kumar Sharma',
            'email': 'citizen.amit@gmail.com',
            'phone': '+91 97123 45679',
            'passwordHash': citizen_pass,
            'role': 'CITIZEN',
            'status': 'Active',
            'createdAt': now,
            'updatedAt': now
        }
    ]
    c_res = users_col.insert_many(citizens)
    citizen_ids = [str(r.inserted_id) for r in c_res]
    cid1, cid2, cid3 = citizen_ids[0], citizen_ids[1], citizen_ids[2]
    print(f"[Seed] Created 3 Citizen Accounts: {', '.join([c['email'] for c in citizens])}")

    # 4. Realistic Grievance Complaints across EVERY Department
    complaints = [
        # --- 1. RAILWAY (In Progress) ---
        {
            'complaintId': 'RLY-2026-000001',
            'citizenId': cid1,
            'citizenName': 'Ravi Teja Sharma',
            'citizenEmail': 'citizen@gmail.com',
            'citizenPhone': '+91 98765 43210',
            'citizenDetails': {'name': 'Ravi Teja Sharma', 'email': 'citizen@gmail.com', 'phone': '+91 98765 43210'},
            'description': 'Deep 2x2m pothole and cracked pavement near platform 2 close to central tea stall, creating tripping hazard for boarding passengers.',
            'generatedProblemStatement': 'Official Grievance Statement: Hazardous pavement collapse at Platform 2 North Section near Coach S4 position. Immediate masonry leveling required.',
            'category': 'Railway Infrastructure Damage',
            'department': {'id': 'railway', 'code': 'RLY', 'name': 'Railway Department'},
            'urgency': 'High',
            'location': 'Secunderabad Junction - Platform 2 North Section, Secunderabad, Telangana',
            'coordinates': {'lat': 17.4344, 'lng': 78.5015},
            'status': 'In Progress',
            'progressUpdates': [
                {
                    'status': 'Submitted',
                    'message': 'Grievance submitted by citizen and routed automatically to Railway Department.',
                    'officer': {'name': 'JanSahayata AI System', 'department': 'Railway Department', 'role': 'Dispatcher'},
                    'timestamp': now - timedelta(hours=36)
                },
                {
                    'status': 'In Progress',
                    'message': 'Site inspected by civil gang. Paver blocks procured and masonry repair underway.',
                    'officer': {'name': 'K. Kiran Sai Karthik', 'department': 'Railway Department', 'role': 'Station Superintendent'},
                    'timestamp': now - timedelta(hours=12)
                }
            ],
            'createdAt': now - timedelta(hours=36),
            'updatedAt': now - timedelta(hours=12)
        },
        # --- 2. WATER SUPPLY (Under Review) ---
        {
            'complaintId': 'WTR-2026-000002',
            'citizenId': cid2,
            'citizenName': 'Pooja Verma',
            'citizenEmail': 'citizen.pooja@gmail.com',
            'citizenPhone': '+91 98123 45678',
            'citizenDetails': {'name': 'Pooja Verma', 'email': 'citizen.pooja@gmail.com', 'phone': '+91 98123 45678'},
            'description': 'Municipal tap water has strong foul odor and yellowish turbidity for the past 48 hours, rendering it unsafe for drinking.',
            'generatedProblemStatement': 'Official Grievance Statement: Turbid and contaminated domestic water supply in Sector 4 residential colony. Potential underground sewage seepage suspected.',
            'category': 'Contaminated Water Supply',
            'department': {'id': 'water_supply', 'code': 'WTR', 'name': 'Water Supply & Sewerage Board'},
            'urgency': 'High',
            'location': 'Street 7, Sector 4 Housing Board Colony, Phagwara, Punjab 144411',
            'coordinates': {'lat': 31.2241, 'lng': 75.7712},
            'status': 'Under Review',
            'progressUpdates': [
                {
                    'status': 'Submitted',
                    'message': 'Ingested into Water Supply Redressal System.',
                    'officer': {'name': 'JanSahayata System', 'department': 'Water Board', 'role': 'System'},
                    'timestamp': now - timedelta(hours=28)
                },
                {
                    'status': 'Under Review',
                    'message': 'Sampling squad scheduled water quality test at distribution main junction.',
                    'officer': {'name': 'P. Balaji Sri Ram', 'department': 'Water Supply Board', 'role': 'Asst Executive Engineer'},
                    'timestamp': now - timedelta(hours=6)
                }
            ],
            'createdAt': now - timedelta(hours=28),
            'updatedAt': now - timedelta(hours=6)
        },
        # --- 3. MUNICIPALITY (Resolved with Proof) ---
        {
            'complaintId': 'MUN-2026-000003',
            'citizenId': cid1,
            'citizenName': 'Ravi Teja Sharma',
            'citizenEmail': 'citizen@gmail.com',
            'citizenPhone': '+91 98765 43210',
            'citizenDetails': {'name': 'Ravi Teja Sharma', 'email': 'citizen@gmail.com', 'phone': '+91 98765 43210'},
            'description': 'Open solid waste dump overflowing across 50 meters of main road, blocking pedestrian walkway and emitting unbearable stench.',
            'generatedProblemStatement': 'Official Grievance Statement: Chronic solid waste dumping and blocked storm water drain cleared by mechanical loader compactor.',
            'category': 'Garbage / Waste Overflow',
            'department': {'id': 'municipality', 'code': 'MUN', 'name': 'Municipal Corporation'},
            'urgency': 'Medium',
            'location': 'Opposite Old Grain Market, GT Road Junction, Jalandhar, Punjab',
            'coordinates': {'lat': 31.3260, 'lng': 75.5762},
            'status': 'Resolved',
            'resolutionProof': {
                'officerNotes': 'Sanitation team deployed with hydraulic compactor truck. Entire 4-ton waste heap cleared, road disinfected with bleaching powder, and No-Dumping signage installed.',
                'resolvedAt': now - timedelta(hours=4),
                'resolvedBy': 'P. Balu Lakshman Pavan (Chief Sanitary Inspector)'
            },
            'progressUpdates': [
                {
                    'status': 'Submitted',
                    'message': 'Grievance submitted by citizen.',
                    'officer': {'name': 'System', 'department': 'Municipal Corporation', 'role': 'Ingestion'},
                    'timestamp': now - timedelta(hours=48)
                },
                {
                    'status': 'In Progress',
                    'message': 'Sanitation supervisor deployed hydraulic skip loader to site.',
                    'officer': {'name': 'P. Balu Lakshman Pavan', 'department': 'Municipal Corporation', 'role': 'Sanitary Inspector'},
                    'timestamp': now - timedelta(hours=24)
                },
                {
                    'status': 'Resolved',
                    'message': 'Waste completely evacuated, lime spray completed. Issue marked Resolved.',
                    'officer': {'name': 'P. Balu Lakshman Pavan', 'department': 'Municipal Corporation', 'role': 'Sanitary Inspector'},
                    'timestamp': now - timedelta(hours=4)
                }
            ],
            'createdAt': now - timedelta(hours=48),
            'updatedAt': now - timedelta(hours=4)
        },
        # --- 4. ROADS & INFRASTRUCTURE (Disputed) ---
        {
            'complaintId': 'RDS-2026-000004',
            'citizenId': cid3,
            'citizenName': 'Amit Kumar Sharma',
            'citizenEmail': 'citizen.amit@gmail.com',
            'citizenPhone': '+91 97123 45679',
            'citizenDetails': {'name': 'Amit Kumar Sharma', 'email': 'citizen.amit@gmail.com', 'phone': '+91 97123 45679'},
            'description': 'Massive potholes on NH-44 highway bypass flyover ramp. Heavy vehicles getting stuck.',
            'generatedProblemStatement': 'Official Grievance Statement: Highway carriage way crater damage. Citizen disputed previous hasty patch as gravel washed away in 24 hours.',
            'category': 'Pothole / Road Damage',
            'department': {'id': 'roads_infra', 'code': 'RDS', 'name': 'Roads & Infrastructure (PWD)'},
            'urgency': 'High',
            'location': 'NH-44 Bypass Flyover Approach Ramp, Phagwara, Punjab',
            'coordinates': {'lat': 31.2180, 'lng': 75.7620},
            'status': 'Disputed',
            'dispute': {
                'isDisputed': True,
                'disputedAt': now - timedelta(hours=8),
                'citizenRemarks': 'The cold mix gravel laid yesterday was completely washed out by morning rain. Potholes are deeper than before. Re-inspection required immediately!'
            },
            'progressUpdates': [
                {
                    'status': 'Submitted',
                    'message': 'Citizen lodged road damage grievance.',
                    'officer': {'name': 'System', 'department': 'PWD', 'role': 'Dispatcher'},
                    'timestamp': now - timedelta(days=3)
                },
                {
                    'status': 'Resolved',
                    'message': 'Officer marked resolved following patch work.',
                    'officer': {'name': 'K. Pavan Kalyan', 'department': 'PWD Roads', 'role': 'Assistant Engineer'},
                    'timestamp': now - timedelta(hours=14)
                },
                {
                    'status': 'Disputed',
                    'message': 'Citizen verified site and filed Dispute: patch wash-away noted. Reopened for executive inspection.',
                    'officer': {'name': 'System Dispute Cell', 'department': 'JanSahayata Grievance Mediation', 'role': 'Mediation'},
                    'timestamp': now - timedelta(hours=8)
                }
            ],
            'createdAt': now - timedelta(days=3),
            'updatedAt': now - timedelta(hours=8)
        },
        # --- 5. ELECTRICITY (Escalated - Critical Hazard) ---
        {
            'complaintId': 'ELE-2026-000005',
            'citizenId': cid2,
            'citizenName': 'Pooja Verma',
            'citizenEmail': 'citizen.pooja@gmail.com',
            'citizenPhone': '+91 98123 45678',
            'citizenDetails': {'name': 'Pooja Verma', 'email': 'citizen.pooja@gmail.com', 'phone': '+91 98123 45678'},
            'description': 'High-tension 11kV conductor snapped and dangling 5 feet above street level outside government girls school. Sparking continuously during wind.',
            'generatedProblemStatement': 'CRITICAL SAFETY ESCALATION: Dangling high-voltage 11kV wire posing imminent electrocution hazard near school gate. Power feeder isolation ordered.',
            'category': 'Hanging Live Wire / Shock Hazard',
            'department': {'id': 'electricity', 'code': 'ELE', 'name': 'Electricity Board (DISCOM)'},
            'urgency': 'Critical',
            'location': 'Substation Feeder 3, Model Town near Girls Sr Sec School, Phagwara',
            'coordinates': {'lat': 31.2290, 'lng': 75.7780},
            'status': 'Escalated',
            'escalation': {
                'isEscalated': True,
                'escalatedAt': now - timedelta(hours=2),
                'escalationReason': 'Imminent pedestrian hazard outside school zone. Escalated to Chief Electrical Inspectorate & Sub-Divisional Officer.',
                'escalatedTo': 'Central Electrical Safety Cell'
            },
            'progressUpdates': [
                {
                    'status': 'Submitted',
                    'message': 'Emergency safety grievance registered.',
                    'officer': {'name': 'JanSahayata AI System', 'department': 'DISCOM', 'role': 'Triage'},
                    'timestamp': now - timedelta(hours=10)
                },
                {
                    'status': 'Escalated',
                    'message': 'Emergency gang isolated Feeder 3. Restringing of insulated conductor underway under Section 53 CEA rules.',
                    'officer': {'name': 'Allada Pavan', 'department': 'Electricity Board (DISCOM)', 'role': 'Divisional Engineer'},
                    'timestamp': now - timedelta(hours=2)
                }
            ],
            'createdAt': now - timedelta(hours=10),
            'updatedAt': now - timedelta(hours=2)
        },
        # --- 6. HEALTH & SANITATION (Under Review) ---
        {
            'complaintId': 'PHS-2026-000006',
            'citizenId': cid3,
            'citizenName': 'Amit Kumar Sharma',
            'citizenEmail': 'citizen.amit@gmail.com',
            'citizenPhone': '+91 97123 45679',
            'citizenDetails': {'name': 'Amit Kumar Sharma', 'email': 'citizen.amit@gmail.com', 'phone': '+91 97123 45679'},
            'description': 'Large stagnant water pool behind community hall breeding swarms of mosquitoes. Multiple dengue cases reported in surrounding blocks.',
            'generatedProblemStatement': 'Official Grievance Statement: Chronic stagnant water breeding ground for vector-borne diseases. Larvicide fogging and anti-dengue spray required.',
            'category': 'Mosquito Breeding / Stagnant Water',
            'department': {'id': 'health_sanitation', 'code': 'PHS', 'name': 'Public Health & Sanitation'},
            'urgency': 'High',
            'location': 'Behind Community Center, Block C, Urban Estate, Phagwara',
            'coordinates': {'lat': 31.2215, 'lng': 75.7810},
            'status': 'Under Review',
            'progressUpdates': [
                {
                    'status': 'Submitted',
                    'message': 'Grievance assigned to District Health Team.',
                    'officer': {'name': 'System', 'department': 'Public Health', 'role': 'Dispatcher'},
                    'timestamp': now - timedelta(hours=20)
                },
                {
                    'status': 'Under Review',
                    'message': 'Health Inspector deployed larvicidal spray schedule for Block C.',
                    'officer': {'name': 'Dr. Sunita Deshmukh', 'department': 'Public Health', 'role': 'District Health Officer'},
                    'timestamp': now - timedelta(hours=5)
                }
            ],
            'createdAt': now - timedelta(hours=20),
            'updatedAt': now - timedelta(hours=5)
        },
        # --- 7. EDUCATION (In Progress) ---
        {
            'complaintId': 'EDU-2026-000007',
            'citizenId': cid2,
            'citizenName': 'Pooja Verma',
            'citizenEmail': 'citizen.pooja@gmail.com',
            'citizenPhone': '+91 98123 45678',
            'citizenDetails': {'name': 'Pooja Verma', 'email': 'citizen.pooja@gmail.com', 'phone': '+91 98123 45678'},
            'description': 'Boundary wall of Govt Primary School collapsed during heavy rain. Stray cattle and dogs entering classrooms during study hours.',
            'generatedProblemStatement': 'Official Grievance Statement: Collapsed 15-meter boundary wall at Government Primary School. Student perimeter security compromised.',
            'category': 'School Building Damage',
            'department': {'id': 'education', 'code': 'EDU', 'name': 'Department of Education'},
            'urgency': 'High',
            'location': 'Government Primary School, Vill. Chheru, Phagwara, Punjab',
            'coordinates': {'lat': 31.2330, 'lng': 75.7650},
            'status': 'In Progress',
            'progressUpdates': [
                {
                    'status': 'Submitted',
                    'message': 'Ingested into Department of Education Infrastructure Cell.',
                    'officer': {'name': 'System', 'department': 'Education', 'role': 'Dispatcher'},
                    'timestamp': now - timedelta(days=2)
                },
                {
                    'status': 'In Progress',
                    'message': 'Civil tender estimate sanctioned by SSA engineer. Temporary tin barricades erected, bricklaying begins tomorrow.',
                    'officer': {'name': 'Ramesh Chandra Roy', 'department': 'Education', 'role': 'Block Education Officer'},
                    'timestamp': now - timedelta(hours=18)
                }
            ],
            'createdAt': now - timedelta(days=2),
            'updatedAt': now - timedelta(hours=18)
        },
        # --- 8. STATE PUBLIC TRANSPORT (Submitted) ---
        {
            'complaintId': 'TRN-2026-000008',
            'citizenId': cid1,
            'citizenName': 'Ravi Teja Sharma',
            'citizenEmail': 'citizen@gmail.com',
            'citizenPhone': '+91 98765 43210',
            'citizenDetails': {'name': 'Ravi Teja Sharma', 'email': 'citizen@gmail.com', 'phone': '+91 98765 43210'},
            'description': 'Main Bus Shelter on GT Road has rusted roof sheets collapsed. Commuters waiting in rain and sun. Real-time ETA LED display is completely dead.',
            'generatedProblemStatement': 'Official Grievance Statement: Structural deterioration of highway bus stop shelter and malfunctioning public passenger info display.',
            'category': 'Damaged Bus Shelter / Stand',
            'department': {'id': 'public_transport', 'code': 'TRN', 'name': 'State Public Transport'},
            'urgency': 'Medium',
            'location': 'Bus Stand Shelter No 4, National Highway 44, Phagwara',
            'coordinates': {'lat': 31.2200, 'lng': 75.7700},
            'status': 'Submitted',
            'progressUpdates': [
                {
                    'status': 'Submitted',
                    'message': 'Grievance lodged and routed to Roadways Depot Manager.',
                    'officer': {'name': 'JanSahayata AI System', 'department': 'State Transport', 'role': 'Ingestion'},
                    'timestamp': now - timedelta(hours=15)
                }
            ],
            'createdAt': now - timedelta(hours=15),
            'updatedAt': now - timedelta(hours=15)
        },
        # --- 9. RAILWAY (Resolved - Coach Air Conditioning) ---
        {
            'complaintId': 'RLY-2026-000009',
            'citizenId': cid3,
            'citizenName': 'Amit Kumar Sharma',
            'citizenEmail': 'citizen.amit@gmail.com',
            'citizenPhone': '+91 97123 45679',
            'citizenDetails': {'name': 'Amit Kumar Sharma', 'email': 'citizen.amit@gmail.com', 'phone': '+91 97123 45679'},
            'description': 'Train 12723 Telangana Express Coach B3 air conditioning tripped. Heavy suffocation with elderly passengers on board.',
            'generatedProblemStatement': 'Official Grievance Statement: Complete HVAC tripping in AC 3-Tier Coach B3. In-transit electrical staff attended and reset inverter unit.',
            'category': 'Coach Cleanliness & Bio-Toilet',
            'department': {'id': 'railway', 'code': 'RLY', 'name': 'Railway Department'},
            'urgency': 'Critical',
            'location': 'Telangana Express (12723) - Coach B3, Berths 21-45',
            'coordinates': {'lat': 18.7800, 'lng': 78.9000},
            'status': 'Resolved',
            'resolutionProof': {
                'officerNotes': 'Train Electrical Escort Staff attended at Ballarshah station. Blower fuse replaced, cooling restored to 23 degrees Celsius. Passenger signatures obtained.',
                'resolvedAt': now - timedelta(hours=16),
                'resolvedBy': 'K. Kiran Sai Karthik (Zonal Grievance Officer)'
            },
            'progressUpdates': [
                {
                    'status': 'Submitted',
                    'message': 'Critical passenger amenity grievance lodged via RailMadad sync.',
                    'officer': {'name': 'System', 'department': 'Railway', 'role': 'Dispatcher'},
                    'timestamp': now - timedelta(hours=22)
                },
                {
                    'status': 'Resolved',
                    'message': 'Escorting electrical engineer resolved HVAC inverter fault.',
                    'officer': {'name': 'K. Kiran Sai Karthik', 'department': 'Railway', 'role': 'Station Superintendent'},
                    'timestamp': now - timedelta(hours=16)
                }
            ],
            'createdAt': now - timedelta(hours=22),
            'updatedAt': now - timedelta(hours=16)
        },
        # --- 10. MUNICIPALITY (In Progress - Illegal Encroachment) ---
        {
            'complaintId': 'MUN-2026-000010',
            'citizenId': cid2,
            'citizenName': 'Pooja Verma',
            'citizenEmail': 'citizen.pooja@gmail.com',
            'citizenPhone': '+91 98123 45678',
            'citizenDetails': {'name': 'Pooja Verma', 'email': 'citizen.pooja@gmail.com', 'phone': '+91 98123 45678'},
            'description': 'Commercial shopkeepers erected unauthorized tin sheds on public pedestrian footpath, forcing school children to walk on busy vehicle road.',
            'generatedProblemStatement': 'Official Grievance Statement: Encroachment on pedestrian right-of-way by commercial entities along Main Bazaar Road.',
            'category': 'Illegal Encroachment',
            'department': {'id': 'municipality', 'code': 'MUN', 'name': 'Municipal Corporation'},
            'urgency': 'Medium',
            'location': 'Main Bazaar Road, Near Clock Tower, Phagwara',
            'coordinates': {'lat': 31.2220, 'lng': 75.7725},
            'status': 'In Progress',
            'progressUpdates': [
                {
                    'status': 'Submitted',
                    'message': 'Encroachment complaint logged.',
                    'officer': {'name': 'System', 'department': 'Municipal Corporation', 'role': 'Dispatcher'},
                    'timestamp': now - timedelta(days=1)
                },
                {
                    'status': 'In Progress',
                    'message': 'Show cause notice issued to shop owners under Section 172 Punjab Municipal Act.',
                    'officer': {'name': 'P. Balu Lakshman Pavan', 'department': 'Municipal Corporation', 'role': 'Enforcement Officer'},
                    'timestamp': now - timedelta(hours=7)
                }
            ],
            'createdAt': now - timedelta(days=1),
            'updatedAt': now - timedelta(hours=7)
        }
    ]
    complaints_col.insert_many(complaints)
    print(f"[Seed] Created {len(complaints)} Realistic Grievance Complaints across all departments.")

    # 5. System Audit Trail Logs
    audits = [
        {
            'action': 'SYSTEM_SEED',
            'performedBy': {'name': 'System Seeder', 'email': 'admin@jansahayata.gov.in', 'role': 'SYSTEM'},
            'targetType': 'System',
            'targetId': 'SYS-INIT-2026',
            'details': 'Initialized multi-department governance records, officer credentials, and sample citizen grievances.',
            'ipAddress': '127.0.0.1',
            'metadata': {'version': '2.0.0-django-sqlite'},
            'createdAt': now - timedelta(hours=48),
            'updatedAt': now - timedelta(hours=48)
        },
        {
            'action': 'OFFICER_PROVISION',
            'performedBy': {'name': 'Phaniswar', 'email': 'admin@jansahayata.gov.in', 'role': 'SUPER_ADMIN'},
            'targetType': 'Employee',
            'targetId': 'RLY-EMP-1001',
            'details': 'Provisioned jurisdictional credentials for Railway Officer K. Kiran Sai Karthik.',
            'ipAddress': '127.0.0.1',
            'metadata': {'department': 'Railway Department'},
            'createdAt': now - timedelta(hours=36),
            'updatedAt': now - timedelta(hours=36)
        },
        {
            'action': 'COMPLAINT_TRIAGE',
            'performedBy': {'name': 'JanSahayata AI Pipeline', 'email': 'ai-triage@jansahayata.gov.in', 'role': 'SYSTEM'},
            'targetType': 'Complaint',
            'targetId': 'ELE-2026-000005',
            'details': 'Automated LLM classification flagged 11kV conductor report as Critical Severity Hazard.',
            'ipAddress': '127.0.0.1',
            'metadata': {'confidence': 0.98},
            'createdAt': now - timedelta(hours=10),
            'updatedAt': now - timedelta(hours=10)
        },
        {
            'action': 'STATUS_CHANGE',
            'performedBy': {'name': 'P. Balu Lakshman Pavan', 'email': 'officer.muni@jansahayata.gov.in', 'role': 'EMPLOYEE'},
            'targetType': 'Complaint',
            'targetId': 'MUN-2026-000003',
            'details': 'Updated status to Resolved with hydraulic compaction proof photos attached.',
            'ipAddress': '127.0.0.1',
            'metadata': {'status': 'Resolved'},
            'createdAt': now - timedelta(hours=4),
            'updatedAt': now - timedelta(hours=4)
        },
        {
            'action': 'CITIZEN_DISPUTE',
            'performedBy': {'name': 'Amit Kumar Sharma', 'email': 'citizen.amit@gmail.com', 'role': 'CITIZEN'},
            'targetType': 'Complaint',
            'targetId': 'RDS-2026-000004',
            'details': 'Citizen rejected resolution: Flyover pothole gravel washed away in rainfall. Case reopened.',
            'ipAddress': '127.0.0.1',
            'metadata': {'status': 'Disputed'},
            'createdAt': now - timedelta(hours=8),
            'updatedAt': now - timedelta(hours=8)
        }
    ]
    audit_col.insert_many(audits)
    print(f"[Seed] Created {len(audits)} System Audit Logs.")

    print("\n=======================================================")
    print(" ✅ JanSahayata AI Database Seed Completed Successfully!")
    print("=======================================================")
    print(f" Super Admin: admin@jansahayata.gov.in / Admin@JanSahayata2026!")
    print(f" Railway Officer: officer.railway@jansahayata.gov.in / Officer@2026!")
    print(f" Municipal Officer: officer.muni@jansahayata.gov.in / Officer@2026!")
    print(f" Citizen 1: citizen@gmail.com / Citizen@2026!")
    print(f" Citizen 2: citizen.pooja@gmail.com / Citizen@2026!")
    print(f" Citizen 3: citizen.amit@gmail.com / Citizen@2026!")
    print("=======================================================\n")

if __name__ == '__main__':
    run_seed()
