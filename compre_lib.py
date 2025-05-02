# Bu gruptaki parametreler
# birleştir  bdist: Tampon genişliği parametresi 
# alan_eleme    a1: Silinecek alan
#               a2: Noktaya çevrilecek alan
# Önerilen akış Dörtgen yap > Birleştir > Alan Eleme 
# Bunun sonucunda genelleştirilmiş alan katmanı ve nokta katmanı çıkar. 
#
from qgis.core import *
import qgis.utils
from qgis import processing
from PyQt5.QtCore import QVariant
import math
import numpy as np
# from .qgeolib import sekilYap

def daireyap(p0,r,dr=1):
    ring=[]
    da=math.degrees(dr/r)
    #Yaya karşılık açı 30'den büyükse daire görünümünü korumak için 30
    #yapıyoruz, ki daire min 12 noktadan oluşsun. 
    if da>30:
        da=30
    az=0
    while az<360:
        ring.append(p0.project(r,az)) #project birinci temel ödev!
        az+=da
    return ring
def izoper(a,p):
    "İzoperimetrik Oran 4*pi*area/perimeter^2"
    return 4*math.pi*a/p**2
def makeRect(geom, tol1=0.95,tol2=0.95,dr=1):
    """tol1 dikdörtgen, tol2 daire için tolerans
       dr daire oluşturmak için yay uzunluğu """
    area0=abs(geom.area())
    #İzoperimetrik oran hesabı
    ci=izoper(area0,geom.length()) #4*math.pi*area0/geom.length()**2
    geom2, area, angle, width, height = geom.orientedMinimumBoundingBox()
    aorn=area0/area 
    if ci>=tol2 and ci <0.9999:
        r=(area0/math.pi)**0.5
        p0=geom.centroid().asPoint()
        rng=daireyap(p0,r,dr=dr)
        return QgsGeometry.fromPolygonXY([rng])
    elif aorn>=tol1 and aorn <0.9999:
        return geom2
    else:
        None
def sekilYap(lyr,tolR=0.95,tolC=0.95,dr=1,da=5):
    crs=lyr.crs()
    vl = QgsVectorLayer("MultiPolygon", "SekilYap", "memory")
    vl.setCrs(crs)
    pr = vl.dataProvider()
    # Mevcut kolonları taşıma
    pr.addAttributes(lyr.fields()) 
    vl.updateFields()
    for ft in lyr.getFeatures():
        geom=ft.geometry()
        #ilk şeklin alanı küçükse elimine et. 
        if geom.area()<=da:
            continue
        if geom.isMultipart():
            plgn = geom.asMultiPolygon()
        else: 
            plgn = [geom.asPolygon()]
        for i in range(len(plgn)):
            for j in range(len(plgn[i])):
                geom0=QgsGeometry.fromPolygonXY([plgn[i][j]])
                a0=geom0.area()
                #alt ring küçükse
                if a0<=da:
                    plgn[i][j]=None
                    continue
                geom1=makeRect(geom0,tol1=tolR,tol2=tolC,dr=dr)
                if geom1:
                    plgn[i][j]=geom1.asPolygon()[0]
            #Yukarıda None yapılanları atalım. 
            plgn[i]=[ii for ii in plgn[i] if ii]
        geomN=None
        for i in range(len(plgn)):
            if i==0:
                geomN=QgsGeometry.fromPolygonXY(plgn[i])
            elif geomN:
                geomi=QgsGeometry.fromPolygonXY(plgn[i])
                geomN.addPartGeometry(geomi)
        fet  = QgsFeature()
        fet.setGeometry(geomN)
        attr=[ft[i] for i in range(len(lyr.fields()))]
        fet.setAttributes(attr)
        pr.addFeatures([fet])
    vl.updateFields()
    return vl
def birlestir(lyr,bdist=2):
    #Buffer aşaması
    params0={
    'INPUT':lyr,
    'DISTANCE':bdist,
    'SEGMENTS':5,
    'END_CAP_STYLE':0,
    'JOIN_STYLE':1,
    'MITER_LIMIT':2,
    'DISSOLVE':False,
    'OUTPUT':'memory:'}
    lyr1 = processing.run("native:buffer", params0)['OUTPUT']
    #Birleştirme aşaması
    params1 = {
    'INPUT': lyr1,
    'OUTPUT': 'memory:', 
    'FIELD': [],  # You can specify field names to dissolve based on specific attributes
    'GEOMETRY': None,
    'SEPARATE_DISJOINT':True}
    lyr2=processing.run('native:dissolve', params1)['OUTPUT']
    #Ters buffer
    params3={
    'INPUT':lyr2,
    'DISTANCE':-bdist,
    'SEGMENTS':5,
    'END_CAP_STYLE':0,
    'JOIN_STYLE':1,
    'MITER_LIMIT':2,
    'DISSOLVE':False,
    'OUTPUT':'memory:'}
    lyr3 = processing.run("native:buffer", params3)['OUTPUT'] 
    #Parçalama
    params2 = {
    'INPUT': lyr3,
    'OUTPUT': 'memory:',
    'FIELD': [], 
    'GEOMETRY': None}
    lyr4=processing.run('native:multiparttosingleparts', params2)['OUTPUT']
    lyr4.setName('Birleştirilmiş')   
    return lyr4

def alan_eleme(lyr,a1=25,a2=156):
# Alan katmanında a1 den küçükleri siliyor. a2 den küçükleri ise
# küçükbina katmanına alıyor. 
    iar=False
    ian=False
    crs=lyr.crs()
    vl = QgsVectorLayer("Point", "Kucukbina", "memory")
    vl.setCrs(crs)
    pr = vl.dataProvider()
    # Mevcut kolonları taşıma
    pr.addAttributes(lyr.fields()) 
    field_names = [field.name() for field in lyr.fields()]
    if "Area" not in field_names:
        pr.addAttributes([QgsField("Area", QVariant.Double)])
        iar=True
    if "Angle" not in field_names:
        pr.addAttributes([QgsField("Angle", QVariant.Double)])
        ian=True
    vl.updateFields()
    idx_ar=vl.fields().indexOf('Area')
    idx_an=vl.fields().indexOf('Angle')
    #print(idx_ar,idx_an)
    for ft in lyr.getFeatures():
        geom=ft.geometry()
        #Alan küçükse ...
        if geom.area()<=a2:
            if geom.area()>=a1:
                fp=QgsFeature()
                geom2, area, angle, width, height = geom.orientedMinimumBoundingBox()
                fp.setGeometry(geom.centroid())
                attr=[ft[i] for i in range(len(lyr.fields()))]
                if iar:
                    attr.append(geom.area())
                else:
                    attr[idx_ar]=geom.area()
                if ian:
                    attr.append(angle)
                else:
                    attr[idx_an]=angle
                fp.setAttributes(attr)
                pr.addFeatures([fp])
            #şimdi alanı silelim
            lyr.dataProvider().deleteFeatures([ft.id()])
            lyr.updateFeature(ft)
    lyr.commitChanges() 
    lyr.updateExtents()    
    vl.commitChanges() 
    vl.updateExtents()
    return vl    


