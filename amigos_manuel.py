#!/usr/bin/python
# -*- coding: utf-8 -*-

from gi.repository import Gtk, GObject
import MySQLdb
import time

def mensajeErrorSQL(e):
   try:
        print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
   except IndexError:
        print "MySQL Error: %s" % str(e)        


class AmigosManuelGUI:
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
			"onCloseAboutDialog": self.onCloseAboutDialog}
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

        column = Gtk.TreeViewColumn('id', Gtk.CellRendererText(), text=0)   
        column.set_clickable(True)   
        column.set_resizable(True)   
        self.lista.append_column(column)

        column = Gtk.TreeViewColumn('Nombre', Gtk.CellRendererText(), text=1)   
        column.set_clickable(True)   
        column.set_resizable(True)   
        self.lista.append_column(column)
        
        # self.window.connect("delete_event", Gtk.main_quit)
        self.window.show_all()
        self.modoOperacion = 0  # No operacio, 1 Crear Amigo, 2 Obtener, 3 Actual, 4 Borrar
        self.ponModoOperacion() 
        #self.window.resize(600,300)
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
            self.cargaLista()
            self.activarCamposEdicion(False)
            self.idSeleccionado = -1
   
    def onDeleteWindow(self, *args):
        self.cerrarBaseDatos()
        Gtk.main_quit(*args)

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

    def cargaLista(self):
        self.modeloLista.clear()
        query= "SELECT Amigo_no,Nombre FROM Amigos WHERE 1;"
        try:
            self.Cursor.execute(query)
            registros = self.Cursor.fetchall()
        except MySQLdb.Error, e:
            mensajeErrorSQL(e)
            return
        try:
            for registro in registros:
                print "Introduce  registro", str(registro[0]), registro[1]
                self.modeloLista.append([str(registro[0]),registro[1]])
                
        except:
            self.statusbar.push(self.idStatusBar, "ERROR no se ha podido cargar la lista de amigos")
            
    def onCrearAmigo(self, menuitem ):
        self.modoOperacion = 1
        self.ponModoOperacion()

    def onObtenerAmigo(self, menuitem):
        self.modoOperacion = 2
        self.ponModoOperacion()
    
    def onActualizarAmigo(self, menuitem):
        print "Actualizar Amigo"
        self.modoOperacion = 3
        self.ponModoOperacion()

    def onBorrarAmigo(self, menuitem):
        self.modoOperacion = 4
        self.ponModoOperacion()

    def idAmigoNuevo(self):
        """ Devuelve un ID para la inserción de un registro nuevo

             Obtiene el numero de registros de la base de datos y le suma 1
        
             Devuelve: El ID nuevo
        """
        n_reg = len(self.modeloLista)+1
        # Comprueba si existe algún registro con ID = n_reg, de ser así lo incrementa hasta
        # que no se dé. 
        while next((fila for fila in self.modeloLista if int(fila[0]) == n_reg),None) != None :
            n_reg += 1
        return n_reg
    
    def ponerDatosEnBlanco(self):
        self.edNombre.set_text("")
        self.edEnComun.set_text("")
        self.edProcedencia.set_text("")
        self.edTelefono.set_text("")
        self.edEmail.set_text("")

    def ponerDatosEdicion(self):
        query= "SELECT * FROM Amigos WHERE Amigo_no={:s};".format(self.idSeleccionado)
        try:
            self.Cursor.execute(query)
            registro = self.Cursor.fetchone()
        except MySQLdb.Error, e:
            mensajeErrorSQL(e)
            self.statusbar.push(self.idStatusBar, "ERROR no se ha podido cargar amigo")
            return
        self.edNombre.set_text(registro[1])
        self.edEnComun.set_text(registro[3])
        self.edProcedencia.set_text(registro[2])
        self.edTelefono.set_text(registro[4])
        self.edEmail.set_text(registro[5])

    def obtenerIdSeleccionado(self):
        selection = self.lista.get_selection()
        tree_model, tree_iter = selection.get_selected()
        self.idSeleccionado = tree_model.get_value(tree_iter, 0)
        
    def activarCamposEdicion(self, activar):
        self.edNombre.set_sensitive(activar)
        self.edEnComun.set_sensitive(activar)
        self.edProcedencia.set_sensitive(activar)
        self.edTelefono.set_sensitive(activar)
        self.edEmail.set_sensitive(activar)
        
    def crearAmigo(self):
        nombre = self.edNombre.get_text()
        if nombre.isspace():
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
                    self.cargaLista()
                    self.ponerDatosEnBlanco()
                    self.activarCamposEdicion(False)
                    self.statusbar.push(self.idStatusBar, "Se ha creado un amigo nuevo")
            except MySQLdb.Error, e:
                mensajeErrorSQL(e)
                self.statusbar.push(self.idStatusBar, "ERROR no se ha podido crear amigo")     

    def obtenerAmigo(self):
        self.obtenerIdSeleccionado()
        self.ponerDatosEdicion()
        
    def actualizarAmigo(self):
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
                self.cargaLista()
                self.ponerDatosEnBlanco()
                self.activarCamposEdicion(False)
                self.statusbar.push(self.idStatusBar, "Se han modificado los datos del amigo")
            except MySQLdb.Error, e:
                mensajeErrorSQL(e)
                self.statusbar.push(self.idStatusBar, "ERROR no se han podido modificar los datos del amigo")

    def borrarAmigo(self):
        self.obtenerIdSeleccionado()
        query = 'DELETE FROM Amigos WHERE Amigo_no="{:s}"'.format(self.idSeleccionado)
        try:
            if self.Cursor.execute(query) != 1L:
                self.statusbar.push(self.idStatusBar, "ERROR no se ha podido borrar el amigo")
            else:
                self.Conexion.commit()
                self.cargaLista()
                self.statusbar.push(self.idStatusBar, "Amigo eliminado")
        except MySQLdb.Error, e:
            mensajeErrorSQL(e)
            self.statusbar.push(self.idStatusBar, "ERROR no se ha podido borrar el amigo")
        
    def onBtnOperacionClicked(self, button):
        if self.modoOperacion == 1:
            self.crearAmigo()
            time.sleep(2)  
        elif self.modoOperacion == 2:
            self.obtenerAmigo()
        elif self.modoOperacion == 3:
            self.actualizarAmigo()
        elif self.modoOperacion == 4:
            self.borrarAmigo()
  
        self.modoOperacion = 0
        self.ponModoOperacion()

    def onAcercaDe(self, menuitem):
        self.about.show()
   
    def onCloseAboutDialog(self,window,data=None):
        print "Salir Acerca de"
        self.about.hide()

    def ponModoOperacion(self):
        if self.modoOperacion == 0:
            self.btOperacion.hide()
            self.statusbar.push(self.idStatusBar, "Elija una opción del menú Operaciones.")
        elif self.modoOperacion == 1:
            self.activarCamposEdicion(True)
            self.ponerDatosEnBlanco()
            self.btOperacion.show()
            self.btOperacion.set_label("Crear nuevo amigo")
            self.statusbar.push(self.idStatusBar,
                                "Introduzca los datos de un nuevo amigo y pulse el botón 'Crear nuevo amigo'")
        elif self.modoOperacion == 2:
            self.btOperacion.show()
            self.btOperacion.set_label("Obtener amigo")
            self.statusbar.push(self.idStatusBar,
                                "Seleccione amigo de la lista y pulse el botón 'Obtener amigo'")
        elif self.modoOperacion == 3:
            self.btOperacion.show()
            self.activarCamposEdicion(True)
            self.obtenerAmigo()
            self.btOperacion.set_label("Actualizar datos")
            self.statusbar.push(self.idStatusBar,
                                "Modifique los datos del amigo seleccionado y pulse 'Actualizar datos'")
        elif self.modoOperacion == 4:
            self.btOperacion.show()
            self.btOperacion.set_label("Borrar amigo")
            self.statusbar.push(self.idStatusBar,
                                "Pulse 'Borrar amigo' y se eliminarán los datos del amigo seleccionado")
            
def main():
    window = AmigosManuelGUI()    
    Gtk.main()
    
    return 0

if __name__ == '__main__':
    main()

