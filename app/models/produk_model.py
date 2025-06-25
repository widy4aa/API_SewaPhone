from koneksi import get_db
import psycopg2
import psycopg2.extras
from psycopg2 import errors as pg_errors 
from werkzeug.security import generate_password_hash
import datetime

class Produk:
    # ... your class definition ...
    @staticmethod
    def get_all():
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = 'SELECT * FROM produk order by id;'
        cursor.execute(query)
        
        users_data = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in users_data]
    
    @staticmethod
    def get_popular():
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = """
             SELECT
                p.nama_produk,
                p.warna,
                p.harga_sewa,
                p.keterangan,
                p.img,
                COUNT(r.produk_id) AS total_penyewaan 
            FROM
                produk AS p
            JOIN
                penyewaan AS r ON p.id = r.produk_id
            WHERE
                p.status = 'active' -- Hanya tampilkan iPhone yang statusnya aktif (tersedia)
                AND p.nama_produk LIKE 'iPhone%' -- Memastikan hanya menampilkan produk iPhone
                AND r.status = 'selesai' -- Filter hanya penyewaan yang sudah selesai/berhasil dikembalikan
                AND r.tanggal_selesai <= CURRENT_DATE -- Pastikan tanggal selesai sewa adalah atau sebelum hari ini
                -- Opsi tambahan: untuk popularitas dalam periode waktu tertentu
                -- AND r.tanggal_mulai >= CURRENT_DATE - INTERVAL '3 months' -- Contoh: Hanya penyewaan 3 bulan terakhir
            GROUP BY
                p.id, p.nama_produk, p.warna, p.harga_sewa, p.keterangan, p.img
            ORDER BY
                total_penyewaan DESC, -- Urutkan berdasarkan jumlah penyewaan terbanyak (paling populer)
                p.nama_produk ASC      -- Jika jumlah penyewaan sama, urutkan berdasarkan nama produk (alfabetis)
            LIMIT 5;                   -- Tampilkan 5 iPhone terpopuler teratas
        """
        cursor.execute(query)
        
        users_data = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in users_data]
    
    @staticmethod
    def get_rekomendasi():
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = """
                    SELECT
                        p.id,
                        p.nama_produk,
                        p.warna,
                        p.harga_sewa,
                        p.keterangan,
                        p.img,
                        -- Hitung jumlah penyewaan yang statusnya 'selesai'. Jika belum pernah disewa, hasilnya 0.
                        COUNT(r.produk_id) AS total_penyewaan 
                    FROM
                        produk AS p
                    LEFT JOIN
                        -- Gabungkan dengan penyewaan yang sudah selesai untuk menghitung popularitas
                        penyewaan AS r ON p.id = r.produk_id AND r.status = 'selesai'
                    WHERE
                        -- Filter utama: Hanya iPhone yang aktif
                        p.status = 'active'
                        AND p.nama_produk LIKE 'iPhone%'
                    GROUP BY
                        -- Kelompokkan berdasarkan setiap produk unik
                        p.id, p.nama_produk, p.warna, p.harga_sewa, p.keterangan, p.img
                    ORDER BY
                        -- Urutkan pertama berdasarkan popularitas (paling banyak disewa)
                        total_penyewaan DESC,
                        -- Jika popularitas sama, urutkan berdasarkan harga (paling murah)
                        p.harga_sewa ASC
                    LIMIT 5; -- Ambil 5 produk teratas
        """
        cursor.execute(query)
        
        users_data = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in users_data]
    
    @staticmethod
    def get_by_id(product_id):
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        product_query = '''
            SELECT 
                p.*,
                k.charger,
                k.casing
            FROM produk p
            LEFT JOIN kelengkapan k ON p.id = k.produk_id
            WHERE p.id = %s;
        '''
        cursor.execute(product_query, (product_id,))
        product_data = cursor.fetchone()

        if not product_data:
            cursor.close()
            return None

        schedule_query = '''
            SELECT 
                TO_CHAR(tanggal_mulai, 'YYYY-MM-DD') AS tanggal_mulai,
                TO_CHAR(tanggal_selesai, 'YYYY-MM-DD') AS tanggal_selesai,
                status
            FROM penyewaan
            WHERE produk_id = %s
            ORDER BY tanggal_mulai;
        '''
        cursor.execute(schedule_query, (product_id,))
        schedules = cursor.fetchall()

        cursor.close()

        result = dict(product_data)
        result['jadwal_sewa'] = [dict(schedule) for schedule in schedules]

        return result
     
    @staticmethod   
    def create_produk(nama_produk, warna, harga_sewa, keterangan, img_path, 
                     charger=True, casing=True, status='active'):
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Insert produk utama
            produk_query = """
                INSERT INTO produk (nama_produk, warna, harga_sewa, status_sewa, keterangan, img, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """
            cursor.execute(produk_query, (
                nama_produk,
                warna,
                harga_sewa,
                False, 
                keterangan,
                img_path,
                status
            ))
            
            new_product_id = cursor.fetchone()[0]
            
            kelengkapan_query = """
                INSERT INTO kelengkapan (produk_id, charger, casing)
                VALUES (%s, %s, %s);
            """
            cursor.execute(kelengkapan_query, (
                new_product_id,
                charger,
                casing
            ))
            
            conn.commit()
            return new_product_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            
    @staticmethod
    def update(produk_id, update_data):
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # Gunakan DictCursor

        try:
            produk_fields = []
            produk_values = []

            for field in ['nama_produk', 'warna', 'harga_sewa', 'keterangan', 'img', 'status']:
                if field in update_data:
                    produk_fields.append(f"{field} = %s")
                    produk_values.append(update_data[field])

            if produk_fields:
                produk_query = f"""
                    UPDATE produk 
                    SET {', '.join(produk_fields)} 
                    WHERE id = %s
                    RETURNING *;
                """
                cursor.execute(produk_query, (*produk_values, produk_id))
                updated_product = dict(cursor.fetchone())  
            else:
                cursor.execute("SELECT * FROM produk WHERE id = %s", (produk_id,))
                updated_product = dict(cursor.fetchone())

            updated_kelengkapan = {}
            if 'kelengkapan' in update_data:
                kelengkapan_data = update_data['kelengkapan']
                kelengkapan_fields = []
                kelengkapan_values = []

                for field in ['charger', 'casing']:
                    if field in kelengkapan_data:
                        kelengkapan_fields.append(f"{field} = %s")
                        kelengkapan_values.append(kelengkapan_data[field])

                if kelengkapan_fields:
                    kelengkapan_query = f"""
                        UPDATE kelengkapan 
                        SET {', '.join(kelengkapan_fields)} 
                        WHERE produk_id = %s
                        RETURNING *;
                    """
                    cursor.execute(kelengkapan_query, (*kelengkapan_values, produk_id))
                    updated_kelengkapan = dict(cursor.fetchone())

            conn.commit()
            return updated_product, updated_kelengkapan

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            
            
