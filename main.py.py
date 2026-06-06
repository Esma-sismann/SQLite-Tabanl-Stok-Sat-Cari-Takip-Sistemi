

from database import Veritabani, veritabanini_kur
from auth import GirisSistemi
from product_manager import UrunYoneticisi
from customer_manager import MusteriYoneticisi
from supplier_manager import TedarikciYoneticisi
from stock_manager import StokYoneticisi
from sales_manager import SatisYoneticisi
from payment_manager import OdemeYoneticisi
from report_manager import RaporYoneticisi
from file_manager import DosyaYoneticisi



DB_YOLU = "data/mini_erp.db"



def baslik_yazdir() -> None:
    print("\n" + "=" * 45)
    print("      MiniERP - İşletme Yönetim Sistemi")
    print("=" * 45)


def kritik_stok_uyarisi(urun_ym: UrunYoneticisi) -> None:
    """Ana menü açılışında kritik stok varsa uyarı gösterir."""
    urunler = urun_ym.kritik_stok_listele()
    if urunler:
        input("\n  Devam etmek için Enter'a basın...")




def urun_menu(urun_ym: UrunYoneticisi, dosya_ym: DosyaYoneticisi) -> None:
    while True:
        print("\n====== ÜRÜN İŞLEMLERİ ======")
        print("1 - Ürün ekle")
        print("2 - Ürünleri listele")
        print("3 - Ürün güncelle")
        print("4 - Ürün sil")
        print("5 - Kritik stok listesi")
        print("6 - Kategori özeti")
        print("0 - Ana menüye dön")

        secim = input("\nSeçiminiz: ").strip()

        if secim == "1":
            urun_ym.urun_ekle()
            dosya_ym.log_yaz("Ürün eklendi.")
        elif secim == "2":
            urun_ym.urunleri_listele()
        elif secim == "3":
            urun_ym.urun_guncelle()
            dosya_ym.log_yaz("Ürün güncellendi.")
        elif secim == "4":
            urun_ym.urun_sil()
            dosya_ym.log_yaz("Ürün silindi (pasif yapıldı).")
        elif secim == "5":
            urun_ym.kritik_stok_listele()
        elif secim == "6":
            urun_ym.kategorileri_listele()
        elif secim == "0":
            break
        else:
            print("[HATA] Geçersiz seçim!")


def musteri_menu(musteri_ym: MusteriYoneticisi, dosya_ym: DosyaYoneticisi) -> None:
    while True:
        print("\n====== MÜŞTERİ İŞLEMLERİ ======")
        print("1 - Müşteri ekle")
        print("2 - Müşterileri listele")
        print("3 - Müşteri güncelle")
        print("4 - Müşteri sil")
        print("5 - Müşteri borç detayı")
        print("0 - Ana menüye dön")

        secim = input("\nSeçiminiz: ").strip()

        if secim == "1":
            musteri_ym.musteri_ekle()
            dosya_ym.log_yaz("Müşteri eklendi.")
        elif secim == "2":
            musteri_ym.musterileri_listele()
        elif secim == "3":
            musteri_ym.musteri_guncelle()
            dosya_ym.log_yaz("Müşteri güncellendi.")
        elif secim == "4":
            musteri_ym.musteri_sil()
            dosya_ym.log_yaz("Müşteri silindi.")
        elif secim == "5":
            musteri_ym.musteri_borc_goruntule()
        elif secim == "0":
            break
        else:
            print("[HATA] Geçersiz seçim!")


def tedarikci_menu(tedarikci_ym: TedarikciYoneticisi, dosya_ym: DosyaYoneticisi) -> None:
    while True:
        print("\n====== TEDARİKÇİ İŞLEMLERİ ======")
        print("1 - Tedarikçi ekle")
        print("2 - Tedarikçileri listele")
        print("3 - Tedarikçi güncelle")
        print("4 - Tedarikçi sil")
        print("0 - Ana menüye dön")

        secim = input("\nSeçiminiz: ").strip()

        if secim == "1":
            tedarikci_ym.tedarikci_ekle()
            dosya_ym.log_yaz("Tedarikçi eklendi.")
        elif secim == "2":
            tedarikci_ym.tedarikcileri_listele()
        elif secim == "3":
            tedarikci_ym.tedarikci_guncelle()
            dosya_ym.log_yaz("Tedarikçi güncellendi.")
        elif secim == "4":
            tedarikci_ym.tedarikci_sil()
            dosya_ym.log_yaz("Tedarikçi silindi.")
        elif secim == "0":
            break
        else:
            print("[HATA] Geçersiz seçim!")


def stok_menu(stok_ym: StokYoneticisi, dosya_ym: DosyaYoneticisi) -> None:
    while True:
        print("\n====== STOK İŞLEMLERİ ======")
        print("1 - Stok girişi yap")
        print("2 - Stok durumunu listele")
        print("3 - Stok hareketlerini listele")
        print("4 - Manuel stok düzelt")
        print("0 - Ana menüye dön")

        secim = input("\nSeçiminiz: ").strip()

        if secim == "1":
            stok_ym.stok_giris()
            dosya_ym.log_yaz("Stok girişi yapıldı.")
        elif secim == "2":
            stok_ym.stok_durumu_listele()
        elif secim == "3":
            stok_ym.stok_hareketleri_listele()
        elif secim == "4":
            stok_ym.stok_duzelt()
            dosya_ym.log_yaz("Manuel stok düzeltmesi yapıldı.")
        elif secim == "0":
            break
        else:
            print("[HATA] Geçersiz seçim!")


def satis_menu(satis_ym: SatisYoneticisi, dosya_ym: DosyaYoneticisi) -> None:
    while True:
        print("\n====== SATIŞ İŞLEMLERİ ======")
        print("1 - Satış yap")
        print("2 - Satışları listele")
        print("3 - Satış detayı")
        print("4 - Satış iptal")
        print("0 - Ana menüye dön")

        secim = input("\nSeçiminiz: ").strip()

        if secim == "1":
            satis_ym.satis_yap()
            dosya_ym.log_yaz("Satış yapıldı.")
        elif secim == "2":
            satis_ym.satislari_listele()
        elif secim == "3":
            satis_ym.satis_detayi()
        elif secim == "4":
            satis_ym.satis_iptal()
            dosya_ym.log_yaz("Satış iptal edildi.")
        elif secim == "0":
            break
        else:
            print("[HATA] Geçersiz seçim!")


def odeme_menu(odeme_ym: OdemeYoneticisi, dosya_ym: DosyaYoneticisi) -> None:
    while True:
        print("\n====== ÖDEME / CARİ HESAP ======")
        print("1 - Ödeme al")
        print("2 - Cari hesap listesi")
        print("3 - Müşteri cari hareketleri")
        print("4 - Manuel borçlandırma")
        print("0 - Ana menüye dön")

        secim = input("\nSeçiminiz: ").strip()

        if secim == "1":
            odeme_ym.odeme_al()
            dosya_ym.log_yaz("Müşteriden ödeme alındı.")
        elif secim == "2":
            odeme_ym.cari_hesap_listele()
        elif secim == "3":
            odeme_ym.musteri_cari_hareketleri()
        elif secim == "4":
            odeme_ym.manuel_borclandir()
            dosya_ym.log_yaz("Manuel borçlandırma yapıldı.")
        elif secim == "0":
            break
        else:
            print("[HATA] Geçersiz seçim!")


def rapor_menu(rapor_ym: RaporYoneticisi) -> None:
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
        print("0  - Ana menüye dön")

        secim = input("\nSeçiminiz: ").strip()

        if secim == "1":
            rapor_ym.gunluk_satis_raporu()
        elif secim == "2":
            rapor_ym.aylik_satis_raporu()
        elif secim == "3":
            rapor_ym.en_cok_satilan_urunler()
        elif secim == "4":
            rapor_ym.musteri_borc_raporu()
        elif secim == "5":
            rapor_ym.kritik_stok_raporu()
        elif secim == "6":
            rapor_ym.kategori_satis_raporu()
        elif secim == "7":
            rapor_ym.personel_satis_raporu()
        elif secim == "8":
            rapor_ym.musteri_alisveris_gecmisi()
        elif secim == "9":
            rapor_ym.en_yuksek_cirolu_urunler()
        elif secim == "0":
            break
        else:
            print("[HATA] Geçersiz seçim!")


def dosya_menu(dosya_ym: DosyaYoneticisi) -> None:
    while True:
        print("\n====== DOSYA İŞLEMLERİ ======")
        print("1 - Satış raporunu aktar")
        print("2 - Stok raporunu aktar")
        print("3 - Müşteri borç raporunu aktar")
        print("4 - Tüm raporları aktar")
        print("5 - Sistem loglarını gör")
        print("0 - Ana menüye dön")

        secim = input("\nSeçiminiz: ").strip()

        if secim == "1":
            dosya_ym.satis_raporu_aktar()
        elif secim == "2":
            dosya_ym.stok_raporu_aktar()
        elif secim == "3":
            dosya_ym.musteri_borc_raporu_aktar()
        elif secim == "4":
            dosya_ym.tum_raporlari_aktar()
        elif secim == "5":
            dosya_ym.log_goruntule()
        elif secim == "0":
            break
        else:
            print("[HATA] Geçersiz seçim!")


def kullanici_menu(giris: GirisSistemi, dosya_ym: DosyaYoneticisi) -> None:
    while True:
        print("\n====== KULLANICI İŞLEMLERİ ======")
        print("1 - Kullanıcıları listele")
        print("2 - Yeni kullanıcı ekle")
        print("3 - Şifre değiştir")
        print("0 - Ana menüye dön")

        secim = input("\nSeçiminiz: ").strip()

        if secim == "1":
            giris.kullanicilari_listele()
        elif secim == "2":
            giris.kullanici_ekle()
            dosya_ym.log_yaz("Yeni kullanıcı eklendi.")
        elif secim == "3":
            giris.sifre_degistir()
            dosya_ym.log_yaz("Şifre değiştirildi.")
        elif secim == "0":
            break
        else:
            print("[HATA] Geçersiz seçim!")



def ana_menu(
    giris:       GirisSistemi,
    urun_ym:     UrunYoneticisi,
    musteri_ym:  MusteriYoneticisi,
    tedarikci_ym:TedarikciYoneticisi,
    stok_ym:     StokYoneticisi,
    satis_ym:    SatisYoneticisi,
    odeme_ym:    OdemeYoneticisi,
    rapor_ym:    RaporYoneticisi,
    dosya_ym:    DosyaYoneticisi,
) -> None:

  
    kritik_stok_uyarisi(urun_ym)

    while True:
        baslik_yazdir()
        rol = giris.aktif_kullanici["rol"]
        kullanici = giris.aktif_kullanici["kullanici_adi"]
        print(f"  Kullanıcı: {kullanici} ({rol})")
        print("=" * 45)
        print("1 - Ürün İşlemleri")
        print("2 - Müşteri İşlemleri")
        print("3 - Tedarikçi İşlemleri")
        print("4 - Stok İşlemleri")
        print("5 - Satış Yap")
        print("6 - Ödeme Al / Cari Hesap")
        print("7 - Raporlar")
        print("8 - Verileri Dosyaya Aktar")
        if rol == "admin":
            print("9 - Kullanıcı İşlemleri")
        print("0 - Çıkış")

        secim = input("\nSeçiminiz: ").strip()

        if secim == "1":
            urun_menu(urun_ym, dosya_ym)
        elif secim == "2":
            musteri_menu(musteri_ym, dosya_ym)
        elif secim == "3":
            tedarikci_menu(tedarikci_ym, dosya_ym)
        elif secim == "4":
            stok_menu(stok_ym, dosya_ym)
        elif secim == "5":
            satis_menu(satis_ym, dosya_ym)
        elif secim == "6":
            odeme_menu(odeme_ym, dosya_ym)
        elif secim == "7":
            rapor_menu(rapor_ym)
        elif secim == "8":
            dosya_menu(dosya_ym)
        elif secim == "9" and rol == "admin":
            kullanici_menu(giris, dosya_ym)
        elif secim == "0":
            dosya_ym.log_yaz("Sistemden çıkış yapıldı.")
            giris.cikis_yap()
            print("\n  Program kapatılıyor...\n")
            break
        else:
            print("[HATA] Geçersiz seçim!")




def main() -> None:
    # Veritabanı kur
    db = Veritabani(DB_YOLU)
    veritabanini_kur(db)

 
    giris        = GirisSistemi(db)
    dosya_ym     = DosyaYoneticisi(db, giris)

    # Giriş dene (3 hak)
    giris_hakki = 3
    giris_basarili = False

    for deneme in range(giris_hakki):
        kalan = giris_hakki - deneme
        if deneme > 0:
            print(f"\n  Kalan deneme hakkı: {kalan}")

        if giris.giris_yap():
            giris_basarili = True
            dosya_ym.log_yaz("Sisteme giriş yapıldı.")
            break
        elif deneme < giris_hakki - 1:
            print("  Tekrar deneyin.")

    if not giris_basarili:
        print("\n  3 hatalı giriş denemesi. Program kapatılıyor.")
        dosya_ym.log_yaz("3 hatalı giriş denemesi - erişim reddedildi.")
        return

    urun_ym      = UrunYoneticisi(db, giris)
    musteri_ym   = MusteriYoneticisi(db, giris)
    tedarikci_ym = TedarikciYoneticisi(db, giris)
    stok_ym      = StokYoneticisi(db, giris)
    satis_ym     = SatisYoneticisi(db, giris)
    odeme_ym     = OdemeYoneticisi(db, giris)
    rapor_ym     = RaporYoneticisi(db, giris)

    ana_menu(
        giris, urun_ym, musteri_ym, tedarikci_ym,
        stok_ym, satis_ym, odeme_ym, rapor_ym, dosya_ym
    )


if __name__ == "__main__":
    main()