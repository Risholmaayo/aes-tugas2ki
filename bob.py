import socket
import json
import threading
import sys
import random
from aes_core import encrypt, decrypt

IDB = "BOB_123"

# Variabel Global untuk Chat
session_key = None
chat_active = False

def receive_messages(conn):
    global chat_active, session_key
    while chat_active:
        try:
            data = conn.recv(4096).decode('utf-8')
            if not data:
                break
            
            # Mendekripsi pesan masuk menggunakan Session Key
            plaintext = decrypt(data, session_key)
            print(f"\n[Alice] (Encrypted: {data[:20]}...) -> {plaintext}")
            print("[Anda]: ", end="", flush=True)
        except Exception:
            print("\n[Bob] Koneksi chat terputus.")
            break

def start_bob():
    global session_key, chat_active
    
    print("=== STARTING BOB (RESPONDER) ===")
    port = int(input("Masukkan port untuk menjalankan Bob (misal: 6000): "))

    kb = input("Masukkan Master Key Bob (Kb): ")
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(1)
    
    print(f"\n[Bob] Bob berjalan. Menunggu kedatangan Alice di port {port}...")
    conn, addr = server_socket.accept()
    
    with conn:
        print(f"\n[Bob] Alice terhubung dari: {addr}")
        
        # --- LANGKAH 3: Menerima Tiket Bob dari Alice ---
        data_terima = conn.recv(4096).decode('utf-8')
        print(f"[Bob] (Langkah 3) Menerima tiket: {data_terima[:50]}...")
        
        try:
            # Bob mendekripsi tiket menggunakan Master Key miliknya (Kb)
            tiket_plaintext = decrypt(data_terima, kb)
            tiket_data = json.loads(tiket_plaintext)
            session_key = tiket_data['ks']
            id_a_klaim = tiket_data['ida']
            
            print(f"[Bob] Tiket berhasil dibongkar!")
            print(f"      - ID Alice tertera: {id_a_klaim}")
            print(f"      - Session Key (Ks) tersimpan: {session_key}")
        except Exception as e:
            print(f"[Bob] Gagal mendekripsi tiket Langkah 3. Master Key salah? Error: {e}")
            return

        # --- LANGKAH 4: Bob Menantang Alice (N2) ---
        n2 = str(random.randint(1000, 9999))
        print(f"\n[Bob] (Langkah 4) Membuat tantangan N2: {n2}")
        
        # Enkripsi N2 dengan Session Key (Ks)
        tantangan_encrypted = encrypt(n2, session_key)
        conn.sendall(tantangan_encrypted.encode('utf-8'))
        print("[Bob] Tantangan terkirim ke Alice.")
        
        # --- LANGKAH 5: Memverifikasi Balasan f(N2) dari Alice ---
        balasan_encrypted = conn.recv(4096).decode('utf-8')
        balasan_plaintext = decrypt(balasan_encrypted, session_key)
        
        # Fungsi f(N2) yang kita sepakati: N2 - 1
        expected_f_n2 = str(int(n2) - 1)
        
        print(f"[Bob] (Langkah 5) Menerima balasan f(N2): {balasan_plaintext}")
        if balasan_plaintext == expected_f_n2:
            print("[Bob] VERIFIKASI BERHASIL! Identitas Alice dikonfirmasi.")
            chat_active = True
        else:
            print("[Bob] VERIFIKASI GAGAL! Kunci tidak cocok. Memutuskan koneksi.")
            return
            
        # --- FASE CHATTING ---
        print("\n" + "="*40)
        print("KONEKSI AMAN ESTABLISHED DENGAN AES")
        print("Silakan mulai mengobrol. Ketik 'exit' untuk keluar.")
        print("="*40 + "\n")
        
        # Thread agar Bob bisa menerima pesan tanpa memblokir input ketikan
        recv_thread = threading.Thread(target=receive_messages, args=(conn,))
        recv_thread.start()
        
        while chat_active:
            pesan = input("[Anda]: ")
            if pesan.lower() == 'exit':
                chat_active = False
                break
                
            # Enkripsi pesan menggunakan Session Key (Ks)
            pesan_encrypted = encrypt(pesan, session_key)
            try:
                conn.sendall(pesan_encrypted.encode('utf-8'))
            except:
                break
                
if __name__ == "__main__":
    start_bob()
