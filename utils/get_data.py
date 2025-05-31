import mysql.connector
import json

def get_candidate_data_json(
    host='34.57.189.211',
    user='remote_user',
    password='RemoteUser$2024',
    database='db_smplhr'
):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            auth_plugin='mysql_native_password'
        )

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
          ccd.id AS certification_id,
          ccd.name AS certification_name,
          ccd.training_by,
          ccd.credential,
          ccd.completed_on,
          cpj.id AS project_id,
          cpj.name AS project_name,
          cpj.link AS project_link,
          cpj.start_year,
          cpj.end_year,
          cpj.status AS project_status,
          cpj.source AS project_source,
          cpj.details AS project_details
        FROM User u
        LEFT JOIN CandidateProfileDetail cpd ON u.id = cpd.user_id
        LEFT JOIN CandidateCertificationDetail ccd ON cpd.id = ccd.profile_id
        LEFT JOIN CandidateProjectDetail cpj ON cpd.id = cpj.profile_id
        WHERE u.role = 'Candidate';
        """

        cursor.execute(query)
        results = cursor.fetchall()

        # Convert ke JSON
        return json.dumps(results, default=str, indent=2)

    except mysql.connector.Error as err:
        return json.dumps({"error": str(err)})

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

# Contoh pemanggilan fungsi
if __name__ == "__main__":
    data_json = get_candidate_data_json()
    print(data_json)
