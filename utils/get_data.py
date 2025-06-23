import mysql.connector
from mysql.connector import pooling
import json
import os
from dotenv import load_dotenv
import re # <-- 1. IMPORT PUSTAKA 're'

load_dotenv()

# ... (kode setup pool koneksi Anda sudah benar) ...
# Setup Connection Pool
dbconfig = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "auth_plugin": 'mysql_native_password'
}
pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **dbconfig)


def get_candidate_data_json(skills_list):
    # 2. TAMBAHKAN PENGECEKAN UNTUK LIST KOSONG
    if not skills_list:
        # Jika tidak ada skill yang dicari, kembalikan list kosong
        return json.dumps([], indent=2) 
        
    conn = None
    cursor = None

    try:
        conn = pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 3. PERBAIKAN: ESCAPE SETIAP SKILL SEBELUM DIGABUNGKAN
        # Ini akan mengubah 'C++' menjadi 'C\+\+' secara otomatis
        escaped_skills = [re.escape(s) for s in skills_list]
        regex_pattern = '|'.join(escaped_skills)
        final_regex_param = f'(^|,| )({regex_pattern})($|,| )'
        
        query = """SELECT 
                    u.id AS user_id, u.name AS user_name, u.email,
                    cpd.id AS profile_id, cpd.first_name, cpd.last_name, cpd.phone_number,
                    cpd.about, cpd.country, cpd.city, cpd.linkedin_profile, cpd.skills,
                    ced.institution_name, ced.degree, ced.field_of_study, 
                    ced.start_year AS edu_start_year, ced.end_year AS edu_end_year, ced.gpa,
                    cwe.company_name, cwe.position, cwe.start_date AS work_start_date, 
                    cwe.end_date AS work_end_date
                FROM User u
                LEFT JOIN CandidateProfileDetail cpd ON u.id = cpd.user_id
                LEFT JOIN CandidateEducationDetail ced ON cpd.id = ced.profile_id
                LEFT JOIN CandidateWorkExperienceDetail cwe ON cpd.id = cwe.profile_id
                WHERE u.role = 'Candidate' AND cpd.skills REGEXP %s
                LIMIT 50;"""
        print(query)
        cursor.execute(query, (final_regex_param,))
        
        flat_results = cursor.fetchall()

        # **BAGIAN AGREGRASI DI PYTHON (Kode Anda sudah benar)**
        candidates_aggregated = {}
        for row in flat_results:
            user_id = row['user_id']
            if user_id not in candidates_aggregated:
                candidates_aggregated[user_id] = {
                    "user_id": user_id,
                    "user_name": row['user_name'],
                    "email": row['email'],
                    "profile": {
                        "id": row['profile_id'], "first_name": row['first_name'],
                        "last_name": row['last_name'], "phone_number": row['phone_number'],
                        "about": row['about'], "country": row['country'], "city": row['city'],
                        "linkedin_profile": row['linkedin_profile'], "skills": row['skills'],
                    },
                    "education": [], "work_experience": []
                }
            
            edu_entry = {
                "institution_name": row['institution_name'], "degree": row['degree'],
                "field_of_study": row['field_of_study'], "start_year": row['edu_start_year'],
                "end_year": row['edu_end_year'], "gpa": row['gpa']
            }
            if edu_entry not in candidates_aggregated[user_id]['education'] and edu_entry['institution_name'] is not None:
                candidates_aggregated[user_id]['education'].append(edu_entry)

            work_entry = {
                "company_name": row['company_name'], "job_title": row['position'], # Menggunakan 'position' dari query
                "start_date": row['work_start_date'], "end_date": row['work_end_date']
            }
            if work_entry not in candidates_aggregated[user_id]['work_experience'] and work_entry['company_name'] is not None:
                candidates_aggregated[user_id]['work_experience'].append(work_entry)

        final_results = list(candidates_aggregated.values())
        return json.dumps(final_results, default=str, indent=2)

    except mysql.connector.Error as err:
        return json.dumps({"error": str(err)}, indent=2)

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Test run untuk versi agregasi
if __name__ == "__main__":
    # Sekarang aman untuk menggunakan skill dengan karakter khusus
    skills_to_find = ["C++", "Node.js", "Python"]
    data_json = get_candidate_data_json(skills_to_find) 
    print(len(data_json))

    # Test dengan list kosong
    print("\n--- Testing dengan list kosong ---")
    data_json_empty = get_candidate_data_json([])
    print(data_json_empty)