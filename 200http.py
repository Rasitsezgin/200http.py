# Örnek kullanım:
    # python3 200durum.py -u http://example.com -w /usr/share/wordlists/dirb/common.txt -t 100 -o results.txt


import os
import requests
import threading
import time
import argparse
from requests.exceptions import RequestException
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

class DirectoryBruteForcer:
    def __init__(self, base_url, wordlist_file, max_threads=50, timeout=5, output_file=None):
        self.base_url = base_url.rstrip('/')
        self.wordlist_file = wordlist_file
        self.max_threads = max_threads
        self.timeout = timeout
        self.output_file = output_file
        self.found_paths = []
        self.scanned_count = 0
        self.lock = threading.Lock()
        
        # Gelişmiş headers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # Önemli status code'lar
        self.interesting_codes = [200, 301, 302, 403, 500]
        
    def load_wordlist(self):
        """Wordlist'i yükler ve filtreler"""
        if not os.path.exists(self.wordlist_file):
            raise FileNotFoundError(f"Wordlist dosyası bulunamadı: {self.wordlist_file}")
            
        wordlist = []
        try:
            with open(self.wordlist_file, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    word = line.strip()
                    if word and not word.startswith('#'):
                        wordlist.append(word)
            print(f"[+] {len(wordlist)} kelime wordlist'ten yüklendi")
            return wordlist
        except Exception as e:
            print(f"[-] Wordlist yüklenirken hata: {e}")
            return []
    
    def check_url(self, path):
        """Tek bir URL'yi kontrol eder"""
        try:
            target_url = urljoin(self.base_url + '/', path)
            
            response = requests.get(
                target_url, 
                headers=self.headers, 
                timeout=self.timeout,
                allow_redirects=False  # Redirect'leri manuel kontrol et
            )
            
            # Response length
            content_length = len(response.content)
            
            with self.lock:
                self.scanned_count += 1
                
                if response.status_code in self.interesting_codes:
                    result = {
                        'url': target_url,
                        'status': response.status_code,
                        'length': content_length,
                        'redirect': response.headers.get('Location', '')
                    }
                    
                    self.found_paths.append(result)
                    
                    # Ek bilgiler
                    server = response.headers.get('Server', 'Unknown')
                    powered_by = response.headers.get('X-Powered-By', '')
                    
                    status_color = self.get_status_color(response.status_code)
                    print(f"[{status_color}{response.status_code}\033[0m] {target_url} (Length: {content_length})")
                    
                    if response.status_code in [301, 302]:
                        print(f"    ↳ Redirects to: {response.headers.get('Location')}")
                    
                    if server != 'Unknown':
                        print(f"    ↳ Server: {server}")
                    
                    # Output dosyasına yaz
                    if self.output_file:
                        with open(self.output_file, 'a') as f:
                            f.write(f"{target_url} | Status: {response.status_code} | Length: {content_length}\n")
                
                # Progress göstergesi
                if self.scanned_count % 100 == 0:
                    print(f"[*] {self.scanned_count} path taranmış...")
                    
        except requests.exceptions.Timeout:
            pass
        except requests.exceptions.ConnectionError:
            print(f"[-] {self.base_url} bağlantı hatası")
        except RequestException as e:
            pass
        except Exception as e:
            pass
    
    def get_status_color(self, status_code):
        """Status code'a göre renk döndürür"""
        if status_code == 200:
            return "\033[92m"  # Yeşil
        elif status_code in [301, 302]:
            return "\033[94m"  # Mavi
        elif status_code == 403:
            return "\033[93m"  # Sarı
        elif status_code == 500:
            return "\033[91m"  # Kırmızı
        else:
            return "\033[0m"   # Normal
    
    def scan(self):
        """Ana tarama fonksiyonu"""
        print(f"[*] Tarama başlatılıyor: {self.base_url}")
        print(f"[*] Wordlist: {self.wordlist_file}")
        print(f"[*] Thread sayısı: {self.max_threads}")
        print("-" * 50)
        
        start_time = time.time()
        wordlist = self.load_wordlist()
        
        if not wordlist:
            print("[-] Wordlist boş, tarama durduruldu")
            return
        
        # Output dosyasını temizle
        if self.output_file:
            open(self.output_file, 'w').close()
        
        # ThreadPool ile tarama
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {executor.submit(self.check_url, word): word for word in wordlist}
            
            try:
                for future in as_completed(futures):
                    future.result()
            except KeyboardInterrupt:
                print("\n[!] Kullanıcı tarafından durduruldu")
                executor.shutdown(wait=False)
        
        # Sonuçları göster
        self.show_results(start_time)
    
    def show_results(self, start_time):
        """Sonuçları gösterir"""
        end_time = time.time()
        scan_duration = end_time - start_time
        
        print("\n" + "=" * 50)
        print("TARAMA TAMAMLANDI")
        print("=" * 50)
        
        # Status code'a göre grupla
        status_groups = {}
        for result in self.found_paths:
            status = result['status']
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(result)
        
        # Grupları göster
        for status in sorted(status_groups.keys()):
            color = self.get_status_color(status)
            print(f"\n{color}{status} Status Code ({len(status_groups[status])} results):\033[0m")
            for result in status_groups[status]:
                print(f"  {result['url']} (Length: {result['length']})")
        
        print(f"\n[*] Toplam süre: {scan_duration:.2f} saniye")
        print(f"[*] Toplam taranan: {self.scanned_count} path")
        print(f"[*] Bulunan path'ler: {len(self.found_paths)}")
        
        if self.output_file:
            print(f"[*] Sonuçlar kaydedildi: {self.output_file}")

def main():
    parser = argparse.ArgumentParser(description='Gelişmiş Directory Brute Force Aracı')
    parser.add_argument('-u', '--url', required=True, help='Hedef URL')
    parser.add_argument('-w', '--wordlist', required=True, help='Wordlist dosya yolu')
    parser.add_argument('-t', '--threads', type=int, default=50, help='Thread sayısı (default: 50)')
    parser.add_argument('-o', '--output', help='Output dosyası')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout süresi (default: 5)')
    
    args = parser.parse_args()
    
    # Brute force başlat
    bruter = DirectoryBruteForcer(
        base_url=args.url,
        wordlist_file=args.wordlist,
        max_threads=args.threads,
        timeout=args.timeout,
        output_file=args.output
    )
    
    try:
        bruter.scan()
    except KeyboardInterrupt:
        print("\n[!] Program kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"[-] Hata: {e}")

if __name__ == "__main__":
    # Örnek kullanım:
    # python3 bruter.py -u http://example.com -w /usr/share/wordlists/dirb/common.txt -t 100 -o results.txt
    main()
