# 🎵 Lyric Widget

Desktop audio-synced lyrics overlay untuk Linux dengan dukungan **Multi-Source Lyrics Engine**, transliterasi **Romaji Jepang**, pemisahan **Lead & Backing Vocals**, dan panel gradasi estetis.

![Lyric Widget Preview](assets/preview.png)

---

## 🛠️ Teknologi & Spesifikasi Sistem

| Komponen | Teknologi | Keterangan |
| :--- | :--- | :--- |
| **Sistem Operasi** | **Linux** (KDE Plasma 6 pada Wayland / X11) | Diuji pada Fedora Linux, kompatibel dengan semua distro KDE 6 |
| **Frontend / UI** | **QML, QtQuick, Qt 6, KDE Kirigami** | Tampilan native, ringan, hardware-accelerated |
| **Protokol Audio** | **MPRIS 2.0 (D-Bus)** | Sinkronisasi pemutar: Spotify, Strawberry, VLC, Browser (YouTube Music), dll. |
| **Mesin Lirik** | **Multi-Source API** (LRCLIB, NetEase, KuGou) | Fallback 3 tingkat otomatis, 100% gratis, tanpa API key |
| **Transliterasi** | **Hepburn Kana-to-Romaji Engine** | Otomatis mengubah Hiragana & Katakana ke huruf alfabet |
| **Versi Standalone** | **Python 3.10+, PySide6 (Qt 6 for Python)** | Mode overlay mandiri untuk desktop non-KDE |

---

## 📦 Panduan Instalasi

### 1. Pemasangan Plasmoid (KDE Plasma 6 Desktop Widget)

> **Rekomendasi Utama**: Mode plasmoid berjalan native langsung di dalam KDE Plasma Shell, sangat hemat memori, dan otomatis aktif setiap kali desktop menyala.

👉 **[📥 Klik di Sini untuk Mengunduh `lyric-widget.plasmoid`](https://github.com/rayyanqatrunada/Lyric-widget/raw/main/lyric-widget.plasmoid)**

#### Cara A: Melalui Menu Pengaturan Desktop (GUI)
1. Unduh file **[`lyric-widget.plasmoid`](https://github.com/rayyanqatrunada/Lyric-widget/raw/main/lyric-widget.plasmoid)**.
2. Klik kanan pada area kosong di Desktop Anda > pilih **Add Widgets...** (Tambah Widget).
3. Klik tombol **Get New Widgets...** di pojok bawah > pilih **Install from Local File...**.
4. Arahkan dan pilih file `lyric-widget.plasmoid` yang telah diunduh.
5. Tarik (*drag & drop*) **Lyric Widget** ke layar desktop Anda.

#### Cara B: Melalui Terminal (CLI)
```bash
# 1. Pasang widget ke sistem Plasma
kpackagetool6 -t Plasma/Applet -i lyric-widget.plasmoid

# 2. Jika melakukan pembaruan (upgrade) di kemudian hari
kpackagetool6 -t Plasma/Applet -u lyric-widget.plasmoid

# 3. Muat ulang Plasma Shell untuk menerapkan
systemctl --user restart plasma-plasmashell
```

---

### 2. Versi Standalone (Aplikasi Desktop Mandiri)

> 💡 **Catatan & Cara Kerja Standalone:**  
> Versi Standalone adalah aplikasi Python independen yang berjalan di atas jendela transparan (*click-through frameless overlay*). Versi ini ditujukan untuk pengguna Linux yang **tidak menggunakan KDE Plasma** (seperti GNOME, XFCE, Hyprland, Sway, i3, dsb.) atau untuk pengujian lirik tanpa memodifikasi desktop environment.

```bash
# 1. Masuk ke direktori standalone
cd standalone

# 2. Pasang dependensi Python
pip install -r requirements.txt

# 3. Jalankan aplikasi overlay
python main_ui.py
```

*Mode Simulasi / Pengujian Cepat (Mock Mode):*
```bash
python main_ui.py --mock-transition   # Demo pergantian lirik otomatis
python main_ui.py --mock-japanese     # Demo lirik bahasa Jepang & Romaji
```

---

## ⚙️ Cara Kerja & Fitur Utama

- **Sinkronisasi Presisi MPRIS 2.0 Realtime**  
  Widget membaca posisi waktu lagu setiap 35ms langsung melalui D-Bus MPRIS 2.0. Pergantian baris lirik dianimasikan secara halus (*fade & vertical slide*).

- **Multi-Source Lyrics Engine (3-Tier Fallback)**  
  Menggunakan rantai pencarian otomatis bertingkat:  
  1. **LRCLIB**: Pencarian spesifik durasi & global query.  
  2. **NetEase Cloud Music**: Database lirik raksasa (>40 juta lagu, sangat kaya lagu Barat, Asia, J-Pop/Anime, dan Indonesia).  
  3. **KuGou Music**: Jaring pengaman cadangan format LRC ber-timestamp.  
  *Jika satu penyedia mengalami gangguan jaringan/503, sistem otomatis mengambil dari sumber berikutnya.*

- **Pembersihan Judul YouTube Music Otomatis**  
  Secara cerdas membuang label video seperti `(Official Music Video)`, `[MV]`, `(Audio)`, atau format `Artis - Judul` agar pencarian lirik di API selalu akurat.

- **Grace Period 30 Detik & Kompatibilitas Browser**  
  Saat memutar musik via browser (YouTube Music), widget **tidak akan berkedip atau hilang** saat jeda transisi antar-lagu. Widget tetap tampil saat musik di-pause, dan memberikan tenggat 30 detik sebelum memudar jika musik dihentikan.

- **Pemisahan Lead & Backing Vocals Bersih**  
  Mendeteksi vokal latar secara otomatis dari tanda kurung lirik `(...)` dan memformatnya dengan tipografi sekunder yang rapi tanpa teks prefix `(Backing)` yang mengganggu.

- **Transliterasi Romaji Jepang Realtime**  
  Mendeteksi karakter Kana (Hiragana & Katakana) dan langsung menampilkan teks ejaan Romaji Hepburn di bawah baris lirik asli.

- **Gradasi Estetis & Background Bleed**  
  Panel gradasi halus dengan posisi puncak kepekatan yang dapat digeser (*Peak Position* di kiri, tengah, atau kanan), opacity 0–100%, serta fitur *Bleed* agar latar belakang hitam dapat melebar ke atas/bawah melewati outline widget.

- **Slider Ketinggian Judul & Tipografi Lengkap**  
  Tersedia slider *Title Top Position* untuk mengatur letak vertikal judul lagu secara bebas, serta menu dropdown pemilihan font yang rapi dan responsif.

- **Tombol Refresh Cepat & Context Menu**  
  Ikon tombol refresh melayang di sudut atas panel yang muncul saat hover (lengkap dengan animasi putar saat memuat lirik), serta opsi **Refresh Lyrics** saat klik kanan pada widget.

---

## 📜 Lisensi
Didistribusikan di bawah lisensi **GPL-3.0**. Silakan gunakan, modifikasi, dan kembangkan secara bebas.
