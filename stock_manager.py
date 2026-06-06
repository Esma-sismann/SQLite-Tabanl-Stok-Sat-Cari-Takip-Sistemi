"""
MiniERP - Stok Yönetimi Modülü
Stok girişi, stok hareketleri ve stok düzeltme işlemleri.
"""

from datetime import datetime
from database import Veritabani


class StokYoneticisi:
    """Stok giriş, çıkış ve hareket takip işlemlerini yönetir."""

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

    def _tarih(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ─────────────────────────────────────────
    #  Stok Girişi (Tedarikçiden Alım)
    # ─────────────────────────────────────────

    def stok_giris(self) -> None:
        """
        Tedarikçiden ürün alımı yapar.
        Ürün stokunu artırır ve stok_hareketleri tablosuna kayıt atar.
        """
        if not self._yetki_kontrol("stok_giris"):
            return

        print("\n--- Stok Girişi (Tedarikçiden Alım) ---")

        # Ürün listele ve seç
        urunler = self.db.tum_kayitlari_getir(
            "SELECT id, ad, kategori, stok FROM urunler WHERE aktif = 1 ORDER BY ad"
        )
        if not urunler:
            print("[HATA] Kayıtlı ürün bulunamadı!")
            return

        print("\n── Ürünler ──")
        for u in urunler:
            print(f"  [{u['id']}] {u['ad']} ({u['kategori']}) - Mevcut stok: {u['stok']}")

        try:
            urun_id = int(input("\nÜrün ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return

        urun = self.db.tek_kayit_getir(
            "SELECT * FROM urunler WHERE id = ? AND aktif = 1", (urun_id,)
        )
        if not urun:
            print("[HATA] Ürün bulunamadı!")
            return

        # Tedarikçi listele ve seç
        tedarikciler = self.db.tum_kayitlari_getir(
            "SELECT id, firma_adi FROM tedarikciler ORDER BY firma_adi"
        )

        tedarikci_id = None
        if tedarikciler:
            print("\n── Tedarikçiler ──")
            for t in tedarikciler:
                print(f"  [{t['id']}] {t['firma_adi']}")
            print("  [0] Tedarikçisiz giriş")

            try:
                tedarikci_id = int(input("\nTedarikçi ID (0 = yok): ").strip())
                if tedarikci_id == 0:
                    tedarikci_id = None
            except ValueError:
                print("[HATA] Geçerli bir ID girin!")
                return

        # Miktar ve açıklama
        try:
            miktar = int(input("Giriş miktarı : ").strip())
            if miktar <= 0:
                print("[HATA] Miktar 0'dan büyük olmalıdır!")
                return
        except ValueError:
            print("[HATA] Geçerli bir miktar girin!")
            return

        tedarikci_adi = "-"
        if tedarikci_id:
            t = self.db.tek_kayit_getir(
                "SELECT firma_adi FROM tedarikciler WHERE id = ?", (tedarikci_id,)
            )
            if t:
                tedarikci_adi = t["firma_adi"]

        aciklama = f"Stok girişi - Tedarikçi: {tedarikci_adi}"
        tarih    = self._tarih()

        # Transaction: stok artır + hareket kaydet
        islemler = [
            (
                "UPDATE urunler SET stok = stok + ? WHERE id = ?",
                (miktar, urun_id)
            ),
            (
                """
                INSERT INTO stok_hareketleri
                    (urun_id, hareket_turu, miktar, aciklama, hareket_tarihi)
                VALUES (?, 'stok_giris', ?, ?, ?)
                """,
                (urun_id, miktar, aciklama, tarih)
            ),
        ]

        basarili = self.db.transaction_calistir(islemler)

        if basarili:
            yeni_stok = urun["stok"] + miktar
            print(f"\n  ✓ Stok girişi yapıldı.")
            print(f"  Ürün    : {urun['ad']}")
            print(f"  Giriş   : +{miktar} adet")
            print(f"  Yeni stok: {yeni_stok} adet")
        else:
            print("  [HATA] Stok girişi yapılamadı!")

    # ─────────────────────────────────────────
    #  Manuel Stok Düzeltme
    # ─────────────────────────────────────────

    def stok_duzelt(self) -> None:
        """Sayım hatası gibi durumlarda stok manuel düzeltme yapar."""
        if not self._yetki_kontrol("stok_giris"):
            return

        print("\n--- Manuel Stok Düzeltme ---")

        urunler = self.db.tum_kayitlari_getir(
            "SELECT id, ad, stok FROM urunler WHERE aktif = 1 ORDER BY ad"
        )
        if not urunler:
            print("[HATA] Kayıtlı ürün bulunamadı!")
            return

        for u in urunler:
            print(f"  [{u['id']}] {u['ad']} - Mevcut stok: {u['stok']}")

        try:
            urun_id = int(input("\nÜrün ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return

        urun = self.db.tek_kayit_getir(
            "SELECT * FROM urunler WHERE id = ? AND aktif = 1", (urun_id,)
        )
        if not urun:
            print("[HATA] Ürün bulunamadı!")
            return

        try:
            yeni_stok = int(input(f"Yeni stok miktarı (mevcut: {urun['stok']}): ").strip())
            if yeni_stok < 0:
                print("[HATA] Stok negatif olamaz!")
                return
        except ValueError:
            print("[HATA] Geçerli bir miktar girin!")
            return

        fark      = yeni_stok - urun["stok"]
        aciklama  = input("Düzeltme nedeni: ").strip() or "Manuel stok düzeltmesi"
        tarih     = self._tarih()

        islemler = [
            (
                "UPDATE urunler SET stok = ? WHERE id = ?",
                (yeni_stok, urun_id)
            ),
            (
                """
                INSERT INTO stok_hareketleri
                    (urun_id, hareket_turu, miktar, aciklama, hareket_tarihi)
                VALUES (?, 'duzeltme', ?, ?, ?)
                """,
                (urun_id, fark, aciklama, tarih)
            ),
        ]

        basarili = self.db.transaction_calistir(islemler)

        if basarili:
            print(f"\n  ✓ Stok düzeltildi.")
            print(f"  Eski stok: {urun['stok']} → Yeni stok: {yeni_stok} (Fark: {fark:+d})")
        else:
            print("  [HATA] Stok düzeltilemedi!")

    # ─────────────────────────────────────────
    #  Stok Hareketi Kaydet (diğer modüller kullanır)
    # ─────────────────────────────────────────

    def hareket_kaydet(self, urun_id: int, hareket_turu: str,
                       miktar: int, aciklama: str = "") -> bool:
        """
        Stok hareketi kaydeder. Satış modülü bu metodu çağırır.
        hareket_turu: stok_giris | stok_cikis | satis | iade | duzeltme
        """
        tarih = self._tarih()
        return self.db.sorgu_calistir(
            """
            INSERT INTO stok_hareketleri
                (urun_id, hareket_turu, miktar, aciklama, hareket_tarihi)
            VALUES (?, ?, ?, ?, ?)
            """,
            (urun_id, hareket_turu, miktar, aciklama, tarih)
        )

    # ─────────────────────────────────────────
    #  Stok Hareketlerini Listele
    # ─────────────────────────────────────────

    def stok_hareketleri_listele(self) -> None:
        """Tüm stok hareketlerini listeler."""
        if not self._yetki_kontrol("stok_listele"):
            return

        print("\n── Filtre ──")
        print("1 - Tüm hareketler")
        print("2 - Belirli bir ürünün hareketleri")
        secim = input("Seçim: ").strip()

        if secim == "2":
            urunler = self.db.tum_kayitlari_getir(
                "SELECT id, ad FROM urunler WHERE aktif = 1 ORDER BY ad"
            )
            for u in urunler:
                print(f"  [{u['id']}] {u['ad']}")
            try:
                urun_id = int(input("Ürün ID: ").strip())
            except ValueError:
                print("[HATA] Geçerli bir ID girin!")
                return

            hareketler = self.db.tum_kayitlari_getir(
                """
                SELECT sh.id, p.ad as urun_adi, sh.hareket_turu,
                       sh.miktar, sh.aciklama, sh.hareket_tarihi
                FROM stok_hareketleri sh
                JOIN urunler p ON sh.urun_id = p.id
                WHERE sh.urun_id = ?
                ORDER BY sh.hareket_tarihi DESC
                LIMIT 50
                """,
                (urun_id,)
            )
        else:
            hareketler = self.db.tum_kayitlari_getir(
                """
                SELECT sh.id, p.ad as urun_adi, sh.hareket_turu,
                       sh.miktar, sh.aciklama, sh.hareket_tarihi
                FROM stok_hareketleri sh
                JOIN urunler p ON sh.urun_id = p.id
                ORDER BY sh.hareket_tarihi DESC
                LIMIT 50
                """
            )

        if not hareketler:
            print("\nHareket kaydı bulunamadı.")
            return

        print("\n" + "=" * 85)
        print(f"{'ID':<5} {'Ürün':<22} {'Tür':<14} {'Miktar':>7} {'Tarih':<22} {'Açıklama'}")
        print("=" * 85)

        for h in hareketler:
            print(
                f"{h['id']:<5} {h['urun_adi']:<22} {h['hareket_turu']:<14} "
                f"{h['miktar']:>+7} {h['hareket_tarihi']:<22} "
                f"{str(h['aciklama'] or '-')[:25]}"
            )

        print("=" * 85)
        print(f"Son {len(hareketler)} hareket listelendi.")

    # ─────────────────────────────────────────
    #  Güncel Stok Durumu
    # ─────────────────────────────────────────

    def stok_durumu_listele(self) -> None:
        """Tüm ürünlerin güncel stok durumunu gösterir."""
        if not self._yetki_kontrol("stok_listele"):
            return

        urunler = self.db.tum_kayitlari_getir(
            """
            SELECT id, ad, kategori, stok, kritik_stok
            FROM urunler
            WHERE aktif = 1
            ORDER BY stok ASC
            """
        )

        if not urunler:
            print("\nÜrün bulunamadı.")
            return

        print("\n" + "=" * 60)
        print(f"{'ID':<5} {'Ürün Adı':<25} {'Kategori':<15} {'Stok':>6} {'Durum'}")
        print("=" * 60)

        for u in urunler:
            if u["stok"] == 0:
                durum = "⛔ TÜKENDİ"
            elif u["stok"] <= u["kritik_stok"]:
                durum = "⚠ KRİTİK"
            else:
                durum = "✓ Yeterli"

            print(f"{u['id']:<5} {u['ad']:<25} {u['kategori']:<15} {u['stok']:>6}  {durum}")

        print("=" * 60)


# ─────────────────────────────────────────────
#  Modül doğrudan çalıştırıldığında test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    from auth import GirisSistemi

    db    = Veritabani("data/mini_erp.db")
    giris = GirisSistemi(db)

    if giris.giris_yap():
        sy = StokYoneticisi(db, giris)

        while True:
            print("\n====== STOK İŞLEMLERİ ======")
            print("1 - Stok girişi yap")
            print("2 - Stok durumunu listele")
            print("3 - Stok hareketlerini listele")
            print("4 - Manuel stok düzelt")
            print("0 - Çıkış")

            secim = input("\nSeçiminiz: ").strip()

            if secim == "1":
                sy.stok_giris()
            elif secim == "2":
                sy.stok_durumu_listele()
            elif secim == "3":
                sy.stok_hareketleri_listele()
            elif secim == "4":
                sy.stok_duzelt()
            elif secim == "0":
                giris.cikis_yap()
                break
            else:
                print("[HATA] Geçersiz seçim!")