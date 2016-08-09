# -------------------------------------------------------------------------
# Name:        Data handling
# Purpose:     Transforming netcdf to numpy arrays, checking mask file
#
# Author:      PB
#
# Created:     13/07/2016
# Copyright:   (c) PB 2016
# -------------------------------------------------------------------------

import os
import calendar
import numpy as np
import globals
from management_modules.checks import *
from management_modules.replace_pcr import *
from messages import *

from pcraster import *
from pcraster.framework import *
from netCDF4 import Dataset,num2date,date2num,date2index


def valuecell(mask, coordx, coordstr):
    """
    to put a value into a pcraster map -> invert of cellvalue
    pcraster map is converted into a numpy array first
    """
    coord = []
    for xy in coordx:
        try:
            coord.append(float(xy))
        except:
            msg = "Gauges: " + xy + " in " + coordstr + " is not a coordinate"
            raise CWATMError(msg)

    null = np.zeros((pcraster.clone().nrRows(), pcraster.clone().nrCols()))
    null[null == 0] = -9999

    for i in xrange(int(len(coord) / 2)):
        col = int(
            (coord[i * 2] - pcraster.clone().west()) / pcraster.clone().cellSize())
        row = int(
            (pcraster.clone().north() - coord[i * 2 + 1]) / pcraster.clone().cellSize())
        #if col >= 0 and row >= 0 and col < pcraster.clone().nrCols() and row < pcraster.clone().nrRows():
        if col >= 0 and row >= 0 and col < pcraster.clone().nrCols() and row < pcraster.clone().nrRows():
            null[row, col] = i + 1
        else:
            msg = "Coordinates: " + str(coord[i * 2]) + ',' + str(
                coord[i * 2 + 1]) + " to put value in is outside mask map - col,row: " + str(col) + ',' + str(row)
            raise CWATMError(msg)

    map = numpy2pcr(Nominal, null, -9999)
    return map


def loadsetclone(name):
    """
    load the maskmap and set as clone
    """

    filename = binding[name]
    coord = filename.split()
    if len(coord) == 5:
        # changed order of x, y i- in setclone y is first in CWATM
        # settings x is first
        # setclone row col cellsize xupleft yupleft
        setclone(int(coord[1]), int(coord[0]), float(coord[2]), float(coord[3]), float(coord[4]))
        mapnp = np.ones((int(coord[1]), int(coord[0])))
        #mapnp[mapnp == 0] = 1
        map = numpy2pcr(Boolean, mapnp, -9999)

    elif len(coord) == 1:
        try:
            # try to read a pcraster map
            setclone(filename)
            map = boolean(readmap(filename))
            flagmap = True
            mapnp = pcr2numpy(map,np.nan)
        except:
            filename = os.path.splitext(binding[name])[0] + '.nc'
            try:
                nf1 = Dataset(filename, 'r')
            except:
                raise CWATMFileError(filename)

            value = nf1.variables.items()[-1][0]  # get the last variable name

            x1 = nf1.variables.values()[0][0]
            x2 = nf1.variables.values()[0][1]
            xlast = nf1.variables.values()[0][-1]
            y1 = nf1.variables.values()[1][0]
            ylast = nf1.variables.values()[1][-1]
            cellSize = round(np.abs(x2 - x1),4)
            nrRows = int(0.5+np.abs(ylast - y1) / cellSize + 1)
            nrCols = int(0.5+np.abs(xlast - x1) / cellSize + 1)
            x = x1 - cellSize / 2
            y = y1 + cellSize / 2

            mapnp = np.array(nf1.variables[value][0:nrRows, 0:nrCols])
            nf1.close()

            # setclone  row col cellsize xupleft yupleft
            setclone(nrRows,nrCols, cellSize, x, y)
            map = numpy2pcr(Boolean, mapnp, 0)
            #map = boolean(map)
            flagmap = True

        if Flags['check']:
            checkmap(name, filename, map, flagmap, 0)

    else:
        msg = "Maskmap: " + Mask + \
            " is not a valid mask map nor valid coordinates"
        raise CWATMError(msg)

    # Definition of cellsize, coordinates of the meteomaps and maskmap
    # need some love for error handling
    maskmapAttr['x'] = pcraster.clone().west()
    maskmapAttr['y'] = pcraster.clone().north()
    maskmapAttr['col'] = pcraster.clone().nrCols()
    maskmapAttr['row'] = pcraster.clone().nrRows()
    maskmapAttr['cell'] = pcraster.clone().cellSize()


    # put in the ldd map
    # if there is no ldd at a cell, this cell should be excluded from modelling
    ldd = loadmap('Ldd',pcr=True)
    maskldd = pcr2numpy(ldd,np.nan)
    maskarea = np.bool8(mapnp)
    mask = np.logical_not(np.logical_and(maskldd,maskarea))

#    mask=np.isnan(mapnp)
#    mask[mapnp==0] = True # all 0 become mask out
    mapC = np.ma.compressed(np.ma.masked_array(mask,mask))

    # Definition of compressed array and info how to blow it up again
    maskinfo['mask']=mask
    maskinfo['shape']=mask.shape
    maskinfo['maskflat']=mask.ravel()    # map to 1D not compresses
    maskinfo['shapeflat']=maskinfo['maskflat'].shape   #length of the 1D array
    maskinfo['mapC']=mapC.shape                        # length of the compressed 1D array
    maskinfo['maskall'] =np.ma.masked_all(maskinfo['shapeflat'])  # empty map 1D but with mask
    maskinfo['maskall'].mask = maskinfo['maskflat']

    globals.inZero=np.zeros(maskinfo['mapC'])

    return map


def loadmap(name,pcr=False, lddflag=False):
    """
    load a static map either value or pcraster map or netcdf
    """
    value = binding[name]
    filename = value
    pcrmap = False

    try:  # loading an integer or float but not a map
        mapC = float(value)
        flagmap = False
        load = True
        if pcr: map=mapC
    except ValueError:
        try:  # try to read a pcraster map
            map = readmap(value)
            flagmap = True
            load = True
            pcrmap = True
        except:
            load = False

    if load and pcrmap:  # test if map is same size as clone map, if not it will make an error
        try:
           test = pcraster.scalar(map) + pcraster.scalar(map)
        except:
           msg = value +" might be of a different size than clone size "
           raise CWATMError(msg)

    if not(load):   # read a netcdf  (single one not a stack)
        filename = os.path.splitext(value)[0] + '.nc'
         # get mapextend of netcdf map and calculate the cutting
        cut0, cut1, cut2, cut3 = mapattrNetCDF(filename)

        # load netcdf map but only the rectangle needed
        nf1 = Dataset(filename, 'r')
        value = nf1.variables.items()[-1][0]  # get the last variable name

        if not timestepInit:
            mapnp = nf1.variables[value][cut2:cut3, cut0:cut1]
        else:
            if 'time' in nf1.variables:
                timestepI = Calendar(timestepInit[0])
                if type(timestepI) is datetime.datetime:
                    timestepI = date2num(timestepI,nf1.variables['time'].units)
                else: timestepI = int(timestepI) -1

                if not(timestepI in nf1.variables['time'][:]):
                    msg = "time step " + str(int(timestepI)+1)+" not stored in "+ filename
                    raise CWATMError(msg)
                itime = np.where(nf1.variables['time'][:] == timestepI)[0][0]
                mapnp = nf1.variables[value][itime,cut2:cut3, cut0:cut1]
            else:
                mapnp = nf1.variables[value][cut2:cut3, cut0:cut1]

        try:
            if any(maskinfo): mapnp.mask = maskinfo['mask']
        except: x=1
        nf1.close()

        # if a map should be pcraster
        if pcr:
            # check if integer map (like outlets, lakes etc
            checkint=str(mapnp.dtype)
            if checkint=="int16" or checkint=="int32":
                mapnp[mapnp.mask]=-9999
                map = numpy2pcr(Nominal, mapnp, -9999)
            elif checkint=="int8":
                mapnp[mapnp<0]=-9999
                map = numpy2pcr(Nominal, mapnp, -9999)
            else:
                mapnp[np.isnan(mapnp)] = -9999
                map = numpy2pcr(Scalar, mapnp, -9999)

            # if the map is a ldd
            #if value.split('.')[0][:3] == 'ldd':
            if lddflag: map = ldd(nominal(map))

        else:
            mapC = compressArray(mapnp,pcr=False,name=filename)
        flagmap = True

    # pcraster map but it has to be an array
    if pcrmap and not(pcr):
        mapC = compressArray(map,name=filename)
    if Flags['check']:

        print name, filename
        if flagmap == False: checkmap(name, filename, mapC, flagmap, 0)
        elif pcr: checkmap(name, filename, map, flagmap, 0)
        else:
            print name, mapC.size
            if mapC.size >0:
                map= decompress(mapC)
                checkmap(name, filename, map, flagmap, 0)

    if pcr:  return map
    else: return mapC


# -----------------------------------------------------------------------
# Compressing to 1-dimensional numpy array
# -----------------------------------------------------------------------

def compressArray(map, pcr=True, name="None"):
    if pcr:
        mapnp = pcr2numpy(map, np.nan).astype(np.float64)
        mapnp1 = np.ma.masked_array(mapnp, maskinfo['mask'])
    else:
        mapnp1 = np.ma.masked_array(map, maskinfo['mask'])
    mapC = np.ma.compressed(mapnp1)
    # if fill: mapC[np.isnan(mapC)]=0
    if name != "None":
        if np.max(np.isnan(mapC)):
            msg = name + " has less valid pixels than area or ldd \n"
            raise CWATMError(msg)
            # test if map has less valid pixel than area.map (or ldd)
    return mapC

def decompress(map):
    # dmap=np.ma.masked_all(maskinfo['shapeflat'], dtype=map.dtype)
    dmap = maskinfo['maskall'].copy()
    dmap[~maskinfo['maskflat']] = map[:]
    dmap = dmap.reshape(maskinfo['shape'])

    # check if integer map (like outlets, lakes etc
    try:
        checkint = str(map.dtype)
    except:
        checkint = "x"

    if checkint == "int16" or checkint == "int32":
        dmap[dmap.mask] = -9999
        map = numpy2pcr(Nominal, dmap, -9999)
    elif checkint == "int8":
        dmap[dmap < 0] = -9999
        map = numpy2pcr(Nominal, dmap, -9999)
    else:
        dmap[dmap.mask] = -9999
        map = numpy2pcr(Scalar, dmap, -9999)

    return map




# -----------------------------------------------------------------------
# NETCDF
# -----------------------------------------------------------------------



def metaNetCDF():
    """
    get the map metadata from netcdf
    """

    try:
        nf1 = Dataset(binding['PrecipitationMaps'], 'r')
        for var in nf1.variables:
           metadataNCDF[var] = nf1.variables[var].__dict__
        nf1.close()
    except:
        msg = "Trying to get metadata from netcdf \n"
        raise CWATMFileError(binding['PrecipitationMaps'],msg)


def mapattrNetCDF(name):
    """
    get the map attributes like col, row etc from a ntcdf map
    and define the rectangular of the mask map inside the netcdf map
    """
    filename = os.path.splitext(name)[0] + '.nc'
    try:
        nf1 = Dataset(filename, 'r')
    except:
        msg = "Checking netcdf map \n"
        raise CWATMFileError(filename,msg)

    x1 = round(nf1.variables.values()[0][0],5)
    x2 = round(nf1.variables.values()[0][1],5)
    xlast = round(nf1.variables.values()[0][-1],5)
    y1 = round(nf1.variables.values()[1][0],5)
    ylast = round(nf1.variables.values()[1][-1],5)
    cellSize = round(np.abs(x2 - x1),5)
    nrRows = int(0.5+np.abs(ylast - y1) / cellSize + 1)
    nrCols = int(0.5+np.abs(xlast - x1) / cellSize + 1)
    x = x1 - cellSize / 2
    y = y1 + cellSize / 2
    nf1.close()

    cut0 = int(np.abs(maskmapAttr['x'] - x) / maskmapAttr['cell'])
    cut1 = cut0 + maskmapAttr['col']
    cut2 = int(np.abs(maskmapAttr['y'] - y) / maskmapAttr['cell'])
    cut3 = cut2 + maskmapAttr['row']

    if maskmapAttr['cell'] != cellSize:
        msg = "Cell size different in maskmap: " + \
            binding['MaskMap'] + " and: " + filename
        raise CWATMError(msg)

    return (cut0, cut1, cut2, cut3)

def readnetcdf(name, time):
    """
      load stack of maps 1 at each timestamp in netcdf format
    """

    #filename = name + ".nc"
    filename =  os.path.splitext(name)[0] + '.nc'
    # value = os.path.basename(name)

    number = time - 1
    try:
       nf1 = Dataset(filename, 'r')
    except:
        msg = "Netcdf map stacks: \n"
        raise CWATMFileError(filename,msg)

    value = nf1.variables.items()[-1][0]  # get the last variable name
    mapnp = nf1.variables[value][
        number, cutmap[2]:cutmap[3], cutmap[0]:cutmap[1]]
    nf1.close()

    mapC = compressArray(mapnp,pcr=False,name=filename)
    #map = decompress(mapC)
    #report(map, 'C:\work\output\out2.map')


    timename = os.path.basename(name) + str(time)
    if Flags['check']:
       map = decompress(mapC)
       checkmap(timename, filename, map, True, 1)
    return mapC


def readnetcdf2(name, date, useDaily='daily', value='None'):
    """
      load stack of maps 1 at each timestamp in netcdf format
    """

    #filename = name + ".nc"
    filename =  os.path.normpath(name)


    try:
       nf1 = Dataset(filename, 'r')
    except:
        msg = "Netcdf map stacks: \n"
        raise CWATMFileError(filename,msg)


    # date if used daily, monthly or yearly or day of year
    if useDaily == "DOY":  # day of year 1-366
        idx = date - 1
    else:
        if useDaily == "month":
           idx = int(date.month) - 1
        else:
           if useDaily == "yearly":
              date = datetime.datetime(date.year, int(1), int(1))
           if useDaily == "monthly":
              date = datetime.datetime(date.year, date.month, int(1))
           # A netCDF time variable object  - time index (in the netCDF file)
           nctime = nf1.variables['time']
           idx = date2index(date, nctime, calendar=nctime.calendar, select='exact')
    if value == "None":
        value = nf1.variables.items()[-1][0]  # get the last variable name
    mapnp = nf1.variables[value][idx, cutmap[2]:cutmap[3], cutmap[0]:cutmap[1]]
    nf1.close()

    mapC = compressArray(mapnp,pcr=False,name=filename)
    return mapC


def readnetcdfWithoutTime(name, value="None"):
    """
      load stack of maps in netcdf format
    """

    filename =  os.path.normpath(name)

    try:
       nf1 = Dataset(filename, 'r')
    except:
        msg = "Netcdf map stacks: \n"
        raise CWATMFileError(filename,msg)
    if value == "None":
        value = nf1.variables.items()[-1][0]  # get the last variable name

    mapnp = nf1.variables[value][cutmap[2]:cutmap[3], cutmap[0]:cutmap[1]]
    nf1.close()

    mapC = compressArray(mapnp,pcr=False,name=filename)
    return mapC




#def writenet(flag, inputmap, netfile, timestep, value_standard_name, value_long_name, value_unit, fillval, startdate, flagTime=True):
def writenetcdf(netfile,varname,varunits,inputmap, timeStamp, posCnt, flag,flagTime, nrdays=None):
    """
    write a netcdf stack
    """

    row = np.abs(cutmap[3] - cutmap[2])
    col = np.abs(cutmap[1] - cutmap[0])

    if flag == False:
        nf1 = Dataset(netfile, 'w', format='NETCDF4')

        # general Attributes
        nf1.settingsfile = os.path.realpath(sys.argv[1])
        nf1.date_created = xtime.ctime(xtime.time())
        nf1.Source_Software = 'CWATM Python'
        nf1.institution = binding ["institution"]
        nf1.title = binding ["title"]
        nf1.source = 'CWATM output maps'
        nf1.Conventions = 'CF-1.6'


        # Dimension
        if 'x' in metadataNCDF.keys():
            lon = nf1.createDimension('x', col)  # x 1000
            longitude = nf1.createVariable('x', 'f8', ('x',))
            for i in metadataNCDF['x']:
                exec('%s="%s"') % ("longitude." + i, metadataNCDF['x'][i])
        if 'lon' in metadataNCDF.keys():
            lon = nf1.createDimension('lon', col)
            longitude = nf1.createVariable('lon', 'f8', ('lon',))
            for i in metadataNCDF['lon']:
                exec('%s="%s"') % ("longitude." + i, metadataNCDF['lon'][i])
        if 'y' in metadataNCDF.keys():
            lat = nf1.createDimension('y', row)  # x 950
            latitude = nf1.createVariable('y', 'f8', ('y'))
            for i in metadataNCDF['y']:
                exec('%s="%s"') % ("latitude." + i, metadataNCDF['y'][i])
        if 'lat' in metadataNCDF.keys():
            lat = nf1.createDimension('lat', row)  # x 950
            latitude = nf1.createVariable('lat', 'f8', ('lat'))
            for i in metadataNCDF['lat']:
                exec('%s="%s"') % ("latitude." + i, metadataNCDF['lat'][i])

        # projection
        if 'laea' in metadataNCDF.keys():
            proj = nf1.createVariable('laea', 'i4')
            for i in metadataNCDF['laea']:
                exec('%s="%s"') % ("proj." + i, metadataNCDF['laea'][i])
        if 'lambert_azimuthal_equal_area' in metadataNCDF.keys():
            proj = nf1.createVariable('lambert_azimuthal_equal_area', 'i4')
            for i in metadataNCDF['lambert_azimuthal_equal_area']:
                exec('%s="%s"') % (
                    "proj." + i, metadataNCDF['lambert_azimuthal_equal_area'][i])


        # Fill variables
        cell = round(pcraster.clone().cellSize(),5)
        xl = round((pcraster.clone().west() + cell / 2),5)
        xr = round((xl + col * cell),5)
        yu = round((pcraster.clone().north() - cell / 2),5)
        yd = round((yu - row * cell),5)
        #lats = np.arange(yu, yd, -cell)
        #lons = np.arange(xl, xr, cell)
        lats = np.linspace(yu, yd, row, endpoint=False)
        lons = np.linspace(xl, xr, col, endpoint=False)

        latitude[:] = lats
        longitude[:] = lons

        if flagTime:
            nf1.createDimension('time', nrdays)
            time = nf1.createVariable('time', 'f8', ('time'))
            time.standard_name = 'time'
            time.units = 'Days since 1901-01-01'
            time.calendar = 'standard'


            if 'x' in metadataNCDF.keys():
               value = nf1.createVariable(varname, 'f4', ('time', 'y', 'x'), zlib=True,fill_value=1e20)
            if 'lon' in metadataNCDF.keys():
               value = nf1.createVariable(varname, 'f4', ('time', 'lat', 'lon'), zlib=True, fill_value=1e20)
        else:
          if 'x' in metadataNCDF.keys():
              value = nf1.createVariable(varname, 'f4', ('y', 'x'), zlib=True,fill_value=1e20)
          if 'lon' in metadataNCDF.keys():
              # for world lat/lon coordinates
              value = nf1.createVariable(varname, 'f4', ('lat', 'lon'), zlib=True, fill_value=1e20)


        value.standard_name= varname
        value.long_name= varname
        value.units= varunits

        for var in metadataNCDF.keys():
            if "esri_pe_string" in metadataNCDF[var].keys():
                value.esri_pe_string = metadataNCDF[var]['esri_pe_string']



    else:
        nf1 = Dataset(netfile, 'a')

    if flagTime:
        date_time = nf1.variables['time']
        nf1.variables['time'][posCnt-1] = date2num(timeStamp, date_time.units, date_time.calendar)



    mapnp = maskinfo['maskall'].copy()
    mapnp[~maskinfo['maskflat']] = inputmap[:]
    #mapnp = mapnp.reshape(maskinfo['shape']).data
    mapnp = mapnp.reshape(maskinfo['shape'])

    #date_time[posCnt] = date2num(timeStamp, date_time.units, date_time.calendar)


    if flagTime:
        #nf1.variables[prefix][flag, :, :] = mapnp
        nf1.variables[varname][posCnt -1, :, :] = (mapnp)
    else:
        # without timeflag
        #nf1.variables[prefix][:, :] = mapnp
        nf1.variables[varname][:, :] = (mapnp)

    nf1.close()
    flag = True

    return flag



# -----------------------------------------------------------------------
# Calendar routines
# -----------------------------------------------------------------------

def Calendar(input):
    """
    get the date from CalendarDayStart in the settings xml
    """
    try:
        date = float(input)
    except ValueError:
        d = input.replace('.', '/')
        d = d.replace('-', '/')
        year = d.split('/')[-1:]
        if len(year[0]) == 4:
            formatstr = "%d/%m/%Y"
        else:
            formatstr = "%d/%m/%y"
        if len(year[0]) == 1:
            d = d.replace('/', '.', 1)
            d = d.replace('/', '/0')
            d = d.replace('.', '/')
            print d
        date = datetime.datetime.strptime(d, formatstr)
        # value=str(int(date.strftime("%j")))
    return date

def checkifDate(start,end):

    begin = Calendar(binding['CalendarDayStart'])

    intStart,strStart = datetoInt(binding[start],True)
    intEnd,strEnd = datetoInt(binding[end],True)

    # test if start and end > begin
    if (intStart<0) or (intEnd<0) or ((intEnd-intStart)<0):
        strBegin = begin.strftime("%d/%m/%Y")
        msg="Start Date: "+strStart+" and/or end date: "+ strEnd + " are wrong!\n or smaller than the first time step date: "+strBegin
        raise CWATMError(msg)
    modelSteps.append(intStart)
    modelSteps.append(intEnd)

    if type(Calendar(binding['StepStart'])) is datetime.datetime:
        end_date = Calendar(binding['StepStart']) + datetime.timedelta(days=modelSteps[1])
    else:
        end_date = begin + datetime.timedelta(days=modelSteps[1])

    modelSteps.append(end_date)
    return


def datecheck( date, step):
    print date
    yearend = False
    if date.day == calendar.monthrange(date.year, date.month)[1]:
        monthend = True
        if date.month == 12:
            yearend = True
    else:
        monthend = False
    doy = date.strftime('%j')

    laststep = False
    if step == modelSteps[1]:
      laststep=True

    datelastmonth = datetime.datetime(year=modelSteps[2].year, month= modelSteps[2].month, day=1) - datetime.timedelta(days=1)
    datelastyear = datetime.datetime(year=modelSteps[2].year, month= 1, day=1) - datetime.timedelta(days=1)

    laststepmonthend = False
    laststepyearend = False
    if date == datelastmonth:
        laststepmonthend = True
    if date == datelastyear:
        laststepyearend = True

    #start = self._userModel.firstTimeStep()
    #end = self._userModel.nrTimeSteps()

    nrdays = modelSteps[1] - modelSteps[0] + 1


    return monthend, yearend, laststepmonthend, laststepyearend, laststep, nrdays


# -----------------------------------------
def getValDivZero(x,y,y_lim,z_def= 0.0):
  #-returns the result of a division that possibly involves a zero
  # denominator; in which case, a default value is substituted:
  # x/y= z in case y > y_lim,
  # x/y= z_def in case y <= y_lim, where y_lim -> 0.
  # z_def is set to zero if not otherwise specified
  return np.where(y > y_lim,x / np.maximum(y_lim,y),z_def)






def cc(self,h):
    res = globals.inZero.copy()
    np.put(res, self.var.waterBodyIndexC, h)
    return res
def ccp(self,h):
    res = globals.inZero.copy()
    np.put(res, self.var.waterBodyIndexC, h)
    report(decompress(res), "c:\work\output/h1.map")