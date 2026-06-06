"""
MiniERP - Kimlik Doğrulama ve Yetki Yönetimi
Kullanıcı girişi, şifre kontrolü ve rol bazlı yetki sistemi.
"""

import hashlib
from database import Veritabani


# ─────────────────────────────────────────────
#  Rol Yetki Tablosu
# ─────────────────────────────────────────────

YETKİLER = {
    "admin": [
        "urun_ekle", "urun_guncelle", "urun_sil", "urun_listele",
        "musteri_ekle", "musteri_guncelle", "musteri_sil", "musteri_listele",
        "tedarikci_ekle", "tedarikci_guncelle", "tedarikci_sil", "tedarikci_listele",
        "stok_giris", "stok_listele",
        "satis_yap", "satis_listele", "satis_iptal",
        "odeme_al", "cari_listele",
        "rapor_goruntule", "dosyaya_aktar",
        "kullanici_ekle", "kullanici_listele", "log_goruntule",
    ],
    "personel": [
        "urun_listele",
        "musteri_ekle", "musteri_listele",
        "stok_listele",
        "satis_yap", "satis_listele",
        "cari_listele",
    ],
    "muhasebe": [
        "urun_listele",
        "musteri_listele",
        "stok_listele",
        "satis_listele",
        "odeme_al", "cari_listele",
        "rapor_goruntule", "dosyaya_aktar",
    ],
}


def sifre_hashle(sifre: str) -> str:
    """SHA-256 ile şifre hash'ler."""
    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()


class GirisSistemi:
    """Kullanıcı giriş, çıkış ve yetki kontrol işlemlerini yönetir."""

    def __init__(self, db: Veritabani):
        self.db = db
        self.aktif_kullanici = None  # giriş yapan kullanıcı bilgisi

    # ─────────────────────────────────────────
    #  Giriş / Çıkış
    # ─────────────────────────────────────────

    def giris_yap(self) -> bool:
        """
        Kullanıcı adı ve şifre alır, doğrularsa aktif_kullanici'yı set eder.
        Başarılı ise True, hatalı ise False döner.
        """
        print("\n" + "=" * 40)
        print("       MiniERP - Kullanıcı Girişi")
        print("=" * 40)

        kullanici_adi = input("Kullanıcı adı: ").strip()
        sifre        = input("Şifre        : ").strip()

        if not kullanici_adi or not sifre:
            print("[HATA] Kullanıcı adı ve şifre boş olamaz!")
            return False

        hashli_sifre = sifre_hashle(sifre)

        kayit = self.db.tek_kayit_getir(
            """
            SELECT id, kullanici_adi, rol
            FROM kullanicilar
            WHERE kullanici_adi = ? AND sifre = ? AND aktif = 1
            """,
            (kullanici_adi, hashli_sifre)
        )

        if kayit:
            self.aktif_kullanici = {
                "id"           : kayit["id"],
                "kullanici_adi": kayit["kullanici_adi"],
                "rol"          : kayit["rol"],
            }
            print(f"\n  Hoş geldin, {kayit['kullanici_adi']}! (Rol: {kayit['rol']})")
            return True
        else:
            print("\n  [HATA] Kullanıcı adı veya şifre hatalı!")
            return False

    def cikis_yap(self) -> None:
        """Aktif kullanıcıyı temizler."""
        if self.aktif_kullanici:
            print(f"\n  Güle güle, {self.aktif_kullanici['kullanici_adi']}!")
        self.aktif_kullanici = None

    # ─────────────────────────────────────────
    #  Yetki Kontrolü
    # ─────────────────────────────────────────

    def yetkisi_var_mi(self, islem: str) -> bool:
        """
        Aktif kullanıcının belirtilen işlemi yapma yetkisi var mı?
        Yetki yoksa hata mesajı basar.
        """
        if not self.aktif_kullanici:
            print("[HATA] Giriş yapılmamış!")
            return False

        rol = self.aktif_kullanici["rol"]
        izin_listesi = YETKİLER.get(rol, [])

        if islem in izin_listesi:
            return True
        else:
            print(f"[YETKİ HATASI] '{rol}' rolünün bu işlem için yetkisi yok!")
            return False

    def giris_zorunlu(self) -> bool:
        """Giriş yapılmış mı kontrol eder."""
        if not self.aktif_kullanici:
            print("[HATA] Bu işlem için giriş yapmanız gerekiyor!")
            return False
        return True

    # ─────────────────────────────────────────
    #  Kullanıcı Yönetimi (sadece admin)
    # ─────────────────────────────────────────

    def kullanici_ekle(self) -> None:
        """Yeni kullanıcı ekler. Sadece admin yapabilir."""
        if not self.yetkisi_var_mi("kullanici_ekle"):
            return

        print("\n--- Yeni Kullanıcı Ekle ---")
        kullanici_adi = input("Kullanıcı adı : ").strip()
        sifre         = input("Şifre         : ").strip()

        print("Roller: admin | personel | muhasebe")
        rol = input("Rol           : ").strip().lower()

        # Doğrulama
        if not kullanici_adi or not sifre or not rol:
            print("[HATA] Tüm alanlar doldurulmalıdır!")
            return

        if rol not in ("admin", "personel", "muhasebe"):
            print("[HATA] Geçersiz rol! (admin / personel / muhasebe)")
            return

        basarili = self.db.sorgu_calistir(
            "INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)",
            (kullanici_adi, sifre_hashle(sifre), rol)
        )

        if basarili:
            print(f"  ✓ '{kullanici_adi}' kullanıcısı eklendi. (Rol: {rol})")
        else:
            print("  [HATA] Kullanıcı eklenemedi. Aynı kullanıcı adı zaten var olabilir.")

    def kullanicilari_listele(self) -> None:
        """Tüm kullanıcıları listeler. Sadece admin görebilir."""
        if not self.yetkisi_var_mi("kullanici_listele"):
            return

        kayitlar = self.db.tum_kayitlari_getir(
            "SELECT id, kullanici_adi, rol, aktif FROM kullanicilar ORDER BY id"
        )

        if not kayitlar:
            print("Kayıtlı kullanıcı bulunamadı.")
            return

        print("\n" + "-" * 45)
        print(f"{'ID':<5} {'Kullanıcı Adı':<20} {'Rol':<12} {'Durum'}")
        print("-" * 45)
        for k in kayitlar:
            durum = "Aktif" if k["aktif"] == 1 else "Pasif"
            print(f"{k['id']:<5} {k['kullanici_adi']:<20} {k['rol']:<12} {durum}")
        print("-" * 45)

    def sifre_degistir(self) -> None:
        """Kendi şifresini değiştirir. Her rol yapabilir."""
        if not self.giris_zorunlu():
            return

        print("\n--- Şifre Değiştir ---")
        eski_sifre = input("Mevcut şifre : ").strip()
        yeni_sifre = input("Yeni şifre   : ").strip()
        tekrar     = input("Tekrar       : ").strip()

        if not eski_sifre or not yeni_sifre:
            print("[HATA] Şifre boş olamaz!")
            return

        if yeni_sifre != tekrar:
            print("[HATA] Yeni şifreler eşleşmiyor!")
            return

        # Eski şifre doğru mu?
        kayit = self.db.tek_kayit_getir(
            "SELECT id FROM kullanicilar WHERE id = ? AND sifre = ?",
            (self.aktif_kullanici["id"], sifre_hashle(eski_sifre))
        )

        if not kayit:
            print("[HATA] Mevcut şifre hatalı!")
            return

        self.db.sorgu_calistir(
            "UPDATE kullanicilar SET sifre = ? WHERE id = ?",
            (sifre_hashle(yeni_sifre), self.aktif_kullanici["id"])
        )
        print("  ✓ Şifre başarıyla değiştirildi.")

    # ─────────────────────────────────────────
    #  Yardımcı
    # ─────────────────────────────────────────

    def aktif_kullanici_bilgisi(self) -> dict:
        """Giriş yapmış kullanıcının bilgilerini döndürür."""
        return self.aktif_kullanici


# ─────────────────────────────────────────────
#  Modül doğrudan çalıştırıldığında test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    db = Veritabani("data/mini_erp.db")
    giris = GirisSistemi(db)

    # Giriş testi
    if giris.giris_yap():
        print("\nYetki testleri:")
        print("  urun_ekle     :", giris.yetkisi_var_mi("urun_ekle"))
        print("  satis_iptal   :", giris.yetkisi_var_mi("satis_iptal"))
        print("  kullanici_ekle:", giris.yetkisi_var_mi("kullanici_ekle"))

        giris.kullanicilari_listele()
        giris.cikis_yap()