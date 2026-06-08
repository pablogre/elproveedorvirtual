cd C:\factufacil

# 1) Crear carpeta de cuarentena
mkdir _archivos_a_borrar

# 2) Mover los archivos sospechosos (no borrar todav¡a)
move config_local.py _archivos_a_borrar\
move "impresora_termica - copia.py" _archivos_a_borrar\
move proveedores_backup_pre_pv5.py _archivos_a_borrar\
move "stock_audit (1).py" _archivos_a_borrar\
move paquete_cambios.zip _archivos_a_borrar\
move archivos.txt _archivos_a_borrar\
move estructura.txt _archivos_a_borrar\
move notas.txt _archivos_a_borrar\
move prov_cod.xls _archivos_a_borrar\
move categorias.xlsx _archivos_a_borrar\
move dump-schiro-202604191120.sql _archivos_a_borrar\
move "EPSON TM-m30II Receipt" _archivos_a_borrar\

# Tests/diagn¢sticos
move diagnostico_*.py _archivos_a_borrar\
move diag_*.py _archivos_a_borrar\
move test_*.py _archivos_a_borrar\
move test_afip_debug _archivos_a_borrar\
move prueba_afip.py _archivos_a_borrar\
move qr_debug_*.py _archivos_a_borrar\
move qr_imagen_*.py _archivos_a_borrar\
move qr_simple_*.py _archivos_a_borrar\
move ssl_ultra_fix.py _archivos_a_borrar\
move convertir_crt.py _archivos_a_borrar\

# Instaladores
move install*.py _archivos_a_borrar\
move instalar_*.py _archivos_a_borrar\
move instalar_*.bat _archivos_a_borrar\
move crear_base_datos.bat _archivos_a_borrar\
move setup_*.* _archivos_a_borrar\
move production_config.py _archivos_a_borrar\
move migrar_proveedores.py _archivos_a_borrar\
move migration_*.py _archivos_a_borrar\
move Win64OpenSSL_Light-3_4_2.exe _archivos_a_borrar\

# 3) Reiniciar el servicio
nssm restart factufacil

# 4) Probar el sistema 1-2 d¡as
# Si todo funciona: borrar la carpeta
# 4) Probar el sistema 1-2 d¡as