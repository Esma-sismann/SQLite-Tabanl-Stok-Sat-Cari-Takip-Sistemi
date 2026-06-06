"""
MiniERP - Tedarikçi Yönetimi Modülü
Tedarikçi ekleme, güncelleme, silme ve listeleme işlemleri.
"""

from database import Veritabani


class TedarikciYoneticisi:
    """Tedarikçi CRUD işlemlerini yönetir."""

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
    #  Tedarikçi Ekle
    # ─────────────────────────────────────────

    def tedarikci_ekle(self) -> None:
        """Yeni tedarikçi ekler."""
        if not self._yetki_kontrol("tedarikci_ekle"):
            return

        print("\n--- Yeni Tedarikçi Ekle ---")

        firma_adi = input("Firma adı     : ").strip()
        if not firma_adi:
            print("[HATA] Firma adı boş olamaz!")
            return

        yetkili_adi = input("Yetkili adı   : ").strip()
        telefon     = input("Telefon       : ").strip()
        email       = input("E-posta       : ").strip()
        adres       = input("Adres         : ").strip()

        basarili = self.db.sorgu_calistir(
            """
            INSERT INTO tedarikciler (firma_adi, yetkili_adi, telefon, email, adres)
            VALUES (?, ?, ?, ?, ?)
            """,
            (firma_adi, yetkili_adi, telefon, email, adres)
        )

        if basarili:
            print(f"  ✓ '{firma_adi}' tedarikçisi eklendi.")
        else:
            print("  [HATA] Tedarikçi eklenemedi.")

    # ─────────────────────────────────────────
    #  Tedarikçi Güncelle
    # ─────────────────────────────────────────

    def tedarikci_guncelle(self) -> None:
        """Mevcut tedarikçi bilgilerini günceller."""
        if not self._yetki_kontrol("tedarikci_guncelle"):
            return

        self.tedarikcileri_listele()

        try:
            tedarikci_id = int(input("\nGüncellenecek tedarikçi ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return

        tedarikci = self.db.tek_kayit_getir(
            "SELECT * FROM tedarikciler WHERE id = ?", (tedarikci_id,)
        )
        if not tedarikci:
            print("[HATA] Tedarikçi bulunamadı!")
            return

        print(f"\nMevcut: {tedarikci['firma_adi']} | {tedarikci['yetkili_adi']} | {tedarikci['telefon']}")
        print("(Değiştirmek istemediğin alanları boş bırak)\n")

        firma_adi   = input(f"Firma adı     [{tedarikci['firma_adi']}]: ").strip()   or tedarikci["firma_adi"]
        yetkili_adi = input(f"Yetkili adı   [{tedarikci['yetkili_adi']}]: ").strip() or tedarikci["yetkili_adi"]
        telefon     = input(f"Telefon       [{tedarikci['telefon']}]: ").strip()     or tedarikci["telefon"]
        email       = input(f"E-posta       [{tedarikci['email']}]: ").strip()       or tedarikci["email"]
        adres       = input(f"Adres         [{tedarikci['adres']}]: ").strip()       or tedarikci["adres"]

        self.db.sorgu_calistir(
            """
            UPDATE tedarikciler
            SET firma_adi=?, yetkili_adi=?, telefon=?, email=?, adres=?
            WHERE id=?
            """,
            (firma_adi, yetkili_adi, telefon, email, adres, tedarikci_id)
        )
        print(f"  ✓ '{firma_adi}' tedarikçisi güncellendi.")

    # ─────────────────────────────────────────
    #  Tedarikçi Sil
    # ─────────────────────────────────────────

    def tedarikci_sil(self) -> None:
        """Tedarikçiyi siler."""
        if not self._yetki_kontrol("tedarikci_sil"):
            return

        self.tedarikcileri_listele()

        try:
            tedarikci_id = int(input("\nSilinecek tedarikçi ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return

        tedarikci = self.db.tek_kayit_getir(
            "SELECT firma_adi FROM tedarikciler WHERE id = ?", (tedarikci_id,)
        )
        if not tedarikci:
            print("[HATA] Tedarikçi bulunamadı!")
            return

        onay = input(f"'{tedarikci['firma_adi']}' tedarikçisini silmek istediğine emin misin? (e/h): ").strip().lower()
        if onay != "e":
            print("  İşlem iptal edildi.")
            return

        self.db.sorgu_calistir("DELETE FROM tedarikciler WHERE id = ?", (tedarikci_id,))
        print(f"  ✓ '{tedarikci['firma_adi']}' tedarikçisi silindi.")

    # ─────────────────────────────────────────
    #  Tedarikçileri Listele
    # ─────────────────────────────────────────

    def tedarikcileri_listele(self) -> None:
        """Tüm tedarikçileri listeler."""
        if not self._yetki_kontrol("tedarikci_listele"):
            return

        tedarikciler = self.db.tum_kayitlari_getir(
            """
            SELECT id, firma_adi, yetkili_adi, telefon, email
            FROM tedarikciler
            ORDER BY firma_adi
            """
        )

        if not tedarikciler:
            print("\nKayıtlı tedarikçi bulunamadı.")
            return

        print("\n" + "=" * 80)
        print(f"{'ID':<5} {'Firma Adı':<25} {'Yetkili':<20} {'Telefon':<15} {'E-posta'}")
        print("=" * 80)

        for t in tedarikciler:
            print(
                f"{t['id']:<5} {t['firma_adi']:<25} "
                f"{str(t['yetkili_adi'] or '-'):<20} "
                f"{str(t['telefon'] or '-'):<15} "
                f"{str(t['email'] or '-')}"
            )

        print("=" * 80)
        print(f"Toplam {len(tedarikciler)} tedarikçi.")

    # ─────────────────────────────────────────
    #  ID ile Tedarikçi Getir (diğer modüller kullanır)
    # ─────────────────────────────────────────

    def tedarikci_getir(self, tedarikci_id: int):
        """Tek tedarikçi bilgisini döndürür. Stok modülü tarafından kullanılır."""
        return self.db.tek_kayit_getir(
            "SELECT * FROM tedarikciler WHERE id = ?", (tedarikci_id,)
        )


# ─────────────────────────────────────────────
#  Modül doğrudan çalıştırıldığında test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    from auth import GirisSistemi

    db    = Veritabani("data/mini_erp.db")
    giris = GirisSistemi(db)

    if giris.giris_yap():
        ty = TedarikciYoneticisi(db, giris)

        while True:
            print("\n====== TEDARİKÇİ İŞLEMLERİ ======")
            print("1 - Tedarikçi ekle")
            print("2 - Tedarikçileri listele")
            print("3 - Tedarikçi güncelle")
            print("4 - Tedarikçi sil")
            print("0 - Çıkış")

            secim = input("\nSeçiminiz: ").strip()

            if secim == "1":
                ty.tedarikci_ekle()
            elif secim == "2":
                ty.tedarikcileri_listele()
            elif secim == "3":
                ty.tedarikci_guncelle()
            elif secim == "4":
                ty.tedarikci_sil()
            elif secim == "0":
                giris.cikis_yap()
                break
            else:
                print("[HATA] Geçersiz seçim!")