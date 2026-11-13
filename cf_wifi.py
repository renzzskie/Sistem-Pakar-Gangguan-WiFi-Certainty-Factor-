import json
import os
import sys

AMBANG_TAMPIL = 0.2


def muat_kb(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def baca_cf(teks):
    while True:
        s = input(teks).strip().replace(",", ".")
        try:
            v = float(s)
            if -1.0 <= v <= 1.0:
                return v
        except ValueError:
            pass
        print("   Masukkan angka -1 sampai 1 (contoh -1, 0, 0.4, 0.8, 1).")


def tanya_fakta(kb):
    print("Jawab dengan tingkat keyakinan Anda (skala istilah, -1 sampai 1):")
    print("  1 = pasti | 0.8 = hampir pasti | 0.6 = kemungkinan besar | 0.4 = mungkin")
    print("  0 = belum tahu | -0.4 = mungkin tidak | -0.8 = hampir pasti tidak | -1 = pasti tidak\n")
    fakta = {}
    for i, (fid, pertanyaan) in enumerate(kb["fakta"].items(), 1):
        fakta[fid] = baca_cf(f"{i}. {pertanyaan} > ")
    return fakta


def cf_premis(aturan, cf):
    nilai = [cf.get(k, 0.0) for k in aturan["jika"]]
    return min(nilai) if aturan["mode"] == "dan" else max(nilai)


def gabung(cf_lama, cf_baru):
    return cf_lama + cf_baru * (1 - cf_lama)


def inferensi(kb, fakta):
    aturan = kb["aturan"]
    turunan = {a["maka"] for a in aturan}
    cf = dict(fakta)
    for h in turunan:
        cf[h] = 0.0
    jejak = {}
    for _ in range(len(aturan) + 1):
        baru, jejak = dict(cf), {}
        for h in turunan:
            nilai, dipakai = 0.0, []
            for a in aturan:
                if a["maka"] != h:
                    continue
                p = cf_premis(a, cf)
                if p <= 0:
                    continue
                hasil = p * a["cf"]
                nilai = gabung(nilai, hasil)
                dipakai.append((a, p, hasil))
            baru[h], jejak[h] = nilai, dipakai
        selesai = all(abs(baru[h] - cf[h]) < 1e-9 for h in turunan)
        cf = baru
        if selesai:
            break
    return cf, jejak


def jelaskan(kb, h, cf, jejak, tab=2):
    label = kb["hipotesis"][h]["label"]
    for a, p, hasil in jejak[h]:
        print(" " * tab + f"{label} <- {a['id']} [{', '.join(a['sumber'])}] "
              f"(premis {p:.2f} x CF aturan {a['cf']} = {hasil:.3f})")
        for k in a["jika"]:
            if k in kb["hipotesis"]:
                if cf[k] > 0:
                    jelaskan(kb, k, cf, jejak, tab + 4)
            elif cf[k] > 0:
                print(" " * (tab + 4) + f"fakta: {kb['fakta'][k].rstrip('?')} (CF {cf[k]})")


def tingkat(v):
    if v >= 0.9:
        return "pasti"
    if v >= 0.7:
        return "hampir pasti"
    if v >= 0.5:
        return "kemungkinan besar"
    return "mungkin"


def tampilkan(kb, cf, jejak):
    akhir = [h for h, d in kb["hipotesis"].items() if d["akhir"] and cf[h] > AMBANG_TAMPIL]
    akhir.sort(key=lambda h: cf[h], reverse=True)
    print("\n=== HASIL DIAGNOSIS ===")
    if not akhir:
        print("Belum dapat dikatakan: bukti belum cukup untuk menyimpulkan apa pun.")
    for h in akhir:
        d = kb["hipotesis"][h]
        print(f"\nKesimpulan: {d['label']} -> {tingkat(cf[h])} (CF kira-kira {cf[h]:.2f})")
        print("Alasan:")
        jelaskan(kb, h, cf, jejak)
        print(f"Saran: {d['saran']}")
    print("\nSumber:")
    for k, v in kb["sumber"].items():
        print(f"  {k}: {v}")
    print(f"\nCatatan: {kb['batas']}")


def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kb_wifi.json")
    if len(sys.argv) > 1:
        path = sys.argv[1]
    kb = muat_kb(path)
    print(kb["judul"] + "\n")
    fakta = tanya_fakta(kb)
    cf, jejak = inferensi(kb, fakta)
    tampilkan(kb, cf, jejak)


if __name__ == "__main__":
    main()