"""
MiniERP - Ürün Yönetimi Modülü
Ürün ekleme, güncelleme, silme, listeleme ve kritik stok kontrolü.
"""

from datetime import datetime
from database import Veritabani


class UrunYoneticisi:
    """Ürün CRUD işlemlerini ve stok kontrolünü yönetir."""

    def __init__(self, db: Veritabani, giris_sistemi=None):
        self.db = db
        self.giris = giris_sistemi  # yetki kontrolü için

    # ─────────────────────────────────────────
    #  Yardımcı
    # ─────────────────────────────────────────

    def _yetki_kontrol(self, islem: str) -> bool:
        if self.giris and not self.giris.yetkisi_var_mi(islem):
            return False
        return True

    def _sayi_al(self, mesaj: str, tam_sayi: bool = False, sifir_olabilir: bool = False):
        """Kullanıcıdan geçerli sayı alır. Hatalı girişte None döner."""
        try:
            deger = input(mesaj).strip()
            if not deger:
                print("[HATA] Bu alan boş bırakılamaz!")
                return None
            sayi = int(deger) if tam_sayi else float(deger)
            if not sifir_olabilir and sayi < 0:
                print("[HATA] Negatif değer girilemez!")
                return None
            return sayi
        except ValueError:
            print("[HATA] Lütfen geçerli bir sayı girin!")
            return None

    # ─────────────────────────────────────────
    #  Ürün Ekle
    # ─────────────────────────────────────────

    def urun_ekle(self) -> None:
        """Yeni ürün ekler."""
        if not self._yetki_kontrol("urun_ekle"):
            return

        print("\n--- Yeni Ürün Ekle ---")

        ad = input("Ürün adı       : ").strip()
        if not ad:
            print("[HATA] Ürün adı boş olamaz!")
            return

        kategori = input("Kategori       : ").strip()
        if not kategori:
            print("[HATA] Kategori boş olamaz!")
            return

        alis_fiyati = self._sayi_al("Alış fiyatı    : ")
        if alis_fiyati is None:
            return

        satis_fiyati = self._sayi_al("Satış fiyatı   : ")
        if satis_fiyati is None:
            return

        stok = self._sayi_al("Başlangıç stok : ", tam_sayi=True, sifir_olabilir=True)
        if stok is None:
            return

        kritik_stok = self._sayi_al("Kritik stok    : ", tam_sayi=True, sifir_olabilir=True)
        if kritik_stok is None:
            return

        tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        basarili = self.db.sorgu_calistir(
            """
            INSERT INTO urunler
                (ad, kategori, alis_fiyati, satis_fiyati, stok, kritik_stok, olusturulma_tarihi)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ad, kategori, alis_fiyati, satis_fiyati, stok, kritik_stok, tarih)
        )

        if basarili:
            print(f"  ✓ '{ad}' ürünü başarıyla eklendi.")
        else:
            print("  [HATA] Ürün eklenemedi.")

    # ─────────────────────────────────────────
    #  Ürün Güncelle
    # ─────────────────────────────────────────

    def urun_guncelle(self) -> None:
        """Mevcut ürün bilgilerini günceller."""
        if not self._yetki_kontrol("urun_guncelle"):
            return

        self.urunleri_listele()

        try:
            urun_id = int(input("\nGüncellenecek ürün ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return

        urun = self.db.tek_kayit_getir(
            "SELECT * FROM urunler WHERE id = ? AND aktif = 1", (urun_id,)
        )
        if not urun:
            print("[HATA] Ürün bulunamadı!")
            return

        print(f"\nMevcut bilgiler: {urun['ad']} | {urun['kategori']} | "
              f"Alış: {urun['alis_fiyati']} TL | Satış: {urun['satis_fiyati']} TL")
        print("(Değiştirmek istemediğin alanları boş bırak)\n")

        ad           = input(f"Ürün adı       [{urun['ad']}]: ").strip() or urun["ad"]
        kategori     = input(f"Kategori       [{urun['kategori']}]: ").strip() or urun["kategori"]

        alis_girdi   = input(f"Alış fiyatı    [{urun['alis_fiyati']}]: ").strip()
        satis_girdi  = input(f"Satış fiyatı   [{urun['satis_fiyati']}]: ").strip()
        kritik_girdi = input(f"Kritik stok    [{urun['kritik_stok']}]: ").strip()

        try:
            alis_fiyati  = float(alis_girdi)  if alis_girdi  else urun["alis_fiyati"]
            satis_fiyati = float(satis_girdi) if satis_girdi else urun["satis_fiyati"]
            kritik_stok  = int(kritik_girdi)  if kritik_girdi else urun["kritik_stok"]
        except ValueError:
            print("[HATA] Geçersiz sayı girişi!")
            return

        self.db.sorgu_calistir(
            """
            UPDATE urunler
            SET ad=?, kategori=?, alis_fiyati=?, satis_fiyati=?, kritik_stok=?
            WHERE id=?
            """,
            (ad, kategori, alis_fiyati, satis_fiyati, kritik_stok, urun_id)
        )
        print(f"  ✓ '{ad}' ürünü güncellendi.")

    # ─────────────────────────────────────────
    #  Ürün Sil (pasif yap)
    # ─────────────────────────────────────────

    def urun_sil(self) -> None:
        """
        Ürünü veritabanından silmek yerine pasif yapar (aktif=0).
        Böylece geçmiş satış kayıtları bozulmaz.
        """
        if not self._yetki_kontrol("urun_sil"):
            return

        self.urunleri_listele()

        try:
            urun_id = int(input("\nSilinecek ürün ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return

        urun = self.db.tek_kayit_getir(
            "SELECT ad FROM urunler WHERE id = ? AND aktif = 1", (urun_id,)
        )
        if not urun:
            print("[HATA] Ürün bulunamadı!")
            return

        onay = input(f"'{urun['ad']}' ürününü silmek istediğine emin misin? (e/h): ").strip().lower()
        if onay != "e":
            print("  İşlem iptal edildi.")
            return

        self.db.sorgu_calistir(
            "UPDATE urunler SET aktif = 0 WHERE id = ?", (urun_id,)
        )
        print(f"  ✓ '{urun['ad']}' ürünü pasif yapıldı.")

    # ─────────────────────────────────────────
    #  Ürünleri Listele
    # ─────────────────────────────────────────

    def urunleri_listele(self) -> None:
        """Aktif tüm ürünleri listeler."""
        if not self._yetki_kontrol("urun_listele"):
            return

        urunler = self.db.tum_kayitlari_getir(
            """
            SELECT id, ad, kategori, alis_fiyati, satis_fiyati, stok, kritik_stok
            FROM urunler
            WHERE aktif = 1
            ORDER BY kategori, ad
            """
        )

        if not urunler:
            print("\nKayıtlı ürün bulunamadı.")
            return

        print("\n" + "=" * 85)
        print(f"{'ID':<5} {'Ürün Adı':<22} {'Kategori':<15} {'Alış':>8} {'Satış':>8} {'Stok':>6} {'Kritik':>7}")
        print("=" * 85)

        for u in urunler:
            # Kritik stokta ise satırı işaretle
            uyari = " ⚠" if u["stok"] <= u["kritik_stok"] else ""
            print(
                f"{u['id']:<5} {u['ad']:<22} {u['kategori']:<15} "
                f"{u['alis_fiyati']:>8.2f} {u['satis_fiyati']:>8.2f} "
                f"{u['stok']:>6} {u['kritik_stok']:>7}{uyari}"
            )

        print("=" * 85)
        print(f"Toplam {len(urunler)} ürün listelendi.")

    # ─────────────────────────────────────────
    #  Kritik Stok Kontrolü
    # ─────────────────────────────────────────

    def kritik_stok_listele(self) -> list:
        """
        Stoku kritik seviyede olan ürünleri döndürür.
        Ana menü açılışında uyarı vermek için de kullanılır.
        """
        if not self._yetki_kontrol("urun_listele"):
            return []

        urunler = self.db.tum_kayitlari_getir(
            """
            SELECT id, ad, stok, kritik_stok
            FROM urunler
            WHERE aktif = 1 AND stok <= kritik_stok
            ORDER BY stok ASC
            """
        )

        if not urunler:
            print("\n  ✓ Kritik stokta ürün yok.")
            return []

        print("\n" + "!" * 50)
        print(f"  UYARI: {len(urunler)} ürün kritik stok seviyesinde!")
        print("!" * 50)
        for u in urunler:
            print(f"  - {u['ad']:<25} Stok: {u['stok']} / Kritik: {u['kritik_stok']}")
        print("!" * 50)

        return [dict(u) for u in urunler]

    # ─────────────────────────────────────────
    #  ID ile Ürün Getir (diğer modüller kullanır)
    # ─────────────────────────────────────────

    def urun_getir(self, urun_id: int):
        """Tek ürün bilgisini döndürür. Satış modülü tarafından kullanılır."""
        return self.db.tek_kayit_getir(
            "SELECT * FROM urunler WHERE id = ? AND aktif = 1", (urun_id,)
        )

    def kategorileri_listele(self) -> None:
        """Mevcut kategorileri ve ürün sayılarını gösterir."""
        kategoriler = self.db.tum_kayitlari_getir(
            """
            SELECT kategori, COUNT(*) as adet, SUM(stok) as toplam_stok
            FROM urunler
            WHERE aktif = 1
            GROUP BY kategori
            ORDER BY kategori
            """
        )

        if not kategoriler:
            print("\nKategori bulunamadı.")
            return

        print("\n--- Kategoriler ---")
        print(f"{'Kategori':<20} {'Ürün Sayısı':>12} {'Toplam Stok':>12}")
        print("-" * 46)
        for k in kategoriler:
            print(f"{k['kategori']:<20} {k['adet']:>12} {k['toplam_stok']:>12}")


# ─────────────────────────────────────────────
#  Modül doğrudan çalıştırıldığında test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    from auth import GirisSistemi

    db    = Veritabani("data/mini_erp.db")
    giris = GirisSistemi(db)

    if giris.giris_yap():
        ym = UrunYoneticisi(db, giris)

        while True:
            print("\n====== ÜRÜN İŞLEMLERİ ======")
            print("1 - Ürün ekle")
            print("2 - Ürünleri listele")
            print("3 - Ürün güncelle")
            print("4 - Ürün sil")
            print("5 - Kritik stok listesi")
            print("6 - Kategoriler")
            print("0 - Çıkış")

            secim = input("\nSeçiminiz: ").strip()

            if secim == "1":
                ym.urun_ekle()
            elif secim == "2":
                ym.urunleri_listele()
            elif secim == "3":
                ym.urun_guncelle()
            elif secim == "4":
                ym.urun_sil()
            elif secim == "5":
                ym.kritik_stok_listele()
            elif secim == "6":
                ym.kategorileri_listele()
            elif secim == "0":
                giris.cikis_yap()
                break
            else:
                print("[HATA] Geçersiz seçim!")