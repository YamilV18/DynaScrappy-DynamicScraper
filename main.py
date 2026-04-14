from dynamic_scraper import DynamicScraper

def main():
    scraper = DynamicScraper()
    
    while True: # Bucle infinito para mantener la consola abierta
        print("\n" + "="*40)
        print("   UNIVERSAL DYNAMIC SCRAPER")
        print("="*40)
        
        target_url = input("Introduce la URL (o 'salir' para terminar): ").strip()
        
        if target_url.lower() in ['salir', 'exit', '0']:
            print("Saliendo del programa...")
            break

        print("\n¿Qué deseas descargar?")
        print("1. Archivos (PDF, CSV, ZIP, etc.)")
        print("2. Imágenes")
        print("3. Solo Texto")
        print("4. Volver / Cancelar")
        
        opc = input("\nSelecciona una opción: ")
        
        if opc == '1':
            exts = input("Extensiones (ej: pdf,csv) o ENTER para default: ")
            ext_list = [e.strip() for e in exts.split(',')] if exts else None
            scraper.run(target_url, mode='files', extensions=ext_list)
        
        elif opc == '2':
            scraper.run(target_url, mode='images')
        
        elif opc == '3':
            scraper.run(target_url, mode='text')
        
        elif opc == '4':
            continue # Vuelve al inicio del bucle
            
        else:
            print("[!] Opción no válida")

        print("\n[✔] Proceso terminado.")
        # Aquí el bucle vuelve a empezar, pidiendo una nueva URL

if __name__ == "__main__":
    main()