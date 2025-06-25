from koneksi import get_db
import psycopg2
import psycopg2.extras
from psycopg2.extras import DictCursor 
from psycopg2 import errors as pg_errors 
from werkzeug.security import generate_password_hash
import datetime

class User:
    @staticmethod
    def get_all():
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = 'SELECT * FROM users order by id;'
        cursor.execute(query)
        
        users_data = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in users_data]

    @staticmethod
    def get_by_id(user_id):
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = 'SELECT * FROM users WHERE id = %s;'
        cursor.execute(query, (user_id,))
        
        user_data = cursor.fetchone()
        cursor.close()
        
        if user_data is None:
            return None
            
        return dict(user_data)

    @staticmethod
    def create(data):
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        hashed_password = generate_password_hash(data['pass'],method='pbkdf2:sha256')

        query = """
            INSERT INTO users (
                username, pass, nama, email, no_telp, point, status, role
            ) VALUES (%s, %s, %s, %s, %s, '50', 'inactive', 'user')
            RETURNING *;
        """

        user_values = ( 
            data['username'],
            hashed_password,
            data.get('nama'),
            data.get('email'),
            data.get('no_telp'),
        )

        try:
             cursor.execute(query, user_values)
             new_user = cursor.fetchone()
             conn.commit()
             cursor.close()
             return {"success": True, "message": "Pendaftaran berhasil!", "user": dict(new_user)}, 201
         
        except pg_errors.UniqueViolation as e:
             conn.rollback() 
             cursor.close()
             if "unique_username" in str(e).lower():
                 return {"success": False, "error": "Username sudah terdaftar. Silakan gunakan username lain."}, 409
             else:
                 return {"success": False, "error": f"Terjadi konflik data duplikat: {str(e)}"}, 409
        except Exception as e:
             conn.rollback() 
             cursor.close()
             print(f"Terjadi kesalahan tak terduga saat membuat user: {e}") 
             return {"success": False, "error": "Terjadi kesalahan internal server. Silakan coba lagi nanti."}, 500
        finally:
             if cursor and not cursor.closed:
                 cursor.close()
             if conn and not conn.closed:
                 conn.close()


    @staticmethod
    def get_by_username(username):
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = """SELECT * FROM users WHERE username = %s;"""
        cursor.execute(query, (username,))
        
        user_data = cursor.fetchone()
        cursor.close()
        
        if user_data:
            return dict(user_data)
        
        return None
    
    @staticmethod
    def me(jwt_identity):
        user_id = jwt_identity
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, nama, no_telp, point, status, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return user


    @staticmethod
    def verify_registration_otp(username, otp_code):
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # user_query = "SELECT id, status FROM users WHERE username = %s"
        # cursor.execute(user_query, (username,))
        # user = cursor.fetchone()
        # if not user:
        #     return {"success": False, "error": "Akun tidak ditemukan."}, 404
        # if user['status'] == 'active':
        #     return {"success": False, "error": "Akun ini sudah aktif. Silakan login."}, 400
        try:
            user_query = "SELECT id, status FROM users WHERE username = %s"
            cursor.execute(user_query, (username,))
            user = cursor.fetchone()
            if not user:
                 return {"success": False, "error": "Akun tidak ditemukan."}, 404

            if user['status'] == 'active':
                 return {"success": False, "error": "Akun ini sudah aktif. Silakan login."}, 400

            user_id = user['id']
            
            otp_query = """
                select * from otp where user_id =%s order by id DESC LIMIT 1;
            """
            cursor.execute(otp_query, (user_id,))
            otp_record = cursor.fetchone()

            if not otp_record:
                 return {"success": False, "error": "Tidak ada OTP yang valid untuk akun ini. Silakan minta OTP baru."}, 400
            if otp_record['otp'] != otp_code:
                 return {"success": False, "error": "Kode OTP salah. Silakan coba lagi."}, 400
            update_user_status_query = """
                 UPDATE users
                 SET status = 'active'
                 WHERE id = %s 
                 RETURNING id AS user_id, username, email, nama, role; 
             """
            cursor.execute(update_user_status_query, (user_id,))
            activated_user = cursor.fetchone()
            delete_otp_query = "DELETE FROM otp WHERE id = %s;"
            cursor.execute(delete_otp_query, (otp_record['id'],))
            conn.commit() 
            cursor.close()
            return {
                "success": True,
                "message": "Akun Anda berhasil diaktifkan! Silakan login.",
                "user": dict(activated_user),
            }, 200

        except Exception as e:
            conn.rollback()
            cursor.close()
            print(f"Error verifying registration OTP: {e}") 
            return {"success": False, "error": "Terjadi kesalahan internal server. Silakan coba lagi nanti."}, 500
        finally:
            if cursor and not cursor.closed:
                cursor.close()
            if conn and not conn.closed:
                conn.close()
                
    @staticmethod
    def edit(user_id, data):
        conn = None
        cursor = None
        editable_fields = ['username', 'nama', 'email', 'no_telp', 'point']
        update_clauses = []
        query_values = []

        for field in editable_fields:
            if field in data and data[field] is not None:
                update_clauses.append(f"{field} = %s")
                query_values.append(data[field])

        if 'pass' in data and data['pass']:
            hashed_password = generate_password_hash(data['pass'], method='pbkdf2:sha256')
            update_clauses.append("pass = %s")
            query_values.append(hashed_password)
            
        if not update_clauses:
            return {"success": False, "error": "Tidak ada data untuk diperbarui."}, 400

        query_values.append(user_id)

        query = f"""
            UPDATE users
            SET {', '.join(update_clauses)}
            WHERE id = %s
            RETURNING *;
        """

        try:
            conn = get_db()
            cursor = conn.cursor(cursor_factory=DictCursor)
            
            cursor.execute(query, tuple(query_values))
            updated_user = cursor.fetchone()

            if not updated_user:
                conn.rollback()
                return {"success": False, "error": "User dengan ID tersebut tidak ditemukan."}, 404

            conn.commit()
            return {"success": True, "message": "Data user berhasil diperbarui.", "user": dict(updated_user)}, 200

        except pg_errors.UniqueViolation as e:
            conn.rollback()
            error_message = "Terjadi konflik data duplikat."
            if "unique_username" in str(e).lower():
                error_message = "Username sudah terdaftar. Silakan gunakan username lain."
            elif "unique_email" in str(e).lower(): 
                error_message = "Email sudah terdaftar. Silakan gunakan email lain."
            return {"success": False, "error": error_message}, 409
        
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Terjadi kesalahan tak terduga saat mengedit user: {e}")
            return {"success": False, "error": "Terjadi kesalahan internal server. Silakan coba lagi nanti."}, 500
        
        finally:
            if cursor and not cursor.closed:
                cursor.close()
            if conn and not conn.closed:
                conn.close()

    @staticmethod
    def get_profile_picture(user_id):
        conn = get_db()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            query = "SELECT pp_img_link FROM users WHERE id = %s;"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            if result:
                return {"success": True, "data": result}, 200
            else:
                return {"success": False, "error": "User tidak ditemukan."}, 404
        except Exception as e:
            print(f"Error getting profile picture: {e}")
            return {"success": False, "error": "Internal server error"}, 500
        finally:
            if cursor and not cursor.closed:
                cursor.close()
            if conn and not conn.closed:
                conn.close()
                
    @staticmethod
    def update_profile_picture(user_id, pp_img_link):
        """
        Memperbarui link gambar profil (pp_link_img) untuk user tertentu.
        """
        conn = get_db()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            query = """
                UPDATE users
                SET pp_img_link = %s
                WHERE id = %s
                RETURNING id, username, pp_img_link;
            """
            print(query)
            cursor.execute(query, (pp_img_link, user_id))
            updated_user = cursor.fetchone()
            
            if not updated_user:
                conn.rollback()
                return {"success": False, "error": "User dengan ID tersebut tidak ditemukan."}, 404

            conn.commit()
            return {"success": True, "message": "Foto profil berhasil diperbarui.", "user": dict(updated_user)}, 200
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Terjadi kesalahan tak terduga saat memperbarui foto profil: {e}")
            return {"success": False, "error": "Terjadi kesalahan internal server. Silakan coba lagi nanti."}, 500
        finally:
            if cursor and not cursor.closed:
                cursor.close()
            if conn and not conn.closed:
                conn.close()


    @staticmethod
    def edit_point_only(user_id, new_point):
        conn = get_db()
        cursor = conn.cursor(cursor_factory=DictCursor)

        try:
            cursor.execute("""
                UPDATE users
                SET point = %s
                WHERE id = %s
                RETURNING id, username, point;
            """, (new_point, user_id))

            updated_user = cursor.fetchone()

            if not updated_user:
                conn.rollback()
                return {"success": False, "error": "User dengan ID tersebut tidak ditemukan."}, 404

            conn.commit()
            return {"success": True, "message": "Point user berhasil diperbarui.", "user": dict(updated_user)}, 200

        except Exception as e:
            conn.rollback()
            print(f"Terjadi kesalahan saat memperbarui point user: {e}")
            return {"success": False, "error": "Terjadi kesalahan internal server. Silakan coba lagi nanti."}, 500

        finally:
            cursor.close()
            conn.close()


