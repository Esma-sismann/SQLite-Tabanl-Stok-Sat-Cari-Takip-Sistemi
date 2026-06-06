"""
MiniERP - Müşteri Yönetimi Modülü
Müşteri ekleme, güncelleme, silme, listeleme ve borç takibi.
"""

from datetime import datetime
from database import Veritabani


class MusteriYoneticisi:
    """Müşteri CRUD işlemlerini ve cari borç takibini yönetir."""

    def __init__(self, db: Veritabani, giris_sistemi=None):
        self.db = db
        self.giris = giris_sistemi

    # ─────────────────────────────────────────
    #  Yardımcı
    # ─────────────────────────────────────────

    def _yetki_kontrol(self, islem: str) -> bool:
        if self.giris and not self.giris.yetkisi_var_mi(islem):
            return False
        return True

    # ─────────────────────────────────────────
    #  Müşteri Ekle
    # ─────────────────────────────────────────

    def musteri_ekle(self) -> None:
        """Yeni müşteri ekler."""
        if not self._yetki_kontrol("musteri_ekle"):
            return

        print("\n--- Yeni Müşteri Ekle ---")

        ad_soyad = input("Ad Soyad  : ").strip()
        if not ad_soyad:
            print("[HATA] Ad soyad boş olamaz!")
            return

        telefon = input("Telefon   : ").strip()
        email   = input("E-posta   : ").strip()
        adres   = input("Adres     : ").strip()

        tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        basarili = self.db.sorgu_calistir(
            """
            INSERT INTO musteriler (ad_soyad, telefon, email, adres, borc_bakiyesi, kayit_tarihi)
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (ad_soyad, telefon, email, adres, tarih)
        )

        if basarili:
            print(f"  ✓ '{ad_soyad}' müşterisi eklendi.")
        else:
            print("  [HATA] Müşteri eklenemedi.")

    # ─────────────────────────────────────────
    #  Müşteri Güncelle
    # ─────────────────────────────────────────

    def musteri_guncelle(self) -> None:
        """Mevcut müşteri bilgilerini günceller."""
        if not self._yetki_kontrol("musteri_guncelle"):
            return

        self.musterileri_listele()

        try:
            musteri_id = int(input("\nGüncellenecek müşteri ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return

        musteri = self.db.tek_kayit_getir(
            "SELECT * FROM musteriler WHERE id = ?", (musteri_id,)
        )
        if not musteri:
            print("[HATA] Müşteri bulunamadı!")
            return

        print(f"\nMevcut: {musteri['ad_soyad']} | {musteri['telefon']} | {musteri['email']}")
        print("(Değiştirmek istemediğin alanları boş bırak)\n")

        ad_soyad = input(f"Ad Soyad  [{musteri['ad_soyad']}]: ").strip() or musteri["ad_soyad"]
        telefon  = input(f"Telefon   [{musteri['telefon']}]: ").strip() or musteri["telefon"]
        email    = input(f"E-posta   [{musteri['email']}]: ").strip()   or musteri["email"]
        adres    = input(f"Adres     [{musteri['adres']}]: ").strip()   or musteri["adres"]

        self.db.sorgu_calistir(
            "UPDATE musteriler SET ad_soyad=?, telefon=?, email=?, adres=? WHERE id=?",
            (ad_soyad, telefon, email, adres, musteri_id)
        )
        print(f"  ✓ '{ad_soyad}' müşterisi güncellendi.")

    # ─────────────────────────────────────────
    #  Müşteri Sil
    # ─────────────────────────────────────────

    def musteri_sil(self) -> None:
        """Müşteriyi siler. Borcu varsa silmeye izin vermez."""
        if not self._yetki_kontrol("musteri_sil"):
            return

        self.musterileri_listele()

        try:
            musteri_id = int(input("\nSilinecek müşteri ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return

        musteri = self.db.tek_kayit_getir(
            "SELECT * FROM musteriler WHERE id = ?", (musteri_id,)
        )
        if not musteri:
            print("[HATA] Müşteri bulunamadı!")
            return

        if musteri["borc_bakiyesi"] > 0:
            print(f"[HATA] Müşterinin {musteri['borc_bakiyesi']:.2f} TL borcu var, silinemez!")
            return

        onay = input(f"'{musteri['ad_soyad']}' müşterisini silmek istediğine emin misin? (e/h): ").strip().lower()
        if onay != "e":
            print("  İşlem iptal edildi.")
            return

        self.db.sorgu_calistir("DELETE FROM musteriler WHERE id = ?", (musteri_id,))
        print(f"  ✓ '{musteri['ad_soyad']}' müşterisi silindi.")

    # ─────────────────────────────────────────
    #  Müşterileri Listele
    # ─────────────────────────────────────────

    def musterileri_listele(self) -> None:
        """Tüm müşterileri listeler."""
        if not self._yetki_kontrol("musteri_listele"):
            return

        musteriler = self.db.tum_kayitlari_getir(
            """
            SELECT id, ad_soyad, telefon, email, borc_bakiyesi
            FROM musteriler
            ORDER BY ad_soyad
            """
        )

        if not musteriler:
            print("\nKayıtlı müşteri bulunamadı.")
            return

        print("\n" + "=" * 75)
        print(f"{'ID':<5} {'Ad Soyad':<25} {'Telefon':<15} {'E-posta':<20} {'Borç':>8}")
        print("=" * 75)

        for m in musteriler:
            borc_goster = f"{m['borc_bakiyesi']:.2f} TL"
            if m["borc_bakiyesi"] > 0:
                borc_goster += " ⚠"
            print(
                f"{m['id']:<5} {m['ad_soyad']:<25} {str(m['telefon'] or '-'):<15} "
                f"{str(m['email'] or '-'):<20} {borc_goster:>10}"
            )

        print("=" * 75)
        print(f"Toplam {len(musteriler)} müşteri.")

    # ─────────────────────────────────────────
    #  Müşteri Borç Detayı
    # ─────────────────────────────────────────

    def musteri_borc_goruntule(self) -> None:
        """Seçilen müşterinin borç geçmişini gösterir."""
        if not self._yetki_kontrol("cari_listele"):
            return

        self.musterileri_listele()

        try:
            musteri_id = int(input("\nMüşteri ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return

        musteri = self.db.tek_kayit_getir(
            "SELECT * FROM musteriler WHERE id = ?", (musteri_id,)
        )
        if not musteri:
            print("[HATA] Müşteri bulunamadı!")
            return

        hareketler = self.db.tum_kayitlari_getir(
            """
            SELECT islem_turu, tutar, aciklama, islem_tarihi
            FROM cari_hareketler
            WHERE musteri_id = ?
            ORDER BY islem_tarihi DESC
            """,
            (musteri_id,)
        )

        print(f"\n{'='*60}")
        print(f"  Müşteri : {musteri['ad_soyad']}")
        print(f"  Mevcut Borç: {musteri['borc_bakiyesi']:.2f} TL")
        print(f"{'='*60}")

        if not hareketler:
            print("  Hareket kaydı bulunamadı.")
        else:
            print(f"{'Tarih':<22} {'İşlem':<16} {'Tutar':>10} {'Açıklama'}")
            print("-" * 60)
            for h in hareketler:
                print(
                    f"{h['islem_tarihi']:<22} {h['islem_turu']:<16} "
                    f"{h['tutar']:>10.2f} {h['aciklama'] or '-'}"
                )
        print("=" * 60)

    # ─────────────────────────────────────────
    #  ID ile Müşteri Getir (diğer modüller kullanır)
    # ─────────────────────────────────────────

    def musteri_getir(self, musteri_id: int):
        """Tek müşteri bilgisini döndürür."""
        return self.db.tek_kayit_getir(
            "SELECT * FROM musteriler WHERE id = ?", (musteri_id,)
        )

    def musteri_borc_guncelle(self, musteri_id: int, tutar: float) -> None:
        """
        Müşteri borcunu günceller.
        Pozitif tutar → borç artar (satış/borçlandırma)
        Negatif tutar → borç azalır (ödeme/iade)
        """
        self.db.sorgu_calistir(
            "UPDATE musteriler SET borc_bakiyesi = borc_bakiyesi + ? WHERE id = ?",
            (tutar, musteri_id)
        )


# ─────────────────────────────────────────────
#  Modül doğrudan çalıştırıldığında test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    from auth import GirisSistemi

    db    = Veritabani("data/mini_erp.db")
    giris = GirisSistemi(db)

    if giris.giris_yap():
        my = MusteriYoneticisi(db, giris)

        while True:
            print("\n====== MÜŞTERİ İŞLEMLERİ ======")
            print("1 - Müşteri ekle")
            print("2 - Müşterileri listele")
            print("3 - Müşteri güncelle")
            print("4 - Müşteri sil")
            print("5 - Müşteri borç detayı")
            print("0 - Çıkış")

            secim = input("\nSeçiminiz: ").strip()

            if secim == "1":
                my.musteri_ekle()
            elif secim == "2":
                my.musterileri_listele()
            elif secim == "3":
                my.musteri_guncelle()
            elif secim == "4":
                my.musteri_sil()
            elif secim == "5":
                my.musteri_borc_goruntule()
            elif secim == "0":
                giris.cikis_yap()
                break
            else:
                print("[HATA] Geçersiz seçim!")