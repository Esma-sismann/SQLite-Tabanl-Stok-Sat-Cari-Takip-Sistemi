"""
MiniERP - Veritabanı Yönetim Modülü
Tüm SQLite bağlantı, sorgu ve tablo kurulum işlemleri bu dosyada.
"""

import sqlite3
import hashlib
import os


class Veritabani:
    """SQLite veritabanı bağlantısını ve temel sorgu işlemlerini yönetir."""

    def __init__(self, db_yolu: str):
        self.db_yolu = db_yolu
        os.makedirs(os.path.dirname(db_yolu), exist_ok=True)

    def baglan(self) -> sqlite3.Connection:
        """Yeni bir bağlantı döndürür. Foreign key desteğini aktif eder."""
        baglanti = sqlite3.connect(self.db_yolu)
        baglanti.execute("PRAGMA foreign_keys = ON")
        baglanti.row_factory = sqlite3.Row  # sütun adıyla erişim: kayit['ad']
        return baglanti

    def sorgu_calistir(self, sorgu: str, parametreler: tuple = None) -> bool:
        """
        INSERT / UPDATE / DELETE sorgularını çalıştırır.
        Başarılı ise True, hata varsa False döner.
        """
        try:
            with self.baglan() as baglanti:
                imleç = baglanti.cursor()
                if parametreler:
                    imleç.execute(sorgu, parametreler)
                else:
                    imleç.execute(sorgu)
                baglanti.commit()
                return True
        except sqlite3.IntegrityError as hata:
            print(f"[HATA] Bütünlük hatası: {hata}")
            return False
        except sqlite3.Error as hata:
            print(f"[HATA] Veritabanı hatası: {hata}")
            return False

    def son_eklenen_id(self, sorgu: str, parametreler: tuple = None):
        """INSERT sonrası oluşan id'yi döndürür."""
        try:
            with self.baglan() as baglanti:
                imleç = baglanti.cursor()
                if parametreler:
                    imleç.execute(sorgu, parametreler)
                else:
                    imleç.execute(sorgu)
                baglanti.commit()
                return imleç.lastrowid
        except sqlite3.Error as hata:
            print(f"[HATA] Veritabanı hatası: {hata}")
            return None

    def tek_kayit_getir(self, sorgu: str, parametreler: tuple = None):
        """Tek satır döndüren SELECT sorgularında kullanılır."""
        try:
            with self.baglan() as baglanti:
                imleç = baglanti.cursor()
                if parametreler:
                    imleç.execute(sorgu, parametreler)
                else:
                    imleç.execute(sorgu)
                return imleç.fetchone()
        except sqlite3.Error as hata:
            print(f"[HATA] Veritabanı hatası: {hata}")
            return None

    def tum_kayitlari_getir(self, sorgu: str, parametreler: tuple = None) -> list:
        """Birden fazla satır döndüren SELECT sorgularında kullanılır."""
        try:
            with self.baglan() as baglanti:
                imleç = baglanti.cursor()
                if parametreler:
                    imleç.execute(sorgu, parametreler)
                else:
                    imleç.execute(sorgu)
                return imleç.fetchall()
        except sqlite3.Error as hata:
            print(f"[HATA] Veritabanı hatası: {hata}")
            return []

    def transaction_calistir(self, islemler: list) -> bool:
        """
        Birden fazla sorguyu tek transaction içinde çalıştırır.
        islemler: [(sorgu, parametreler), ...] formatında liste.
        Herhangi biri başarısız olursa tüm işlem geri alınır (ROLLBACK).
        """
        baglanti = self.baglan()
        try:
            imleç = baglanti.cursor()
            imleç.execute("BEGIN")
            for sorgu, parametreler in islemler:
                if parametreler:
                    imleç.execute(sorgu, parametreler)
                else:
                    imleç.execute(sorgu)
            baglanti.commit()
            return True
        except sqlite3.Error as hata:
            baglanti.rollback()
            print(f"[HATA] Transaction başarısız, geri alındı: {hata}")
            return False
        finally:
            baglanti.close()


# ─────────────────────────────────────────────────────
#  Tablo Tanımları
# ─────────────────────────────────────────────────────

TABLOLAR = [
    # Kullanıcılar (giriş sistemi)
    """
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_adi   TEXT UNIQUE NOT NULL,
        sifre           TEXT NOT NULL,
        rol             TEXT NOT NULL CHECK(rol IN ('admin', 'personel', 'muhasebe')),
        aktif           INTEGER DEFAULT 1
    )
    """,
    # Ürünler
    """
    CREATE TABLE IF NOT EXISTS urunler (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        ad                  TEXT NOT NULL,
        kategori            TEXT NOT NULL,
        alis_fiyati         REAL NOT NULL CHECK(alis_fiyati >= 0),
        satis_fiyati        REAL NOT NULL CHECK(satis_fiyati >= 0),
        stok                INTEGER NOT NULL DEFAULT 0,
        kritik_stok         INTEGER NOT NULL DEFAULT 5,
        aktif               INTEGER DEFAULT 1,
        olusturulma_tarihi  TEXT NOT NULL
    )
    """,
    # Müşteriler
    """
    CREATE TABLE IF NOT EXISTS musteriler (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        ad_soyad        TEXT NOT NULL,
        telefon         TEXT,
        email           TEXT,
        adres           TEXT,
        borc_bakiyesi   REAL DEFAULT 0,
        kayit_tarihi    TEXT NOT NULL
    )
    """,
    # Tedarikçiler
    """
    CREATE TABLE IF NOT EXISTS tedarikciler (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        firma_adi   TEXT NOT NULL,
        yetkili_adi TEXT,
        telefon     TEXT,
        email       TEXT,
        adres       TEXT
    )
    """,
    # Satışlar (başlık)
    """
    CREATE TABLE IF NOT EXISTS satislar (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        musteri_id      INTEGER,
        kullanici_id    INTEGER NOT NULL,
        toplam_tutar    REAL NOT NULL,
        odenen_tutar    REAL NOT NULL DEFAULT 0,
        odeme_turu      TEXT NOT NULL CHECK(odeme_turu IN ('nakit', 'kart', 'veresiye', 'karma')),
        satis_tarihi    TEXT NOT NULL,
        iptal           INTEGER DEFAULT 0,
        FOREIGN KEY (musteri_id)   REFERENCES musteriler(id),
        FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id)
    )
    """,
    # Satış kalemleri (detay)
    """
    CREATE TABLE IF NOT EXISTS satis_kalemleri (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        satis_id        INTEGER NOT NULL,
        urun_id         INTEGER NOT NULL,
        miktar          INTEGER NOT NULL CHECK(miktar > 0),
        birim_fiyat     REAL NOT NULL,
        toplam_fiyat    REAL NOT NULL,
        FOREIGN KEY (satis_id) REFERENCES satislar(id),
        FOREIGN KEY (urun_id)  REFERENCES urunler(id)
    )
    """,
    # Stok hareketleri
    """
    CREATE TABLE IF NOT EXISTS stok_hareketleri (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        urun_id         INTEGER NOT NULL,
        hareket_turu    TEXT NOT NULL CHECK(hareket_turu IN
                            ('stok_giris','stok_cikis','satis','iade','duzeltme')),
        miktar          INTEGER NOT NULL,
        aciklama        TEXT,
        hareket_tarihi  TEXT NOT NULL,
        FOREIGN KEY (urun_id) REFERENCES urunler(id)
    )
    """,
    # Cari hareketler (veresiye / ödeme takibi)
    """
    CREATE TABLE IF NOT EXISTS cari_hareketler (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        musteri_id      INTEGER NOT NULL,
        islem_turu      TEXT NOT NULL CHECK(islem_turu IN
                            ('borclandirma','odeme','iade','duzeltme')),
        tutar           REAL NOT NULL,
        aciklama        TEXT,
        islem_tarihi    TEXT NOT NULL,
        FOREIGN KEY (musteri_id) REFERENCES musteriler(id)
    )
    """,
]


# ─────────────────────────────────────────────────────
#  Yardımcı Fonksiyonlar
# ─────────────────────────────────────────────────────

def sifre_hashle(sifre: str) -> str:
    """SHA-256 ile şifre hash'ler."""
    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()


def veritabanini_kur(db: Veritabani) -> None:
    """Tüm tabloları oluşturur ve varsayılan admin kullanıcısını ekler."""
    print("=" * 45)
    print("  Veritabanı kuruluyor...")
    print("=" * 45)

    # Tabloları oluştur
    baglanti = db.baglan()
    try:
        imleç = baglanti.cursor()
        for sorgu in TABLOLAR:
            imleç.execute(sorgu)
        baglanti.commit()
        print("  ✓ Tüm tablolar oluşturuldu.")
    except sqlite3.Error as hata:
        print(f"  [HATA] Tablolar oluşturulamadı: {hata}")
        return
    finally:
        baglanti.close()

    # Varsayılan admin — daha önce eklenmemişse ekle
    mevcut = db.tek_kayit_getir(
        "SELECT id FROM kullanicilar WHERE kullanici_adi = ?", ("admin",)
    )
    if not mevcut:
        db.sorgu_calistir(
            "INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)",
            ("admin", sifre_hashle("admin123"), "admin"),
        )
        print("  ✓ Varsayılan admin oluşturuldu.")
        print("     Kullanıcı : admin")
        print("     Şifre     : admin123")
    else:
        print("  ✓ Admin kullanıcısı zaten mevcut.")

    print("=" * 45)
    print("  Kurulum tamamlandı.\n")


# ─────────────────────────────────────────────────────
#  Modül doğrudan çalıştırıldığında test
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    db = Veritabani("data/mini_erp.db")
    veritabanini_kur(db)

    # Basit test: admin kaydı var mı?
    kayit = db.tek_kayit_getir(
        "SELECT kullanici_adi, rol FROM kullanicilar WHERE kullanici_adi = ?",
        ("admin",)
    )
    if kayit:
        print(f"Test OK → kullanıcı: {kayit['kullanici_adi']} | rol: {kayit['rol']}")
    else:
        print("Test BAŞARISIZ → admin kaydı bulunamadı.")
