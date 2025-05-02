from .compre_lib import * 
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
import qgis.utils

class Bdiyalog(QDialog):
    def __init__(self,iface,ebeveyn=None):
        super(Bdiyalog,self).__init__(ebeveyn)
        self.iface=iface
        katmanlar=self.katmanliste()
        etk1=QLabel("Bina Katmanı") 
        #etk2=QLabel("Dörtgenleştirme")
        self.cbox=QCheckBox("Şekil Yap (Önce)", self)
        self.cbox2=QCheckBox("Şekil Yap (Sonra)", self)
        self.etk3=QLabel("Başladı")
        etk4=QLabel("Min Alan (eleme)")
        etk5=QLabel("Min Alan (nokta)")
        etk6=QLabel("Tampon Uz.")
        etk7=QLabel("Şekil Oran")
        self.df1=QLineEdit("25")
        self.df2=QLineEdit("156")
        self.dta=QLineEdit("3")
        self.ddo=QLineEdit("0.95")
        but=QPushButton("Uygula")
        but.clicked.connect(self.uygula)
        but.setToolTip("Uygula!")
        if len(katmanlar)==0:
            self.etk3.setText("Açık alan katmanı yok!")
            but.setEnabled(False)
        self.kombt1=QComboBox()
        self.kombt1.addItems(katmanlar) #Katman listesini kombobox a alıyoruz.
        #self.kombt2=QComboBox()
        #self.kombt2.addItems(["Kontrol","Kırpma"])
        kut=QGridLayout()
        kut.addWidget(etk1,0,0)
        kut.addWidget(self.kombt1,0,1)
        kut.addWidget(etk4,2,0)
        kut.addWidget(etk5,3,0)
        kut.addWidget(etk6,4,0)
        kut.addWidget(etk7,5,0)
        kut.addWidget(self.df1,2,1)
        kut.addWidget(self.df2,3,1)
        kut.addWidget(self.dta,4,1)
        kut.addWidget(self.ddo,5,1)  
        kut.addWidget(self.cbox,6,1) 
        kut.addWidget(self.cbox2,7,1)    
        kut.addWidget(self.etk3,7,0)
        kut.addWidget(but,8,1)
        self.setLayout(kut)
        self.setWindowTitle("BUCOMP") 
        self.setGeometry(50,50,100,150) 
    def uygula(self):
        #Parametre kutularındaki değerleri float olarak alalım. 
        tdist=float(self.dta.text())
        a1=float(self.df1.text())
        a2=float(self.df2.text())
        #print(a2)
        dt=float(self.ddo.text())
        for lyr in self.iface.mapCanvas().layers():
            if self.kombt1.currentText()==lyr.name():
                self.lyr1=lyr
                if self.cbox.isChecked():
                    # lyr1=dortgen_yap(lyr,tol=dt,da=a2)
                    lyr1=sekilYap(lyr,tolR=dt,tolC=dt,dr=1,da=a1)
                else:
                    lyr1=lyr
                lyr2=birlestir(lyr1,bdist=tdist)
                plyr=alan_eleme(lyr2,a1=a1,a2=a2)
                if self.cbox2.isChecked():
                    # lyr3=dortgen_yap(lyr2,tol=dt,da=a2)
                    lyr3=sekilYap(lyr2,tolR=dt,tolC=dt,dr=1,da=a1)
                    lyr3.setName(lyr2.name())
                    QgsProject.instance().addMapLayer(lyr3)
                else:
                    QgsProject.instance().addMapLayer(lyr2)
                if plyr.featureCount()>0:
                    QgsProject.instance().addMapLayer(plyr)
        self.kombt1.clear()
        self.kombt1.addItems(self.katmanliste())
        self.etk3.setText("İşlem Tamam!")
    def katmanliste(self):
        katmanlar=[]
        for lyr in self.iface.mapCanvas().layers():
            if lyr.geometryType() == QgsWkbTypes.PolygonGeometry:
                katmanlar.append(lyr.name())
        return katmanlar


