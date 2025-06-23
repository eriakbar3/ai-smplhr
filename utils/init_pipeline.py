def pipeline():
    data =  [
                {
                    "step": 1,
                    "type": "generate",
                    "message": "Memulai proses identifikasi kebutuhan dan kualifikasi yang spesifik untuk posisi IT Programmer Python yang Anda cari.",
                    "is_done": False,
                    "title": "Identifikasi Kebutuhan IT Programmer Python"
                },
                {
                    "step": 2,
                    "type": "filter",
                    "message": "Melakukan penyaringan awal terhadap CV dan profil kandidat yang sesuai dengan kriteria IT Programmer Python.",
                    "is_done": False,
                    "title": "Penyaringan Kandidat Awal"
                },
                {
                    "step": 3,
                    "type": "recommend",
                    "message": "Mempresentasikan daftar kandidat IT Programmer Python yang paling relevan dan memenuhi syarat untuk dipertimbangkan lebih lanjut.",
                    "is_done": False,
                    "title": "Rekomendasi Kandidat Terpilih"
                },
                {
                    "step": 4,
                    "type": "schedule",
                    "message": "Menjadwalkan sesi wawancara dan/atau tes teknis dengan kandidat IT Programmer Python yang telah direkomendasikan.",
                    "is_done": False,
                    "title": "Penjadwalan Wawancara & Tes"
                },
                {
                    "step": 5,
                    "type": "assess",
                    "message": "Melakukan penilaian mendalam terhadap kemampuan teknis dan soft skill kandidat IT Programmer Python melalui wawancara dan studi kasus.",
                    "is_done": False,
                    "title": "Penilaian & Evaluasi Kandidat"
                },
                {
                    "step": 6,
                    "type": "offer",
                    "message": "Menyiapkan dan menyampaikan tawaran pekerjaan kepada kandidat IT Programmer Python terpilih yang paling sesuai.",
                    "is_done": False,
                    "title": "Pemberian Penawaran Kerja"
                }
            ]
    return data