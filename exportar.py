import sys
from cutreronte_server import Usuarios


if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = "cutreronte_v1_db.csv"
lista = Usuarios.query.all()
print("Exportando base de datos ....")
with open(filename, 'w') as csv_file:
    for elemento in lista:
        csv_file.write("{},{},{}\n".format(elemento.username, elemento.rfid, elemento.autorizado))
print("Generado {} con {} registros".format(filename, len(lista)))
quit(0)
