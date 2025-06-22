from koneksi import get_db
import psycopg2
import psycopg2.extras
from psycopg2 import errors as pg_errors 
from werkzeug.security import generate_password_hash
import datetime

class Penyewaan:
    
    @staticmethod
    def get_all():
        """Mengambil semua data penyewaan dengan join ke tabel terkait"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = """
            SELECT 
                pe.id,
                pe.tanggal_mulai,
                pe.tanggal_selesai,
                pe.status,
                pe.metode,
                pe.jam_cod,
                pe.latitude,
                pe.longitude,
                pe.selfie_ktp,
                -- Data Produk
                p.id AS produk_id,
                p.nama_produk,
                p.warna,
                p.harga_sewa,
                p.keterangan AS produk_keterangan,
                p.img AS produk_img,
                p.status AS produk_status,
                -- Data Kelengkapan
                k.charger,
                k.casing,
                -- Data User
                u.id AS user_id,
                u.username,
                u.nama AS nama_user,
                u.email,
                u.no_telp,
                u.point,
                u.img_link_pp,
                u.status AS user_status,
                u.role
            FROM penyewaan pe
            JOIN produk p ON pe.produk_id = p.id
            LEFT JOIN kelengkapan k ON p.id = k.produk_id
            JOIN users u ON pe.user_id = u.id
            ORDER BY pe.id DESC;
        """
        
        cursor.execute(query)
        penyewaan_data = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in penyewaan_data]
    
    @staticmethod
    def get_by_id(penyewaan_id):
        """Mengambil data penyewaan berdasarkan ID dengan join ke tabel terkait"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = """
            SELECT 
                pe.id,
                pe.tanggal_mulai,
                pe.tanggal_selesai,
                pe.status,
                pe.metode,
                pe.jam_cod,
                pe.latitude,
                pe.longitude,
                pe.selfie_ktp,
                -- Data Produk
                p.id AS produk_id,
                p.nama_produk,
                p.warna,
                p.harga_sewa,
                p.keterangan AS produk_keterangan,
                p.img AS produk_img,
                p.status AS produk_status,
                -- Data Kelengkapan
                k.charger,
                k.casing,
                -- Data User
                u.id AS user_id,
                u.username,
                u.nama AS nama_user,
                u.email,
                u.no_telp,
                u.point,
                u.img_link_pp,
                u.status AS user_status,
                u.role
            FROM penyewaan pe
            JOIN produk p ON pe.produk_id = p.id
            LEFT JOIN kelengkapan k ON p.id = k.produk_id
            JOIN users u ON pe.user_id = u.id
            WHERE pe.id = %s;
        """
        
        cursor.execute(query, (penyewaan_id,))
        penyewaan_data = cursor.fetchone()
        cursor.close()
        
        if penyewaan_data:
            return dict(penyewaan_data)
        return None
    
    @staticmethod
    def search_by_user_name(nama_user):
        """Mencari penyewaan berdasarkan nama user"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = """
            SELECT 
                pe.id,
                pe.tanggal_mulai,
                pe.tanggal_selesai,
                pe.status,
                pe.metode,
                pe.jam_cod,
                pe.latitude,
                pe.longitude,
                pe.selfie_ktp,
                -- Data Produk
                p.id AS produk_id,
                p.nama_produk,
                p.warna,
                p.harga_sewa,
                p.keterangan AS produk_keterangan,
                p.img AS produk_img,
                p.status AS produk_status,
                -- Data Kelengkapan
                k.charger,
                k.casing,
                -- Data User
                u.id AS user_id,
                u.username,
                u.nama AS nama_user,
                u.email,
                u.no_telp,
                u.point,
                u.pp_img_link,
                u.status AS user_status,
                u.role
            FROM penyewaan pe
            JOIN produk p ON pe.produk_id = p.id
            LEFT JOIN kelengkapan k ON p.id = k.produk_id
            JOIN users u ON pe.user_id = u.id
            WHERE u.nama ILIKE %s OR u.username ILIKE %s
            ORDER BY pe.id DESC;
        """
        
        search_term = f"%{nama_user}%"
        cursor.execute(query, (search_term, search_term))
        penyewaan_data = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in penyewaan_data]
    
    @staticmethod
    def create(produk_id, user_id, tanggal_mulai, tanggal_selesai, metode, 
               jam_cod=None, latitude=None, longitude=None, selfie_ktp=None):
        """Membuat penyewaan baru"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            query = """
                INSERT INTO penyewaan (
                    produk_id, user_id, tanggal_mulai, tanggal_selesai, 
                    status, metode, jam_cod, latitude, longitude, selfie_ktp
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """
            
            cursor.execute(query, (
                produk_id,
                user_id,
                tanggal_mulai,
                tanggal_selesai,
                'menunggu_persetujuan',  # Status default
                metode,
                jam_cod,
                latitude,
                longitude,
                selfie_ktp
            ))
            
            new_penyewaan_id = cursor.fetchone()[0]
            conn.commit()
            
            # Kembalikan data lengkap penyewaan yang baru dibuat
            return Penyewaan.get_by_id(new_penyewaan_id)
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    @staticmethod
    def update(penyewaan_id, update_data):
        """Update data penyewaan"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Field yang bisa diupdate
            allowed_fields = [
                'produk_id', 'user_id', 'tanggal_mulai', 'tanggal_selesai', 
                'status', 'metode', 'jam_cod', 'latitude', 'longitude', 'selfie_ktp'
            ]
            
            update_fields = []
            update_values = []
            
            for field in allowed_fields:
                if field in update_data:
                    update_fields.append(f"{field} = %s")
                    update_values.append(update_data[field])
            
            if not update_fields:
                return Penyewaan.get_by_id(penyewaan_id)
            
            query = f"""
                UPDATE penyewaan 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id;
            """
            
            cursor.execute(query, (*update_values, penyewaan_id))
            conn.commit()
            
            # Kembalikan data lengkap yang sudah diupdate
            return Penyewaan.get_by_id(penyewaan_id)
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    @staticmethod
    def update_status(penyewaan_id, new_status):
        """Update status penyewaan"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Validasi status
            valid_statuses = ['menunggu_persetujuan', 'proses', 'dibatalkan', 'selesai']
            if new_status not in valid_statuses:
                raise ValueError(f"Status tidak valid. Status yang valid: {valid_statuses}")
            
            query = """
                UPDATE penyewaan 
                SET status = %s
                WHERE id = %s
                RETURNING id;
            """
            
            cursor.execute(query, (new_status, penyewaan_id))
            
            if cursor.rowcount == 0:
                raise ValueError(f"Penyewaan dengan ID {penyewaan_id} tidak ditemukan")
            
            conn.commit()
            
            # Kembalikan data lengkap yang sudah diupdate
            return Penyewaan.get_by_id(penyewaan_id)
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    @staticmethod
    def get_by_status(status):
        """Mengambil penyewaan berdasarkan status"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = """
            SELECT 
                pe.id,
                pe.tanggal_mulai,
                pe.tanggal_selesai,
                pe.status,
                pe.metode,
                pe.jam_cod,
                pe.latitude,
                pe.longitude,
                pe.selfie_ktp,
                -- Data Produk
                p.id AS produk_id,
                p.nama_produk,
                p.warna,
                p.harga_sewa,
                p.keterangan AS produk_keterangan,
                p.img AS produk_img,
                p.status AS produk_status,
                -- Data Kelengkapan
                k.charger,
                k.casing,
                -- Data User
                u.id AS user_id,
                u.username,
                u.nama AS nama_user,
                u.email,
                u.no_telp,
                u.point,
                u.img_link_pp,
                u.status AS user_status,
                u.role
            FROM penyewaan pe
            JOIN produk p ON pe.produk_id = p.id
            LEFT JOIN kelengkapan k ON p.id = k.produk_id
            JOIN users u ON pe.user_id = u.id
            WHERE pe.status = %s
            ORDER BY pe.id DESC;
        """
        
        cursor.execute(query, (status,))
        penyewaan_data = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in penyewaan_data]
    
    @staticmethod
    def get_by_user_id(user_id):
        """Mengambil semua penyewaan berdasarkan user ID"""
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = """
            SELECT 
                pe.id,
                pe.tanggal_mulai,
                pe.tanggal_selesai,
                pe.status,
                pe.metode,
                pe.jam_cod,
                pe.latitude,
                pe.longitude,
                pe.selfie_ktp,
                -- Data Produk
                p.id AS produk_id,
                p.nama_produk,
                p.warna,
                p.harga_sewa,
                p.keterangan AS produk_keterangan,
                p.img AS produk_img,
                p.status AS produk_status,
                -- Data Kelengkapan
                k.charger,
                k.casing,
                -- Data User
                u.id AS user_id,
                u.username,
                u.nama AS nama_user,
                u.email,
                u.no_telp,
                u.point,
                u.img_link_pp,
                u.status AS user_status,
                u.role
            FROM penyewaan pe
            JOIN produk p ON pe.produk_id = p.id
            LEFT JOIN kelengkapan k ON p.id = k.produk_id
            JOIN users u ON pe.user_id = u.id
            WHERE pe.user_id = %s
            ORDER BY pe.id DESC;
        """
        
        cursor.execute(query, (user_id,))
        penyewaan_data = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in penyewaan_data]
    
    @staticmethod
    def delete(penyewaan_id):
        """Menghapus penyewaan berdasarkan ID"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            query = "DELETE FROM penyewaan WHERE id = %s RETURNING id;"
            cursor.execute(query, (penyewaan_id,))
            
            if cursor.rowcount == 0:
                raise ValueError(f"Penyewaan dengan ID {penyewaan_id} tidak ditemukan")
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()