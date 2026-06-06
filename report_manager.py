"""
MiniERP - Raporlama Modülü

"""

from datetime import datetime
from database import Veritabani


class RaporYoneticisi:
    """SQL ağırlıklı raporlama işlemlerini yönetir."""

    def __init__(self, db: Veritabani, giris_sistemi=None):
        self.db = db
        self.giris = giris_sistemi


    def _yetki_kontrol(self, islem: str) -> bool:
        if self.giris and not self.giris.yetkisi_var_mi(islem):
            return False
        return True

    def _bugun(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _baslik_yazdir(self, baslik: str) -> None:
        print(f"\n{'='*55}")
        print(f"  {baslik}")
        print(f"  Oluşturulma: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*55}")

  


    def gunluk_satis_raporu(self) -> list:
        """Bugünkü satışları listeler ve toplamı gösterir."""
        if not self._yetki_kontrol("rapor_goruntule"):
            return []

        tarih = input("Tarih (boş = bugün, örn: 2026-06-06): ").strip() or self._bugun()

        self._baslik_yazdir(f"Günlük Satış Raporu — {tarih}")

        satislar = self.db.tum_kayitlari_getir(
            """
            SELECT s.id, m.ad_soyad, k.kullanici_adi,
                   s.toplam_tutar, s.odenen_tutar, s.odeme_turu, s.satis_tarihi
            FROM satislar s
            LEFT JOIN musteriler m  ON s.musteri_id   = m.id
            JOIN kullanicilar k     ON s.kullanici_id = k.id
            WHERE DATE(s.satis_tarihi) = ? AND s.iptal = 0
            ORDER BY s.satis_tarihi
            """,
            (tarih,)
        )

        if not satislar:
            print(f"  {tarih} tarihinde satış bulunamadı.")
            return []

        print(f"  {'ID':<5} {'Müşteri':<20} {'Personel':<12} {'Toplam':>9} {'Tür':<10}")
        print(f"  {'-'*60}")
        for s in satislar:
            print(
                f"  {s['id']:<5} {str(s['ad_soyad'] or 'Müşterisiz'):<20} "
                f"{s['kullanici_adi']:<12} {s['toplam_tutar']:>9.2f} {s['odeme_turu']:<10}"
            )

        toplam = sum(s["toplam_tutar"] for s in satislar)
        odenen = sum(s["odenen_tutar"] for s in satislar)
        print(f"  {'─'*60}")
        print(f"  Satış sayısı  : {len(satislar)}")
        print(f"  Toplam ciro   : {toplam:.2f} TL")
        print(f"  Tahsil edilen : {odenen:.2f} TL")
        print(f"  Veresiye      : {toplam - odenen:.2f} TL")

        return [dict(s) for s in satislar]

   
   

    def aylik_satis_raporu(self) -> list:
        """Seçilen ay/yıl için satış özeti gösterir."""
        if not self._yetki_kontrol("rapor_goruntule"):
            return []

        yil  = input(f"Yıl  (boş = {datetime.now().year}): ").strip() or str(datetime.now().year)
        ay   = input(f"Ay   (boş = {datetime.now().month:02d}): ").strip() or f"{datetime.now().month:02d}"
        donem = f"{yil}-{ay.zfill(2)}"

        self._baslik_yazdir(f"Aylık Satış Raporu — {donem}")

        # Gün bazlı özet
        gunler = self.db.tum_kayitlari_getir(
            """
            SELECT DATE(satis_tarihi) as gun,
                   COUNT(*) as satis_sayisi,
                   SUM(toplam_tutar) as toplam,
                   SUM(odenen_tutar) as odenen
            FROM satislar
            WHERE strftime('%Y-%m', satis_tarihi) = ? AND iptal = 0
            GROUP BY DATE(satis_tarihi)
            ORDER BY gun
            """,
            (donem,)
        )

        if not gunler:
            print(f"  {donem} döneminde satış bulunamadı.")
            return []

        print(f"  {'Gün':<12} {'Satış Sayısı':>13} {'Toplam':>12} {'Ödenen':>12}")
        print(f"  {'-'*52}")
        for g in gunler:
            print(
                f"  {g['gun']:<12} {g['satis_sayisi']:>13} "
                f"{g['toplam']:>12.2f} {g['odenen']:>12.2f}"
            )

        toplam_ciro   = sum(g["toplam"]       for g in gunler)
        toplam_odenen = sum(g["odenen"]       for g in gunler)
        toplam_satis  = sum(g["satis_sayisi"] for g in gunler)

        print(f"  {'─'*52}")
        print(f"  Toplam satış  : {toplam_satis}")
        print(f"  Aylık ciro    : {toplam_ciro:.2f} TL")
        print(f"  Tahsil edilen : {toplam_odenen:.2f} TL")
        print(f"  Veresiye      : {toplam_ciro - toplam_odenen:.2f} TL")

        return [dict(g) for g in gunler]


    def en_cok_satilan_urunler(self) -> list:
        """Satış adedine göre en çok satılan ürünleri listeler."""
        if not self._yetki_kontrol("rapor_goruntule"):
            return []

        self._baslik_yazdir("En Çok Satılan Ürünler")

        urunler = self.db.tum_kayitlari_getir(
            """
            SELECT p.ad, p.kategori,
                   SUM(si.miktar)       AS toplam_adet,
                   SUM(si.toplam_fiyat) AS toplam_ciro,
                   COUNT(DISTINCT si.satis_id) AS satis_sayisi
            FROM satis_kalemleri si
            JOIN urunler p  ON si.urun_id = p.id
            JOIN satislar s ON si.satis_id = s.id
            WHERE s.iptal = 0
            GROUP BY p.id
            ORDER BY toplam_adet DESC
            LIMIT 10
            """
        )

        if not urunler:
            print("  Satış verisi bulunamadı.")
            return []

        print(f"  {'#':<4} {'Ürün Adı':<25} {'Kategori':<15} {'Adet':>6} {'Ciro':>12}")
        print(f"  {'-'*65}")
        for i, u in enumerate(urunler, 1):
            print(
                f"  {i:<4} {u['ad']:<25} {u['kategori']:<15} "
                f"{u['toplam_adet']:>6} {u['toplam_ciro']:>12.2f} TL"
            )

        return [dict(u) for u in urunler]

    

    def musteri_borc_raporu(self) -> list:
        """Borç bakiyesine göre müşterileri sıralar."""
        if not self._yetki_kontrol("rapor_goruntule"):
            return []

        self._baslik_yazdir("Müşteri Borç Raporu")

        musteriler = self.db.tum_kayitlari_getir(
            """
            SELECT m.ad_soyad, m.telefon, m.borc_bakiyesi,
                   COUNT(s.id) as toplam_satis
            FROM musteriler m
            LEFT JOIN satislar s ON m.id = s.musteri_id AND s.iptal = 0
            WHERE m.borc_bakiyesi > 0
            GROUP BY m.id
            ORDER BY m.borc_bakiyesi DESC
            """
        )

        if not musteriler:
            print("  Borçlu müşteri bulunamadı.")
            return []

        print(f"  {'Ad Soyad':<25} {'Telefon':<15} {'Toplam Satış':>13} {'Borç':>12}")
        print(f"  {'-'*68}")
        for m in musteriler:
            print(
                f"  {m['ad_soyad']:<25} {str(m['telefon'] or '-'):<15} "
                f"{m['toplam_satis']:>13} {m['borc_bakiyesi']:>12.2f} TL"
            )

        toplam = sum(m["borc_bakiyesi"] for m in musteriler)
        print(f"  {'─'*68}")
        print(f"  Toplam açık borç: {toplam:.2f} TL")

        return [dict(m) for m in musteriler]

  

    def kritik_stok_raporu(self) -> list:
        """Kritik seviyedeki ürünleri listeler."""
        if not self._yetki_kontrol("rapor_goruntule"):
            return []

        self._baslik_yazdir("Kritik Stok Raporu")

        urunler = self.db.tum_kayitlari_getir(
            """
            SELECT id, ad, kategori, stok, kritik_stok,
                   (kritik_stok - stok) AS eksik_miktar
            FROM urunler
            WHERE aktif = 1 AND stok <= kritik_stok
            ORDER BY stok ASC
            """
        )

        if not urunler:
            print("  ✓ Kritik stokta ürün yok.")
            return []

        print(f"  {'Ürün Adı':<25} {'Kategori':<15} {'Stok':>6} {'Kritik':>7} {'Eksik':>7}")
        print(f"  {'-'*63}")
        for u in urunler:
            durum = "⛔ TÜKENDİ" if u["stok"] == 0 else "⚠ KRİTİK"
            print(
                f"  {u['ad']:<25} {u['kategori']:<15} "
                f"{u['stok']:>6} {u['kritik_stok']:>7} {u['eksik_miktar']:>7}  {durum}"
            )

        print(f"  {'─'*63}")
        print(f"  Toplam {len(urunler)} ürün kritik/tükendi.")

        return [dict(u) for u in urunler]

   

    def kategori_satis_raporu(self) -> list:
        """Kategoriye göre satış cirosu ve adet özetini gösterir."""
        if not self._yetki_kontrol("rapor_goruntule"):
            return []

        self._baslik_yazdir("Kategori Bazlı Satış Raporu")

        kategoriler = self.db.tum_kayitlari_getir(
            """
            SELECT p.kategori,
                   COUNT(DISTINCT s.id)  AS satis_sayisi,
                   SUM(si.miktar)        AS toplam_adet,
                   SUM(si.toplam_fiyat)  AS toplam_ciro
            FROM satis_kalemleri si
            JOIN urunler p  ON si.urun_id  = p.id
            JOIN satislar s ON si.satis_id = s.id
            WHERE s.iptal = 0
            GROUP BY p.kategori
            ORDER BY toplam_ciro DESC
            """
        )

        if not kategoriler:
            print("  Satış verisi bulunamadı.")
            return []

        print(f"  {'Kategori':<20} {'Satış':>7} {'Adet':>7} {'Ciro':>14}")
        print(f"  {'-'*52}")
        for k in kategoriler:
            print(
                f"  {k['kategori']:<20} {k['satis_sayisi']:>7} "
                f"{k['toplam_adet']:>7} {k['toplam_ciro']:>14.2f} TL"
            )

        toplam_ciro = sum(k["toplam_ciro"] for k in kategoriler)
        print(f"  {'─'*52}")
        print(f"  Genel toplam: {toplam_ciro:.2f} TL")

        return [dict(k) for k in kategoriler]


    def personel_satis_raporu(self) -> list:
        """Personele göre satış performansını gösterir."""
        if not self._yetki_kontrol("rapor_goruntule"):
            return []

        self._baslik_yazdir("Personel Bazlı Satış Raporu")

        personeller = self.db.tum_kayitlari_getir(
            """
            SELECT k.kullanici_adi, k.rol,
                   COUNT(s.id)          AS satis_sayisi,
                   SUM(s.toplam_tutar)  AS toplam_ciro,
                   AVG(s.toplam_tutar)  AS ortalama_satis
            FROM satislar s
            JOIN kullanicilar k ON s.kullanici_id = k.id
            WHERE s.iptal = 0
            GROUP BY k.id
            HAVING satis_sayisi > 0
            ORDER BY toplam_ciro DESC
            """
        )

        if not personeller:
            print("  Satış verisi bulunamadı.")
            return []

        print(f"  {'Personel':<20} {'Rol':<12} {'Satış':>7} {'Toplam Ciro':>14} {'Ortalama':>12}")
        print(f"  {'-'*68}")
        for p in personeller:
            print(
                f"  {p['kullanici_adi']:<20} {p['rol']:<12} {p['satis_sayisi']:>7} "
                f"{p['toplam_ciro']:>14.2f} {p['ortalama_satis']:>12.2f} TL"
            )

        return [dict(p) for p in personeller]


    def musteri_alisveris_gecmisi(self) -> list:
        """Seçilen müşterinin tüm satış geçmişini gösterir."""
        if not self._yetki_kontrol("rapor_goruntule"):
            return []

        musteriler = self.db.tum_kayitlari_getir(
            "SELECT id, ad_soyad FROM musteriler ORDER BY ad_soyad"
        )
        if not musteriler:
            print("  Müşteri bulunamadı.")
            return []

        for m in musteriler:
            print(f"  [{m['id']}] {m['ad_soyad']}")

        try:
            musteri_id = int(input("\nMüşteri ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return []

        musteri = self.db.tek_kayit_getir(
            "SELECT * FROM musteriler WHERE id = ?", (musteri_id,)
        )
        if not musteri:
            print("[HATA] Müşteri bulunamadı!")
            return []

        self._baslik_yazdir(f"Alışveriş Geçmişi — {musteri['ad_soyad']}")

        satislar = self.db.tum_kayitlari_getir(
            """
            SELECT s.id, s.toplam_tutar, s.odenen_tutar,
                   s.odeme_turu, s.satis_tarihi,
                   COUNT(si.id) AS kalem_sayisi
            FROM satislar s
            LEFT JOIN satis_kalemleri si ON s.id = si.satis_id
            WHERE s.musteri_id = ? AND s.iptal = 0
            GROUP BY s.id
            ORDER BY s.satis_tarihi DESC
            """,
            (musteri_id,)
        )

        if not satislar:
            print("  Bu müşteriye ait satış bulunamadı.")
            return []

        print(f"  {'ID':<5} {'Tarih':<22} {'Ürün Sayısı':>11} {'Toplam':>10} {'Tür':<10}")
        print(f"  {'-'*62}")
        for s in satislar:
            print(
                f"  {s['id']:<5} {s['satis_tarihi']:<22} {s['kalem_sayisi']:>11} "
                f"{s['toplam_tutar']:>10.2f} {s['odeme_turu']:<10}"
            )

        toplam = sum(s["toplam_tutar"] for s in satislar)
        print(f"  {'─'*62}")
        print(f"  Toplam {len(satislar)} alışveriş | Toplam harcama: {toplam:.2f} TL")
        print(f"  Mevcut borç: {musteri['borc_bakiyesi']:.2f} TL")

        return [dict(s) for s in satislar]

    # ─────────────────────────────────────────
    #  9. En Yüksek Ciro Yapan Ürünler
    # ─────────────────────────────────────────

    def en_yuksek_cirolu_urunler(self) -> list:
        """Ciro bazında en iyi performans gösteren ürünleri listeler."""
        if not self._yetki_kontrol("rapor_goruntule"):
            return []

        self._baslik_yazdir("En Yüksek Ciro Yapan Ürünler")

        urunler = self.db.tum_kayitlari_getir(
            """
            SELECT p.ad, p.kategori,
                   p.alis_fiyati, p.satis_fiyati,
                   SUM(si.miktar)       AS toplam_adet,
                   SUM(si.toplam_fiyat) AS toplam_ciro,
                   SUM(si.miktar * (p.satis_fiyati - p.alis_fiyati)) AS tahmini_kar
            FROM satis_kalemleri si
            JOIN urunler p  ON si.urun_id  = p.id
            JOIN satislar s ON si.satis_id = s.id
            WHERE s.iptal = 0
            GROUP BY p.id
            ORDER BY toplam_ciro DESC
            LIMIT 10
            """
        )

        if not urunler:
            print("  Satış verisi bulunamadı.")
            return []

        print(f"  {'#':<4} {'Ürün Adı':<22} {'Adet':>6} {'Ciro':>12} {'Tahmini Kâr':>13}")
        print(f"  {'-'*61}")
        for i, u in enumerate(urunler, 1):
            print(
                f"  {i:<4} {u['ad']:<22} {u['toplam_adet']:>6} "
                f"{u['toplam_ciro']:>12.2f} {u['tahmini_kar']:>13.2f} TL"
            )

        return [dict(u) for u in urunler]



if __name__ == "__main__":
    from auth import GirisSistemi

    db    = Veritabani("data/mini_erp.db")
    giris = GirisSistemi(db)

    if giris.giris_yap():
        ry = RaporYoneticisi(db, giris)

        while True:
            print("\n====== RAPORLAR ======")
            print("1  - Günlük satış raporu")
            print("2  - Aylık satış raporu")
            print("3  - En çok satılan ürünler")
            print("4  - Müşteri borç raporu")
            print("5  - Kritik stok raporu")
            print("6  - Kategori bazlı satış")
            print("7  - Personel bazlı satış")
            print("8  - Müşteri alışveriş geçmişi")
            print("9  - En yüksek cirolu ürünler")
            print("0  - Çıkış")

            secim = input("\nSeçiminiz: ").strip()

            if secim == "1":
                ry.gunluk_satis_raporu()
            elif secim == "2":
                ry.aylik_satis_raporu()
            elif secim == "3":
                ry.en_cok_satilan_urunler()
            elif secim == "4":
                ry.musteri_borc_raporu()
            elif secim == "5":
                ry.kritik_stok_raporu()
            elif secim == "6":
                ry.kategori_satis_raporu()
            elif secim == "7":
                ry.personel_satis_raporu()
            elif secim == "8":
                ry.musteri_alisveris_gecmisi()
            elif secim == "9":
                ry.en_yuksek_cirolu_urunler()
            elif secim == "0":
                giris.cikis_yap()
                break
            else:
                print("[HATA] Geçersiz seçim!")