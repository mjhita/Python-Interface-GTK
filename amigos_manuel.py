#!/usr/bin/python
# -*- coding: utf-8 -*-
############################################################################
#
# Curso Tratamiento de datos, juegos y programación gráfica en Python
#
# TEMA: Interfaces gráficas con PyGTK.
#
# Tarea CRUD. Interfaz gráfica que permita Crear, Obtener, Actualizar
#             y Borrar elementos de una base de datos
#             
#
# Las ordenes para crear la base de datos y la tabla están en el archivo:
#     DBManuel.sql
# Implementado por: Manuel Jesús Hita Jiménez - 2017
#
############################################################################
from gi.repository import Gtk, GObject
import MySQLdb
import time

def mensajeErrorSQL(e):
   try:
        print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
   except IndexError:
        print "MySQL Error: %s" % str(e)        


class AmigosManuelGUI:
    """
         Clase que implementa la interfaz gráfica que permita Crear, Obtener, Actualizar
         y Borrar elementos de la base de datos de Amigos de Manuel (DBManuel)
         
         Visualiza una lista (treeview) a la izquierda con los registros existentes en
         la tabla de amigos, mostrando en cada fila el Id y Nombre de cada uno de los amigos

         Las operaciones, accesibles a través del menú (opción Operaciones) permiten:
           - Actualizar y Borrar el elemento seleccionado en la lista
           - Obtener elemento, hace una busqueda por Nombre
           - Crear nuevos elementos

         Incluye la gestión de conexión y desconexión a la base de datos
    """
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("amigos_manuel.glade")
        self.handlers = {
			"onDeleteWindow": self.onDeleteWindow,
			"onCrearAmigo": self.onCrearAmigo,
                        "onObtenerAmigo": self.onObtenerAmigo,
                        "onActualizarAmigo": self.onActualizarAmigo,
                        "onBorrarAmigo": self.onBorrarAmigo,
                        "onAcercaDe": self.onAcercaDe,
                        "onBtnOperacionClicked": self.onBtnOperacionClicked,
			"onCloseAboutDialog": self.onCloseAboutDialog,
                        "onCambiarSeleccion": self.onCambiarSeleccion}
        # Conectamos las señales e iniciamos la aplicación
        self.builder.connect_signals(self.handlers)

        self.window = self.builder.get_object("AmigosManuel")
        self.btn = self.builder.get_object("btn")
        self.menuOperaciones = self.builder.get_object("menuOperaciones")
        self.statusbar = self.builder.get_object("statusbar")
        self.idStatusBar = self.statusbar.get_context_id("statusbar")
        self.btOperacion = self.builder.get_object("btOperacion")
        self.edNombre =  self.builder.get_object("edNombre")
        self.edEnComun =  self.builder.get_object("edEnComun")
        self.edProcedencia =  self.builder.get_object("edProcedencia")
        self.edTelefono =  self.builder.get_object("edTelefono")
        self.edEmail =  self.builder.get_object("edEmail")
        self.about = self.builder.get_object("dialogoAcercaDe")
        self.modeloLista = self.builder.get_object('listItems')
        self.lista = self.builder.get_object('treeIds')
        
        # Defino las columnas de la lista TreeView 
        column = Gtk.TreeViewColumn('Id', Gtk.CellRendererText(), text=0)   
        column.set_clickable(True)   
        column.set_resizable(True)   
        self.lista.append_column(column)

        column = Gtk.TreeViewColumn('Nombre', Gtk.CellRendererText(), text=1)   
        column.set_clickable(True)   
        column.set_resizable(True)   
        self.lista.append_column(column)
        
        self.window.show_all()
        self.modoOperacion = 0  # No operacio, 1 Crear Amigo, 2 Obtener, 3 Actual, 4 Borrar
        self.ponModoOperacion() 
        self.Conexion = None
        self.Cursor = None
        self.conectarABaseDatos()
        if not self.Conexion or not self.Cursor:
            self.statusbar.push(self.idStatusBar, "ERROR al conectar a la Base de Datos. "
                                "Las operaciones no están disponibles")
            self.builder.get_object("menuitemCrear").set_sensitive(False)
            self.builder.get_object("menuitemObtener").set_sensitive(False)
            self.builder.get_object("menuitemActualizar").set_sensitive(False)
            self.builder.get_object("menuitemBorrar").set_sensitive(False)
        else:
            self.cargarLista()
            self.activarCamposEdicion(False)
            self.idSeleccionado = -1

    def conectarABaseDatos(self):
        try:
            self.Conexion = MySQLdb.connect(host='localhost', user='manuel',passwd='hita', db='DBManuel')
            self.Cursor = self.Conexion.cursor()
        except MySQLdb.Error, e:
            mensajeErrorSQL(e)

    def cerrarBaseDatos(self):
        if not self.Conexion or not self.Cursor:
            return
        try:
            self.Cursor.close()
            self.Conexion.close()
        except MySQLdb.Error, e:
            mensajeErrorSQL(e)  

    def cargarLista(self):
        """
            Carga la lista, el TreeView, con el Id y nombre de cada amigo por fila
        """ 
        self.modeloLista.clear()
        query= "SELECT Amigo_no,Nombre FROM Amigos WHERE 1;"
        try:
            self.Cursor.execute(query)
            registros = self.Cursor.fetchall()
            for registro in registros:
                self.modeloLista.append([str(registro[0]),registro[1]])
                
        except MySQLdb.Error, e:
            mensajeErrorSQL(e)
        except:
            self.statusbar.push(self.idStatusBar, "ERROR no se ha podido cargar la lista de amigos")
 
    def onDeleteWindow(self, *args):
        self.cerrarBaseDatos()
        Gtk.main_quit(*args)
       
    def onCrearAmigo(self, menuitem ):
        self.modoOperacion = 1
        self.ponModoOperacion()

    def onObtenerAmigo(self, menuitem):
        self.modoOperacion = 2
        self.ponModoOperacion()
    
    def onActualizarAmigo(self, menuitem):
        self.modoOperacion = 3
        self.ponModoOperacion()

    def onBorrarAmigo(self, menuitem):
        self.modoOperacion = 4
        self.ponModoOperacion()

    def onCambiarSeleccion(self,reeSelection):
        """
           Evento provocado por el cambio de elemento seleccionado de la lista
         
        """ 
        self.cargarAmigo()

    def idAmigoNuevo(self):
        """
             Devuelve un ID para la inserción de un registro nuevo

             Obtiene el numero de registros de la base de datos y le suma 1
        
             Devuelve: El ID nuevo
        """
        n_reg = len(self.modeloLista)+1
        # Comprueba si existe algún registro con ID = n_reg, de ser así lo incrementa hasta
        # que no se dé. 
        while next((fila for fila in self.modeloLista if int(fila[0]) == n_reg),None) != None :
            n_reg += 1
        return n_reg
      
    def activarCamposEdicion(self, activar):
        self.edNombre.set_sensitive(activar)
        self.edEnComun.set_sensitive(activar)
        self.edProcedencia.set_sensitive(activar)
        self.edTelefono.set_sensitive(activar)
        self.edEmail.set_sensitive(activar)
            
    def ponerDatosEnBlanco(self):
        self.edNombre.set_text("")
        self.edEnComun.set_text("")
        self.edProcedencia.set_text("")
        self.edTelefono.set_text("")
        self.edEmail.set_text("")

    def cargarDatosRegistro(self, registro):
        """
            Vuelca los datos del registro "registro" en los campos de edición de la
            interfaz gráfica
        """
        self.edNombre.set_text(registro[1])
        self.edEnComun.set_text(registro[3])
        self.edProcedencia.set_text(registro[2])
        self.edTelefono.set_text(registro[4])
        self.edEmail.set_text(registro[5])
        
    def ponerDatosEdicion(self):
        """
           Vuelca los datos del registro que coincida (por su ID) con el
           seleccionado en la lista
        """  
        if not self.idSeleccionado:
            self.ponerDatosEnBlanco()
            return
        query= "SELECT * FROM Amigos WHERE Amigo_no={:s};".format(self.idSeleccionado)
        try:
            if self.Cursor.execute(query) > 0:
                registro = self.Cursor.fetchone()
                self.cargarDatosRegistro(registro)
            else:
                self.ponerDatosEnBlanco()    
        except MySQLdb.Error, e:
            mensajeErrorSQL(e)
            self.statusbar.push(self.idStatusBar, "ERROR no se ha podido cargar amigo")
            return  

    def obtenerIdSeleccionado(self):
        """
            Obtiene de la lista el ID del elemento seleccionado y lo almacena en
            idSeleccionado
        """
        selection = self.lista.get_selection()
        tree_model, tree_iter = selection.get_selected()
        if tree_iter:
            self.idSeleccionado = tree_model.get_value(tree_iter, 0)
        else:
            self.idSeleccionado = None
        
    def ponerIdSeleccionado(self, idSel):
        """
           Selecciona de la lista (TreeView) la fila con la columna ID =idSel

        """
        selection = self.lista.get_selection()
        cont = 0
        for fila in self.modeloLista:
           if fila[0] == idSel:
               break
           cont += 1
         
        selection.select_path(cont)   

    def crearAmigo(self):
        """
            Crea un amigo nuevo y lo añade a la tabla y a la lista de amigos
        """ 
        nombre = self.edNombre.get_text()
        if nombre.isspace() or nombre == "":
            self.statusbar.push(self.idStatusBar, "ERROR Debe introducir al menos el nombre")
        else:
            idAmigo = self.idAmigoNuevo()
            enComun =  self.edEnComun.get_text()
            procedencia =  self.edProcedencia.get_text()
            telefono =  self.edTelefono.get_text()
            email =  self.edEmail.get_text()
            query = 'INSERT INTO Amigos (Amigo_no,Nombre,Procedencia,EnComun,Telefono,Email) VALUES'
            query += '({:d},"{:s}","{:s}","{:s}","{:s}","{:s}");'.format(idAmigo, nombre, procedencia,
                                                                         enComun, telefono, email)
            try:
                if self.Cursor.execute(query) != 1L:
                    self.statusbar.push(self.idStatusBar, "ERROR no se ha podido crear amigo")
                else:
                    self.Conexion.commit()
                    self.cargarLista()
                    self.ponerDatosEnBlanco()
                    self.ponerIdSeleccionado(str(idAmigo))
            except MySQLdb.Error, e:
                mensajeErrorSQL(e)
                self.statusbar.push(self.idStatusBar, "ERROR no se ha podido crear amigo")
        self.activarCamposEdicion(False)       

    def cargarAmigo(self):
        """
            Obtiene el ID del amigo de la lista, lo busca en la tabla y lo carga en los
            campos de edición de datos
        """
        self.obtenerIdSeleccionado()
        self.ponerDatosEdicion()

    def obtenerAmigo(self):
        """
           Solicita un nombre de amigo y lo busca en la tabla. Si lo encuentra vuelca
           sus datos en los campos de edición de la ventana
        """
        nombre = self.edNombre.get_text()
        query= 'SELECT * FROM Amigos WHERE Nombre="{:s}";'.format(nombre)
        try:
            nSel = self.Cursor.execute(query)
            if nSel > 0:
                registro = self.Cursor.fetchone()
                self.cargarDatosRegistro(registro)
                self.ponerIdSeleccionado(str(registro[0]))
            else:
                self.ponerDatosEnBlanco()
                self.edNombre.set_text("No se ha encontrado")
            self.edNombre.set_sensitive(False)    
        except MySQLdb.Error, e:
            mensajeErrorSQL(e)
            self.statusbar.push(self.idStatusBar, "ERROR no se ha podido cargar amigo")
            
    def actualizarAmigo(self):
        """
           Permite modificar los datos del amigo que esté seleccionado
        """
        nombre = self.edNombre.get_text()
        if nombre.isspace():
            self.statusbar.push(self.idStatusBar, "ERROR el nombre no puede estar vacio")
        else:
            enComun =  self.edEnComun.get_text()
            procedencia =  self.edProcedencia.get_text()
            telefono =  self.edTelefono.get_text()
            email =  self.edEmail.get_text()
            query = 'UPDATE Amigos SET Nombre="{:s}",Procedencia="{:s}",EnComun="{:s}",'.format(nombre,
                                                                                                 procedencia,
                                                                                                 enComun)
            query += 'Telefono="{:s}",Email="{:s}" WHERE Amigo_no={:s}'.format(telefono, email,
                                                                                 self.idSeleccionado)
            try:
                self.Cursor.execute(query)
                self.Conexion.commit()
                idSel = self.idSeleccionado 
                self.cargarLista()
                self.ponerIdSeleccionado(idSel)
                self.ponerDatosEdicion()
            except MySQLdb.Error, e:
                mensajeErrorSQL(e)
                self.statusbar.push(self.idStatusBar, "ERROR no se han podido modificar los datos del amigo")   

    def borrarAmigo(self):
        """
           Borra el amigo que esté seleccionado
        """
        self.obtenerIdSeleccionado()
        query = 'DELETE FROM Amigos WHERE Amigo_no="{:s}"'.format(self.idSeleccionado)
        try:
            if self.Cursor.execute(query) != 1L:
                self.statusbar.push(self.idStatusBar, "ERROR no se ha podido borrar el amigo")
            else:
                self.Conexion.commit()
                self.cargarLista()
            self.ponerDatosEnBlanco()    
        except MySQLdb.Error, e:
            mensajeErrorSQL(e)
            self.statusbar.push(self.idStatusBar, "ERROR no se ha podido borrar el amigo")
        
    def onBtnOperacionClicked(self, button):
        if self.modoOperacion == 1:
            self.crearAmigo()
        elif self.modoOperacion == 2:
            self.obtenerAmigo()
        elif self.modoOperacion == 3:
            self.obtenerIdSeleccionado()
            if self.idSeleccionado:
                self.actualizarAmigo()
            else:
                self.ponerDatosEnBlanco()
            self.activarCamposEdicion(False)    
        elif self.modoOperacion == 4:
            if self.idSeleccionado:
                self.borrarAmigo()
  
        self.modoOperacion = 0
        self.ponModoOperacion()

    def onAcercaDe(self, menuitem):
        self.about.show()
   
    def onCloseAboutDialog(self,window,data=None):
        self.about.hide()

    def ponModoOperacion(self):
        """
            Se llama al pulsar las opcioes del menu Operaciones
            Gesiona el botón para realizar la operación, da inforamción sobre la operación
            en la barra de estado, activa o desactiva los controles necesarios para la operación
            y pone la varible que modoOperacion con un valor que indica la operación seleccionada
        """    
        if self.modoOperacion == 0:
            self.btOperacion.hide()
            self.statusbar.push(self.idStatusBar, "Elija una opción del menú Operaciones.")
        elif self.modoOperacion == 1:
            self.btOperacion.set_label("Crear nuevo amigo")
            self.activarCamposEdicion(True)
            self.ponerDatosEnBlanco()
            self.btOperacion.show()
            self.statusbar.push(self.idStatusBar,
                                "Introduzca los datos de un nuevo amigo y pulse el botón 'Crear nuevo amigo'")
        elif self.modoOperacion == 2:
            self.btOperacion.set_label("Obtener amigo")
            self.btOperacion.show()
            self.ponerDatosEnBlanco()
            self.edNombre.set_sensitive(True)
            self.statusbar.push(self.idStatusBar,
                                "Introduzca nombre de amigo y pulse el botón 'Obtener amigo'")
        elif self.modoOperacion == 3:
            self.btOperacion.set_label("Actualizar datos")
            self.btOperacion.show()
            self.activarCamposEdicion(True)
            self.cargarAmigo()
            self.statusbar.push(self.idStatusBar,
                                "Modifique los datos del amigo seleccionado y pulse 'Actualizar datos'")
        elif self.modoOperacion == 4:
            self.btOperacion.set_label("Borrar amigo")
            self.btOperacion.show()
            self.statusbar.push(self.idStatusBar,
                                "Pulse 'Borrar amigo' y se eliminarán los datos del amigo seleccionado")
            
def main():
    window = AmigosManuelGUI()    
    Gtk.main()
    
    return 0

if __name__ == '__main__':
    main()

