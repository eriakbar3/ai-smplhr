import mysql.connector
from mysql.connector import pooling
import json
import os

# Setup Connection Pool
dbconfig = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "auth_plugin": 'mysql_native_password'
}

pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    **dbconfig
)

def get_candidate_data_json():
    try:
        conn = pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT 
  u.id AS user_id,
  u.name AS user_name,
  u.email,
  cpd.id AS profile_id,
  cpd.first_name,
  cpd.last_name,
  cpd.phone_number,
  cpd.about,
  cpd.country,
  cpd.city,
  cpd.linkedin_profile,
  cpd.skills,
  cpd.cv_score,
  cpd.cv_feedback,
  cpd.cv_filename,
  cpd.expected_fulltime_salary,
  cpd.expected_parttime_salary,
  cpd.currency_salary,
  cpd.week_notice_fulltime,
  cpd.week_notice_parttime,
  cpd.work_schedule,
  cpd.work_available,
  cpd.is_asap_join,
  cpd.is_complete_profile,

  ced.id AS education_id,
  ced.institution_name,
  ced.degree,
  ced.field_of_study,
  ced.start_year AS edu_start_year,
  ced.end_year AS edu_end_year,
  ced.gpa,

  cwe.id AS work_id,
  cwe.company_name,
  cwe.position,
  cwe.location,
  cwe.start_date AS work_start_date,
  cwe.end_date AS work_end_date,
  cwe.description AS work_description

FROM User u
LEFT JOIN CandidateProfileDetail cpd ON u.id = cpd.user_id
LEFT JOIN CandidateEducationDetail ced ON cpd.id = ced.profile_id
LEFT JOIN CandidateWorkExperienceDetail cwe ON cpd.id = cwe.profile_id
WHERE u.role = 'Candidate';
        """

        cursor.execute(query)
        results = cursor.fetchall()

        return json.dumps(results, default=str, indent=2)

    except mysql.connector.Error as err:
        return json.dumps({"error": str(err)})

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

# Test run
if __name__ == "__main__":
    data_json = get_candidate_data_json()
    print(data_json)
