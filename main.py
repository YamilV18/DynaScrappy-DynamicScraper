from dynamic_scraper import DynamicScraper
import sys

def main():
    scraper = DynamicScraper()

    scraper.iniciar_navegador()
    
    try:
        while True:
            print("\n" + "="*40)
            print("   | DYNASCRAPPY | DYNAMIC SCRAPER")
            print("="*40)
            
            target_url = input("URL (o 'salir'): ").strip()
            
            if target_url.lower() in ['salir', 'exit', '0']:
                break

            print("\n1. Archivos | 2. Imágenes | 3. Texto | 4. Videos | 5. Cancelar")
            opc = input("Opción: ")
            
            if opc == '1':
                exts = input("Extensiones (ej: pdf,csv): ")
                ext_list = [e.strip() for e in exts.split(',')] if exts else None
                scraper.run(target_url, mode='files', extensions=ext_list)
            elif opc == '2':
                scraper.run(target_url, mode='images')
            elif opc == '3':
                scraper.run(target_url, mode='text')
            elif opc == '4':
                scraper.run(target_url, mode='videos')
            elif opc == '5':
                continue
            
            print("\n[✔] Tarea completada. El navegador sigue abierto.")

    except KeyboardInterrupt:
        print("\n[!] Interrupción detectada (Ctrl+C).")
    
    finally:
        # Esto se ejecuta tanto si escribes 'salir' como si presionas Ctrl+C
        scraper.cerrar_todo()
        print("Programa finalizado correctamente.")
        sys.exit(0)

if __name__ == "__main__":
    main()