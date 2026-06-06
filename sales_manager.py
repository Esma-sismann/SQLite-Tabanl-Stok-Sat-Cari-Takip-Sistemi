"""
MiniERP - Satış Yönetimi Modülü
Satış oluşturma, stok düşme, cari borç güncelleme — tek transaction içinde.
"""

from datetime import datetime
from database import Veritabani


class SatisYoneticisi:
    """Satış işlemlerini transaction ile güvenli şekilde yönetir."""

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
    #  Satış Yap  (Ana Fonksiyon)
    # ─────────────────────────────────────────

    def satis_yap(self) -> None:
        """
        Satış işlemi:
        1. Müşteri seç
        2. Ürün ekle (birden fazla olabilir)
        3. Ödeme tipini seç
        4. Transaction ile kaydet:
           - satislar tablosuna başlık
           - satis_kalemleri tablosuna her ürün
           - urunler stok düş
           - stok_hareketleri kaydet
           - musteriler borç güncelle (veresiye ise)
           - cari_hareketler kaydet (veresiye ise)
        """
        if not self._yetki_kontrol("satis_yap"):
            return

        print("\n" + "=" * 50)
        print("           YENİ SATIŞ")
        print("=" * 50)

        # ── 1. Müşteri Seç ──
        musteriler = self.db.tum_kayitlari_getir(
            "SELECT id, ad_soyad, borc_bakiyesi FROM musteriler ORDER BY ad_soyad"
        )

        musteri_id = None
        if musteriler:
            print("\n── Müşteriler ──")
            for m in musteriler:
                print(f"  [{m['id']}] {m['ad_soyad']} (Borç: {m['borc_bakiyesi']:.2f} TL)")
            print("  [0] Müşterisiz satış")

            try:
                musteri_id = int(input("\nMüşteri ID (0 = yok): ").strip())
                if musteri_id == 0:
                    musteri_id = None
            except ValueError:
                print("[HATA] Geçerli bir ID girin!")
                return

            if musteri_id:
                musteri = self.db.tek_kayit_getir(
                    "SELECT * FROM musteriler WHERE id = ?", (musteri_id,)
                )
                if not musteri:
                    print("[HATA] Müşteri bulunamadı!")
                    return

        # ── 2. Ürün Seç ──
        sepet = []  # [(urun, miktar, birim_fiyat), ...]

        while True:
            urunler = self.db.tum_kayitlari_getir(
                """
                SELECT id, ad, kategori, satis_fiyati, stok
                FROM urunler
                WHERE aktif = 1 AND stok > 0
                ORDER BY ad
                """
            )

            if not urunler:
                print("[HATA] Stokta ürün bulunamadı!")
                return

            print("\n── Stokta Olan Ürünler ──")
            print(f"{'ID':<5} {'Ürün Adı':<25} {'Fiyat':>8} {'Stok':>6}")
            print("-" * 48)
            for u in urunler:
                print(f"  [{u['id']}] {u['ad']:<25} {u['satis_fiyati']:>8.2f} TL  Stok: {u['stok']}")

            if sepet:
                print("\n── Sepet ──")
                for kalem in sepet:
                    print(f"  {kalem['urun_adi']:<25} x{kalem['miktar']}  =  {kalem['toplam_fiyat']:.2f} TL")

            print("\n[0] Satışı tamamla")
            girdi = input("Ürün ID: ").strip()

            if girdi == "0":
                break

            try:
                urun_id = int(girdi)
            except ValueError:
                print("[HATA] Geçerli bir ID girin!")
                continue

            urun = self.db.tek_kayit_getir(
                "SELECT * FROM urunler WHERE id = ? AND aktif = 1", (urun_id,)
            )
            if not urun:
                print("[HATA] Ürün bulunamadı!")
                continue

            try:
                miktar = int(input(f"Miktar (max {urun['stok']}): ").strip())
                if miktar <= 0:
                    print("[HATA] Miktar 0'dan büyük olmalı!")
                    continue
                if miktar > urun["stok"]:
                    print(f"[HATA] Yetersiz stok! Mevcut: {urun['stok']}")
                    continue
            except ValueError:
                print("[HATA] Geçerli bir miktar girin!")
                continue

            # Sepette zaten var mı?
            mevcut = next((k for k in sepet if k["urun_id"] == urun_id), None)
            if mevcut:
                toplam_miktar = mevcut["miktar"] + miktar
                if toplam_miktar > urun["stok"]:
                    print(f"[HATA] Toplam miktar stoku aşıyor! Mevcut: {urun['stok']}")
                    continue
                mevcut["miktar"]       = toplam_miktar
                mevcut["toplam_fiyat"] = toplam_miktar * mevcut["birim_fiyat"]
                print(f"  ✓ Güncellendi: {urun['ad']} x{toplam_miktar}")
            else:
                sepet.append({
                    "urun_id"     : urun_id,
                    "urun_adi"    : urun["ad"],
                    "miktar"      : miktar,
                    "birim_fiyat" : urun["satis_fiyati"],
                    "toplam_fiyat": miktar * urun["satis_fiyati"],
                })
                print(f"  ✓ Eklendi: {urun['ad']} x{miktar} = {miktar * urun['satis_fiyati']:.2f} TL")

        if not sepet:
            print("  Sepet boş, satış iptal edildi.")
            return

        # ── 3. Toplam & Ödeme ──
        toplam_tutar = sum(k["toplam_fiyat"] for k in sepet)

        print(f"\n{'─'*40}")
        print(f"  TOPLAM TUTAR : {toplam_tutar:.2f} TL")
        print(f"{'─'*40}")

        print("\nÖdeme Türü:")
        print("  1 - Nakit")
        print("  2 - Kart")
        print("  3 - Veresiye")
        print("  4 - Karma (kısmi ödeme)")

        odeme_secim = input("Seçim: ").strip()

        odeme_map = {"1": "nakit", "2": "kart", "3": "veresiye", "4": "karma"}
        if odeme_secim not in odeme_map:
            print("[HATA] Geçersiz ödeme türü!")
            return

        odeme_turu = odeme_map[odeme_secim]

        if odeme_turu == "veresiye":
            if not musteri_id:
                print("[HATA] Veresiye satış için müşteri seçilmeli!")
                return
            odenen_tutar = 0.0
        elif odeme_turu == "karma":
            if not musteri_id:
                print("[HATA] Karma ödeme için müşteri seçilmeli!")
                return
            try:
                odenen_tutar = float(input(f"Ödenen tutar (toplam: {toplam_tutar:.2f} TL): ").strip())
                if odenen_tutar < 0 or odenen_tutar > toplam_tutar:
                    print("[HATA] Geçersiz tutar!")
                    return
            except ValueError:
                print("[HATA] Geçerli bir tutar girin!")
                return
        else:
            odenen_tutar = toplam_tutar

        veresiye_tutar = toplam_tutar - odenen_tutar
        tarih          = self._tarih()
        kullanici_id   = self.giris.aktif_kullanici["id"] if self.giris else 1

        # ── 4. Özet & Onay ──
        print(f"\n{'='*45}")
        print("  SATIŞ ÖZETİ")
        print(f"{'='*45}")
        for k in sepet:
            print(f"  {k['urun_adi']:<25} x{k['miktar']}  {k['toplam_fiyat']:>8.2f} TL")
        print(f"{'─'*45}")
        print(f"  Toplam    : {toplam_tutar:>8.2f} TL")
        print(f"  Ödenen    : {odenen_tutar:>8.2f} TL")
        if veresiye_tutar > 0:
            print(f"  Veresiye  : {veresiye_tutar:>8.2f} TL")
        print(f"  Ödeme türü: {odeme_turu}")
        print(f"{'='*45}")

        onay = input("Satışı onayla? (e/h): ").strip().lower()
        if onay != "e":
            print("  Satış iptal edildi.")
            return

        # ── 5. Transaction ile Kaydet ──
        basarili = self._satisi_kaydet(
            sepet, musteri_id, kullanici_id,
            toplam_tutar, odenen_tutar, veresiye_tutar,
            odeme_turu, tarih
        )

        if basarili:
            print(f"\n  ✓ Satış başarıyla kaydedildi!")
            if veresiye_tutar > 0:
                print(f"  Müşteri borcuna {veresiye_tutar:.2f} TL eklendi.")
        else:
            print("\n  [HATA] Satış kaydedilemedi!")

    # ─────────────────────────────────────────
    #  Transaction ile Satış Kaydet
    # ─────────────────────────────────────────

    def _satisi_kaydet(self, sepet, musteri_id, kullanici_id,
                       toplam_tutar, odenen_tutar, veresiye_tutar,
                       odeme_turu, tarih) -> bool:
        """
        Tüm satış işlemlerini tek transaction içinde yapar.
        Herhangi biri başarısız olursa tümü geri alınır.
        """
        baglanti = self.db.baglan()
        try:
            imleç = baglanti.cursor()
            imleç.execute("BEGIN")

            # 1. Satış başlığı ekle
            imleç.execute(
                """
                INSERT INTO satislar
                    (musteri_id, kullanici_id, toplam_tutar, odenen_tutar, odeme_turu, satis_tarihi)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (musteri_id, kullanici_id, toplam_tutar, odenen_tutar, odeme_turu, tarih)
            )
            satis_id = imleç.lastrowid

            for kalem in sepet:
                # 2. Satış kalemi ekle
                imleç.execute(
                    """
                    INSERT INTO satis_kalemleri
                        (satis_id, urun_id, miktar, birim_fiyat, toplam_fiyat)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (satis_id, kalem["urun_id"], kalem["miktar"],
                     kalem["birim_fiyat"], kalem["toplam_fiyat"])
                )

                # 3. Stok düş
                imleç.execute(
                    "UPDATE urunler SET stok = stok - ? WHERE id = ?",
                    (kalem["miktar"], kalem["urun_id"])
                )

                # 4. Stok hareketi kaydet
                imleç.execute(
                    """
                    INSERT INTO stok_hareketleri
                        (urun_id, hareket_turu, miktar, aciklama, hareket_tarihi)
                    VALUES (?, 'satis', ?, ?, ?)
                    """,
                    (kalem["urun_id"], -kalem["miktar"],
                     f"Satış #{satis_id}", tarih)
                )

            # 5. Veresiye varsa müşteri borcunu güncelle
            if veresiye_tutar > 0 and musteri_id:
                imleç.execute(
                    "UPDATE musteriler SET borc_bakiyesi = borc_bakiyesi + ? WHERE id = ?",
                    (veresiye_tutar, musteri_id)
                )

                # 6. Cari hareket kaydet
                imleç.execute(
                    """
                    INSERT INTO cari_hareketler
                        (musteri_id, islem_turu, tutar, aciklama, islem_tarihi)
                    VALUES (?, 'borclandirma', ?, ?, ?)
                    """,
                    (musteri_id, veresiye_tutar, f"Satış #{satis_id}", tarih)
                )

            baglanti.commit()
            return True

        except Exception as hata:
            baglanti.rollback()
            print(f"[HATA] Transaction geri alındı: {hata}")
            return False
        finally:
            baglanti.close()

    # ─────────────────────────────────────────
    #  Satışları Listele
    # ─────────────────────────────────────────

    def satislari_listele(self) -> None:
        """Son satışları listeler."""
        if not self._yetki_kontrol("satis_listele"):
            return

        satislar = self.db.tum_kayitlari_getir(
            """
            SELECT s.id, m.ad_soyad, k.kullanici_adi,
                   s.toplam_tutar, s.odenen_tutar, s.odeme_turu,
                   s.satis_tarihi, s.iptal
            FROM satislar s
            LEFT JOIN musteriler m ON s.musteri_id = m.id
            JOIN kullanicilar k    ON s.kullanici_id = k.id
            ORDER BY s.satis_tarihi DESC
            LIMIT 50
            """
        )

        if not satislar:
            print("\nSatış kaydı bulunamadı.")
            return

        print("\n" + "=" * 90)
        print(f"{'ID':<5} {'Müşteri':<20} {'Personel':<12} {'Toplam':>9} {'Ödenen':>9} {'Tür':<10} {'Tarih':<20} {'Durum'}")
        print("=" * 90)

        for s in satislar:
            durum    = "İPTAL" if s["iptal"] else "Aktif"
            musteri  = s["ad_soyad"] or "Müşterisiz"
            print(
                f"{s['id']:<5} {musteri:<20} {s['kullanici_adi']:<12} "
                f"{s['toplam_tutar']:>9.2f} {s['odenen_tutar']:>9.2f} "
                f"{s['odeme_turu']:<10} {s['satis_tarihi']:<20} {durum}"
            )

        print("=" * 90)

    # ─────────────────────────────────────────
    #  Satış Detayı
    # ─────────────────────────────────────────

    def satis_detayi(self) -> None:
        """Seçilen satışın kalemlerini gösterir."""
        if not self._yetki_kontrol("satis_listele"):
            return

        try:
            satis_id = int(input("Satış ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return

        satis = self.db.tek_kayit_getir(
            """
            SELECT s.*, m.ad_soyad, k.kullanici_adi
            FROM satislar s
            LEFT JOIN musteriler m ON s.musteri_id = m.id
            JOIN kullanicilar k    ON s.kullanici_id = k.id
            WHERE s.id = ?
            """,
            (satis_id,)
        )

        if not satis:
            print("[HATA] Satış bulunamadı!")
            return

        kalemleri = self.db.tum_kayitlari_getir(
            """
            SELECT p.ad, sk.miktar, sk.birim_fiyat, sk.toplam_fiyat
            FROM satis_kalemleri sk
            JOIN urunler p ON sk.urun_id = p.id
            WHERE sk.satis_id = ?
            """,
            (satis_id,)
        )

        print(f"\n{'='*50}")
        print(f"  Satış No  : #{satis['id']}")
        print(f"  Müşteri   : {satis['ad_soyad'] or 'Müşterisiz'}")
        print(f"  Personel  : {satis['kullanici_adi']}")
        print(f"  Tarih     : {satis['satis_tarihi']}")
        print(f"  Ödeme türü: {satis['odeme_turu']}")
        print(f"{'─'*50}")
        print(f"  {'Ürün':<25} {'Adet':>5} {'Birim':>9} {'Toplam':>9}")
        print(f"{'─'*50}")

        for k in kalemleri:
            print(f"  {k['ad']:<25} {k['miktar']:>5} {k['birim_fiyat']:>9.2f} {k['toplam_fiyat']:>9.2f}")

        print(f"{'─'*50}")
        print(f"  {'TOPLAM':<25} {'':>5} {'':>9} {satis['toplam_tutar']:>9.2f} TL")
        print(f"  {'ÖDENEN':<25} {'':>5} {'':>9} {satis['odenen_tutar']:>9.2f} TL")
        veresiye = satis["toplam_tutar"] - satis["odenen_tutar"]
        if veresiye > 0:
            print(f"  {'VERESİYE':<25} {'':>5} {'':>9} {veresiye:>9.2f} TL")
        print(f"{'='*50}")

    # ─────────────────────────────────────────
    #  Satış İptali
    # ─────────────────────────────────────────

    def satis_iptal(self) -> None:
        """
        Satışı iptal eder:
        - Stok geri ekler
        - Veresiye borcu geri alır
        - Satışı iptal olarak işaretler
        """
        if not self._yetki_kontrol("satis_iptal"):
            return

        try:
            satis_id = int(input("İptal edilecek satış ID: ").strip())
        except ValueError:
            print("[HATA] Geçerli bir ID girin!")
            return

        satis = self.db.tek_kayit_getir(
            "SELECT * FROM satislar WHERE id = ? AND iptal = 0", (satis_id,)
        )
        if not satis:
            print("[HATA] Satış bulunamadı veya zaten iptal edilmiş!")
            return

        kalemleri = self.db.tum_kayitlari_getir(
            "SELECT * FROM satis_kalemleri WHERE satis_id = ?", (satis_id,)
        )

        onay = input(f"Satış #{satis_id} iptal edilsin mi? (e/h): ").strip().lower()
        if onay != "e":
            print("  İşlem iptal edildi.")
            return

        tarih    = self._tarih()
        baglanti = self.db.baglan()

        try:
            imleç = baglanti.cursor()
            imleç.execute("BEGIN")

            # Satışı iptal işaretle
            imleç.execute(
                "UPDATE satislar SET iptal = 1 WHERE id = ?", (satis_id,)
            )

            for kalem in kalemleri:
                # Stok geri ekle
                imleç.execute(
                    "UPDATE urunler SET stok = stok + ? WHERE id = ?",
                    (kalem["miktar"], kalem["urun_id"])
                )
                # İade stok hareketi kaydet
                imleç.execute(
                    """
                    INSERT INTO stok_hareketleri
                        (urun_id, hareket_turu, miktar, aciklama, hareket_tarihi)
                    VALUES (?, 'iade', ?, ?, ?)
                    """,
                    (kalem["urun_id"], kalem["miktar"],
                     f"Satış iptali #{satis_id}", tarih)
                )

            # Veresiye borcu geri al
            veresiye = satis["toplam_tutar"] - satis["odenen_tutar"]
            if veresiye > 0 and satis["musteri_id"]:
                imleç.execute(
                    "UPDATE musteriler SET borc_bakiyesi = borc_bakiyesi - ? WHERE id = ?",
                    (veresiye, satis["musteri_id"])
                )
                imleç.execute(
                    """
                    INSERT INTO cari_hareketler
                        (musteri_id, islem_turu, tutar, aciklama, islem_tarihi)
                    VALUES (?, 'iade', ?, ?, ?)
                    """,
                    (satis["musteri_id"], veresiye,
                     f"Satış iptali #{satis_id}", tarih)
                )

            baglanti.commit()
            print(f"\n  ✓ Satış #{satis_id} iptal edildi. Stoklar geri yüklendi.")

        except Exception as hata:
            baglanti.rollback()
            print(f"[HATA] İptal işlemi geri alındı: {hata}")
        finally:
            baglanti.close()


# ─────────────────────────────────────────────
#  Modül doğrudan çalıştırıldığında test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    from auth import GirisSistemi

    db    = Veritabani("data/mini_erp.db")
    giris = GirisSistemi(db)

    if giris.giris_yap():
        sy = SatisYoneticisi(db, giris)

        while True:
            print("\n====== SATIŞ İŞLEMLERİ ======")
            print("1 - Satış yap")
            print("2 - Satışları listele")
            print("3 - Satış detayı")
            print("4 - Satış iptal")
            print("0 - Çıkış")

            secim = input("\nSeçiminiz: ").strip()

            if secim == "1":
                sy.satis_yap()
            elif secim == "2":
                sy.satislari_listele()
            elif secim == "3":
                sy.satis_detayi()
            elif secim == "4":
                sy.satis_iptal()
            elif secim == "0":
                giris.cikis_yap()
                break
            else:
                print("[HATA] Geçersiz seçim!")