import socket
import random
import string
import json
from aes_core import encrypt, decrypt

def generate_session_key():
    # Membuat Session Key (Ks) acak sepanjang 16 karakter (128 bit)
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(16))

def start_kdc():
    print("=== STARTING KDC SERVER ===")
    
    # KDC meminta input port agar interaktif (sesuai instruksi tugas)
    port = int(input("Masukkan port untuk menjalankan KDC (misal: 5000): "))

    # Tambahkan input key dinamis di sini
    ka = input("Masukkan Master Key Alice (Ka): ")
    kb = input("Masukkan Master Key Bob (Kb): ")
    
    # Inisialisasi Socket (0.0.0.0 agar bisa diakses dari IP jaringan manapun)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(5)
    
    print(f"\n[KDC] KDC berjalan. Menunggu permintaan dari Initiator (Alice) di port {port}...")
    
    while True:
        conn, addr = server_socket.accept()
        with conn:
            print(f"\n[KDC] Terhubung dengan Initiator di: {addr}")
            
            # --- LANGKAH 1: Menerima (IDA || IDB || N1) dari Alice ---
            data_terima = conn.recv(4096).decode('utf-8')
            if not data_terima:
                continue
                
            print(f"[KDC] (Langkah 1) Menerima pesan: {data_terima}")
            
            # Mem-parsing pesan dari Alice
            try:
                pesan_alice = json.loads(data_terima)
                id_a = pesan_alice['ida']
                id_b = pesan_alice['idb']
                n1 = pesan_alice['n1']
                print(f"[KDC] Parsing berhasil -> IDA: {id_a}, IDB: {id_b}, N1: {n1}")
            except Exception as e:
                print(f"[KDC] Format pesan Langkah 1 tidak valid. Error: {e}")
                continue

            # KDC membuat Session Key (Ks) baru
            ks = generate_session_key()
            print(f"\n[KDC] Men-generate Session Key (Ks): {ks}")
            
            # --- LANGKAH 2: Mengirim Balasan ke Alice ---
            # Bagian untuk Bob: E(Kb, [Ks || IDA])
            tiket_bob_plaintext = json.dumps({"ks": ks, "ida": id_a})
            tiket_bob_encrypted = encrypt(tiket_bob_plaintext, kb)
            
            # Bagian untuk Alice: E(Ka, [Ks || IDA || IDB || N1 || Tiket_Bob_Encrypted])
            # Tiket Bob ditaruh di dalam tiket Alice
            pesan_untuk_alice_plaintext = json.dumps({
                "ks": ks,
                "ida": id_a,
                "idb": id_b,
                "n1": n1,
                "tiket_bob": tiket_bob_encrypted
            })
            
            # Enkripsi seluruh paket untuk Alice menggunakan Ka
            pesan_final_encrypted = encrypt(pesan_untuk_alice_plaintext, ka)
            
            print("[KDC] (Langkah 2) Mengirim balasan terenkripsi AES ke Alice...")
            print(f"[KDC] Ciphertext (Hex): {pesan_final_encrypted[:60]}... (dipotong untuk tampilan)")
            
            # Kirim kembali ke Alice
            conn.sendall(pesan_final_encrypted.encode('utf-8'))
            print("[KDC] Selesai melayani permintaan ini.\n")

if __name__ == "__main__":
    start_kdc()
