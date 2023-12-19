
# First, required modules are loaded
#Author: Christian Croissant, CeMOS

import tempfile, shutil, os
from datetime import datetime
import pathlib
import re
# In[2]:

class mismaker():
    '''This class produces a *.mis-file in current working directory readable by flexImaging software
        
        - mandatory arguments:
        
        imagefilename:  str;    Path of image to register with the mis file
       
        - optional arguments:

        outputfilename: str;    path of the *.mis-file to save to (present will be overwritten)
                                anyway a *.mis-file is produced with leading datetime stamp
        
        defaultmethod:  str;    path to *.par or *.m-file representing a method to use with every area if not customized when adding each contour

        teachpoints:    list;   list of integers, shape 3*2*2 with positions of teachpoints, default to 0

        referencepoint: list;   list of integers, shape 2*2 with positions of a global reference point

        basegeometry:   str;    the base geometry accepted by flexImaging software when read from mis file. defaults to "MTP 384 ground steel.xeo"
        
        defaultlocalreference: list; of shape 2,2
        
        defaultraster:  list; defaults to 20,20

        defaultpolygontype: str; the polygons default type if not defined later when adding, defaults to "Area", could be "ROI" (case sensitive)
        '''  

    def __init__(self,imagefilename,outputfilename=None,defaultmethod=r"D:\method.m",teachpoints=None,referencepoint=None,basegeometry="MTP 384 ground steel.xeo",defaultlocalreference=[0,0],defaultraster=[20,20],defaultpolygontype="Area",defaultareaname=str("T"+datetime.now().strftime("%Y%m%d_%H%M%S"))):
        
        
        if teachpoints!=None and len(teachpoints)!=3:
            print("teach point pairs must be exactly 3 or none")
            teachpoints=[[[0,0][0,0]],[[0,0][0,0]],[[0,0][0,0]]]
            return 
        if referencepoint!=None and len(referencepoint)!=2:
            print("reference point has only x,y")
            referencepoint=[[0,0],[0,0]]
            return 
        self.outputfilename=outputfilename
        self.defaultmethod=defaultmethod
        self.imagefile=imagefilename
        self.teachpoints=teachpoints
        self.referencepoint=referencepoint
        self.basegeometry=basegeometry
        self.defaultlocalreference=defaultlocalreference
        self.defaultraster=defaultraster
        self.defaultpolygontype=defaultpolygontype
        self.defaultareaname=defaultareaname
        with tempfile.NamedTemporaryFile(mode='a+',delete=False) as self.vf:
            with open(self.vf.name, "a+") as filename:
                try:
                    date_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    print("""<ImagingSequence flexImagingVersion="5.0.80.0_1078_162" last_modified=\""""+ date_time +"""\">
<Comment></Comment>
<ResultDir></ResultDir>""",file=filename)
                    print("<Method>"+self.defaultmethod+"</Method>",file=filename)
                    print("<ImageFile>"+self.imagefile+"</ImageFile>",file=filename)
                    print("<OriginalImage>"+self.imagefile+"</OriginalImage>",file=filename)
                    print("<FilterList></FilterList>",file=filename)
                    print("<BaseGeometry>"+self.basegeometry+"</BaseGeometry>",file=filename)
                    print("""
<AreaColor>#c08080</AreaColor>
<RoiColor>#80c080</RoiColor>
<SpotColor>#8080c0</SpotColor>
<SystemType>0</SystemType>
<ParentMass></ParentMass>
<FragmentMass></FragmentMass>
<BlendImgRgn>40</BlendImgRgn>
<BlendImgRes>50</BlendImgRes>
<GradientMode>0</GradientMode>
<flexControlRunVersion>0.0.0.0</flexControlRunVersion>
<View Zoom="0" CenterPos="14550,5217" ShowImage="1" ShowImage2="0" ShowAreas="1" ShowRois="1" ShowTeachPoints="1" ShowRuler="1" ShowIntensity="0" ShowSpots="0" ShowSamplePos="0" ShowSpectra="1"></View>
<AutoScanParameters>
<MinMass>0</MinMass>
<MaxMass>0</MaxMass>
<WindowSize>0.5</WindowSize>
<Overlap>0.1</Overlap>
<MinPercent>10</MinPercent>
<MaxPercent>100</MaxPercent>
<MinRelIntens>0.2</MinRelIntens>
</AutoScanParameters>
<Preparation Mode="0"></Preparation>
<SpotOffset>0,0</SpotOffset>
<SpotDia>0</SpotDia>
<WasRunInc>0</WasRunInc>
<RunStep>2</RunStep>
<RunOrder>3</RunOrder>
<DoSourceCleaning>0</DoSourceCleaning>
<EjectTarget>0</EjectTarget>
<ProcessingParameters>
<DataSource>2</DataSource>
<DataPoints>8000</DataPoints>
<SmoothSpectrum>0</SmoothSpectrum>
<IcrThreshold>0.97</IcrThreshold>
<MinMass>0</MinMass>
<MaxMass>0</MaxMass>
<BaselineSub>1</BaselineSub>
<CacheData>0</CacheData>
<CacheValid>0</CacheValid>
<NormalizeSpectra>0</NormalizeSpectra>
<NormalizeMethod>0</NormalizeMethod>
<NormalizeNoiseThreshold>0.5</NormalizeNoiseThreshold>
</ProcessingParameters>
<HierarchClusteringParams>
<HCLRegionsOnly>0</HCLRegionsOnly>
<HCLSmoothing>lambda=0.1 iterations=10</HCLSmoothing>
<HCLBlackList></HCLBlackList>
<HCLWhiteList></HCLWhiteList>
<HCLMassTolerance>1e-010</HCLMassTolerance>
</HierarchClusteringParams>
<MDFParameters>
<MdfName></MdfName>
<MdfSource>1</MdfSource>
<MdfBaseMass>0</MdfBaseMass>
<MdfRangeHi>-1</MdfRangeHi>
<MdfRangeLo>-1</MdfRangeLo>
<MdfMinInt>0.02</MdfMinInt>
<MdfLlimit>0.025</MdfLlimit>
<MdfUlimit>0.025</MdfUlimit>
<MdfLslope>0</MdfLslope>
<MdfUslope>0</MdfUslope>
</MDFParameters>""",file=filename)
                    for tp in teachpoints:
                        print(tp)
                        print("<TeachPoint>"+str(tp[0][0])+","+str(tp[0][1])+";"+str(tp[1][0])+","+str(tp[1][0])+"</TeachPoint>",file=filename)
                    print("<ReferencePoint>"+str(referencepoint[0])+","+str(referencepoint[1])+"</ReferencePoint>", file=filename)
                    print("Mis initialized")
                except:
                    ("Filehandler not operateable")

    def load_mis(self,path,mode="add"):
        """loads existing *.mis-file, copies method as default for later "add_contours"
        existing file content will be copied until first appearance of an area
        defaults of initialization apply

        invoce "add_contours", save via "save_mis"
        
        parameter:
        path: str; path to existing *.mis-file
        mode: str; defaults to "add", can be "replace": defines if Areas/ROI already present should be kept"""
        if mode=="replace":
            print("Replacing mis content")
            firstarealine=None
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, 'tempfilename')
            shutil.copy2(path, temp_path)
            self.vf.close()
            with open(self.vf.name, "w") as write_file:

                with open(path, "r") as read_file:
                    for i, line in enumerate(read_file):
                        for match in re.finditer(re.compile("<Method>.+</Method>"), line):
                            matchgroup=match.group()[8:-9:1]
                            print("Found Method in Line", i+1, matchgroup)
                            self.defaultmethod=matchgroup

                        for match in re.finditer(re.compile("<Area Type=.+"), line):
                            print("Found first Area in Line", i+1, match.group())
                            firstarealine=i

                        if firstarealine==None:
                            print(line,file=write_file,end="")
                        else:
                            return
        elif mode=="add":
            print("Adding mis content")
            imagingsequenceendline=None
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, 'tempfilename')
            shutil.copy2(path, temp_path)
            self.vf.close()
            with open(self.vf.name, "w") as write_file:
                with open(path, "r") as read_file:
                    for i, line in enumerate(read_file):
                        for match in re.finditer(re.compile("<Method>.+</Method>"), line):
                            matchgroup=match.group()[8:-9:1]
                            print("Found Method in Line", i+1, matchgroup)
                            self.defaultmethod=matchgroup
                        for match in re.finditer(re.compile("</ImagingSequence>"), line):
                            print("Found end of Area and ROI definitions in Line", i+1, match.group())
                            imagingsequenceendline=i

                        if imagingsequenceendline==None:
                            print(line,file=write_file,end="")
                        else:
                            return


                    
                          

    def save_mis(self,name):
        with open(self.vf.name, "a+") as output_file:
            print("</ImagingSequence>",file=output_file)
        shutil.copy(self.vf.name,name)
        print("file saved as", str(os.getcwd()+"\\"+name))
        if self.outputfilename:
            shutil.copy(self.vf.name,self.outputfilename)
            print("file saved as", str(os.getcwd()+"\\"+self.outputfilename))
        self.vf.close()

    def _add_area_polygon(self,areaname,polygonpoints,method=None,raster=[10,10],localreference_xy=[0,0],polygontype="Area"):
        if method==None:
            method=self.defaultmethod
        if polygontype!="ROI":
            polygontype="Area"
        reference_x,reference_y=localreference_xy
        raster_x,raster_y=raster
        strHex = "%0.6X" % (int((255**3)/500)*4)
        with open(self.vf.name, "a+") as output_file:
            try:
                print('<'+polygontype+' Type="3" Name="'+areaname+'" Enabled="0" ShowSpectra="0" SpectrumColor="#'+ strHex.lower() +'">',file=output_file)
                print("<Raster>"+str(raster_x)+","+str(raster_y)+"</Raster>",file=output_file)
                print("<Method>"+str(method)+"</Method>",file=output_file)
                for p in polygonpoints[:]:
                    print("<Point>"+str(p[0]+reference_x)+","+str(p[1]+reference_y)+"</Point>",file=output_file)
                print("</"+polygontype+">",file=output_file)
            except:
                print("Something went wrong adding the single area", areaname)
            finally:
                pass

    def add_contours(self,contourdict):
        """contourdict:
            A dictionary of polygonal contours (list) [,and their parameters (dict) if different from initialisation]
            contourdict={"Name":{"contour":list([x,y]*n),"parameters":{"areaname": str,"method":str,"raster":[int,int]}}}
            available parameters: 
                areaname:           str;        is the name of the area, defaults to "Area i" wiht i=processed contours of the input
                method:             str;        is the method to use within the distinct area, defaults to initial method
                raster:             [int,int]   is the movement of the laser before each ablation
                localreference_xy:  [int,int]   is the offset to add to each point of the polygon, defaults to initialisation
        """
        defaultparameters={"method":self.defaultmethod,"reference_xy": self.defaultlocalreference,"raster":self.defaultraster,"polygontype":self.defaultpolygontype,"areaname":self.defaultareaname}
        parameters={}
        for k in contourdict.keys():
            try:
                parameters[k]=contourdict[k][parameters]
            except:
                break
            parameters.update() 
        filename=self.vf.name
       
        with open(filename, "a+") as self.output_file:
            for i,(k,v) in enumerate(contourdict.items()):
                currentparameters=defaultparameters.copy() #if accompanying parameters are missing
                if currentparameters["areaname"]==self.defaultareaname:
                    currentparameters["areaname"]=currentparameters["areaname"]+str(i)               
                contour=v["contour"]
                newparameters=contourdict.get(k)
                for parameterkey,_ in newparameters.items():   
                    currentparameters[parameterkey]=newparameters[parameterkey]
                self._add_area_polygon(currentparameters["areaname"],contour,currentparameters["method"],currentparameters["raster"],currentparameters["reference_xy"],currentparameters["polygontype"])
 