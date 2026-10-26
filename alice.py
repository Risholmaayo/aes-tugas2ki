import socket
import json
import threading
import random
from aes_core import encrypt, decrypt

# Identitas
IDA = "ALICE_001"
IDB = "BOB_123"

chat_active = False

def receive_messages(conn, session_key):
    global chat_active
    while chat_active:
        try:
            data = conn.recv(4096).decode('utf-8')
            if not data:
                break
            
            # Mendekripsi pesan masuk dari Bob
            plaintext = decrypt(data, session_key)
            print(f"\n[Bob] (Encrypted: {data[:20]}...) -> {plaintext}")
            print("[Anda]: ", end="", flush=True)
        except Exception:
            print("\n[Alice] Koneksi chat terputus.")
            break

def start_alice():
    global chat_active
    print("=== STARTING ALICE (INITIATOR) ===")
    
    # Input interaktif untuk IP dan Master Key
    ka = input("Masukkan Master Key Alice (Ka) (misal: AliceSecret12345): ")
    ip_kdc = input("Masukkan IP Address KDC: ")
    port_kdc = int(input("Masukkan Port KDC: "))
    ip_bob = input("Masukkan IP Address Bob: ")
    port_bob = int(input("Masukkan Port Bob: "))
    
    print("\n[Alice] Menghubungi KDC...")
    kdc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        kdc_socket.connect((ip_kdc, port_kdc))
    except Exception as e:
        print(f"[Alice] Gagal terhubung ke KDC. Error: {e}")
        return

    # --- LANGKAH 1: Alice mengirim (IDA || IDB || N1) ke KDC ---
    n1 = str(random.randint(1000, 9999))
    pesan_ke_kdc = json.dumps({"ida": IDA, "idb": IDB, "n1": n1})
    print(f"[Alice] (Langkah 1) Mengirim permintaan ke KDC dengan N1: {n1}")
    kdc_socket.sendall(pesan_ke_kdc.encode('utf-8'))
    
    # --- LANGKAH 2: Alice menerima balasan terenkripsi dari KDC ---
    data_kdc = kdc_socket.recv(4096).decode('utf-8')
    kdc_socket.close()
    
    print(f"[Alice] (Langkah 2) Menerima bungkusan tiket dari KDC: {data_kdc[:50]}...")
    
    try:
        # Dekripsi tiket KDC dengan Master Key Alice (Ka)
        tiket_terbuka = decrypt(data_kdc, ka)
        data_tiket = json.loads(tiket_terbuka)
        
        session_key = data_tiket['ks']
        tiket_bob = data_tiket['tiket_bob'] # Ini masih terenkripsi dengan Kb
        
        print(f"[Alice] Tiket KDC berhasil dibongkar!")
        print(f"      - Session Key (Ks) didapatkan: {session_key}")
        print(f"      - Verifikasi N1: {'Cocok' if data_tiket['n1'] == n1 else 'TIDAK COCOK!'}")
    except Exception as e:
        print(f"[Alice] Gagal mendekripsi tiket KDC. Master Key Ka salah? Error: {e}")
        return

    # --- LANGKAH 3: Alice menghubungi Bob dan mengirim Tiket Bob ---
    print("\n[Alice] Menghubungi Bob...")
    bob_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        bob_socket.connect((ip_bob, port_bob))
    except Exception as e:
        print(f"[Alice] Gagal terhubung ke Bob. Error: {e}")
        return
        
    print("[Alice] (Langkah 3) Mengirim tiket Bob (E(Kb, [Ks || IDA])) ke Bob...")
    bob_socket.sendall(tiket_bob.encode('utf-8'))
    
    # --- LANGKAH 4: Alice menerima tantangan N2 dari Bob ---
    tantangan_encrypted = bob_socket.recv(4096).decode('utf-8')
    n2_str = decrypt(tantangan_encrypted, session_key)
    print(f"[Alice] (Langkah 4) Menerima tantangan N2 dari Bob: {n2_str}")
    
    # --- LANGKAH 5: Alice membalas dengan f(N2) ---
    f_n2 = str(int(n2_str) - 1) # Sepakat bahwa f(N) adalah N - 1
    balasan_encrypted = encrypt(f_n2, session_key)
    
    print(f"[Alice] (Langkah 5) Mengirim balasan f(N2) = {f_n2} (terenkripsi) ke Bob...")
    bob_socket.sendall(balasan_encrypted.encode('utf-8'))
    
    # --- FASE CHATTING ---
    chat_active = True
    print("\n" + "="*40)
    print("KONEKSI AMAN ESTABLISHED DENGAN AES")
    print("Silakan mulai mengobrol. Ketik 'exit' untuk keluar.")
    print("="*40 + "\n")
    
    # Menjalankan thread penerima agar bisa terus memonitor pesan masuk
    recv_thread = threading.Thread(target=receive_messages, args=(bob_socket, session_key))
    recv_thread.start()
    
    while chat_active:
        pesan = input("[Anda]: ")
        if pesan.lower() == 'exit':
            chat_active = False
            break
            
        pesan_encrypted = encrypt(pesan, session_key)
        try:
            bob_socket.sendall(pesan_encrypted.encode('utf-8'))
        except:
            break

if __name__ == "__main__":
    start_alice()