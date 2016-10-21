# -------------------------------------------------------------------------
# Name:        Land Cover Type module
# Purpose:
#
# Author:      PB
#
# Created:     15/07/2016
# Copyright:   (c) PB 2016
# -------------------------------------------------------------------------

from management_modules.data_handling import *


class landcoverType(object):

    """
    # ************************************************************
    # *****  LAND COVER TYPE *************************************
    # ************************************************************
    """

    def __init__(self, landcoverType_variable):
        self.var = landcoverType_variable

# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

    def initial(self):
        """ initial part of the land cover type module
        """

        self.var.coverTypes= map(str.strip, binding["coverTypes"].split(","))

        landcoverPara = ['minTopWaterLayer','minCropKC','minInterceptCap','cropDeplFactor','fracVegCover','rootFraction1','rootFraction2',
                         'maxRootDepth', 'minSoilDepthFrac','maxSoilDepthFrac','interceptStor', 'topWaterLayer',
                         'interflow','arnoBeta',
                         'cropCoefficientNC_filename', 'interceptCapNC_filename','coverFractionNC_filename',]
        # arrays stored as list not as numpy, because it can contain strings, single parameters or arrays
        # list is filled with append afterwards
        for variable in landcoverPara: vars(self.var)[variable] = []

        # fraction of what type of irrigation area
        # fraction (m2) of a certain irrigation type over (only) total irrigation area ; will be assigned by the landSurface module
        # output variable per land cover class
        landcoverVars = ['irrTypeFracOverIrr','fractionArea','totAvlWater',
                         'effSatAt50',  'effPoreSizeBetaAt50', 'rootZoneWaterStorageMin','rootZoneWaterStorageRange',
                         'directRunoff','totalPotET','potBareSoilEvap','potTranspiration','availWaterInfiltration','interceptEvap','soilWaterStorage',
                         'infiltration','actBareSoilEvap','landSurfaceRunoff','actTransTotal',
                         'gwRecharge','interflow','actualET','interflowTotal','openWaterEvap','irrGrossDemand',
                         'interceptStor','topWaterLayer',
                         'totalPotentialGrossDemand','actSurfaceWaterAbstract','allocSurfaceWaterAbstract','potGroundwaterAbstract',
                         'percToGW','capRiseFromGW','netPercUpper','netPerc']
        # for 4 landcover types
        for variable in landcoverVars:  vars(self.var)[variable] = np.tile(globals.inZero,(4,1))




        soilVars = ['adjRoot','perc','capRise', 'soilStor','rootDepth']
        # For 3 soil layers and 4 landcover types
        for variable in soilVars:  vars(self.var)[variable]= np.tile(globals.inZero,(self.var.soilLayers,4,1))



        # set aggregated storages to zero
        self.var.landcoverSum = [ 'interceptStor', 'topWaterLayer','interflow',
                         'directRunoff', 'totalPotET', 'potBareSoilEvap', 'potTranspiration', 'availWaterInfiltration',
                         'interceptEvap', 'infiltration', 'actBareSoilEvap', 'landSurfaceRunoff', 'actTransTotal', 'gwRecharge',
                         'actualET','interflowTotal', 'topWaterLayer', 'openWaterEvap','capRiseFromGW','percToGW',
                         'irrGrossDemand','totalPotentialGrossDemand','actSurfaceWaterAbstract','allocSurfaceWaterAbstract','potGroundwaterAbstract']
        for variable in self.var.landcoverSum: vars(self.var)["sum_"+variable] = globals.inZero.copy()

        # for three soil layers
        soilVars = ['soilStor']
        for variable in soilVars: vars(self.var)["sum_" + variable] = np.tile(globals.inZero,(3,1))

        self.var.totalSoil = globals.inZero.copy()
        self.var.totalET = globals.inZero.copy()




        #-----------------------------------------------------------------------------------
        #Calculate the fraction of each individual land fraction
        #

        i = 0
        for coverType in self.var.coverTypes:
            frac = np.around(loadmap(coverType + "_fracVegCover"),decimals=5)
            #forest + grassland should be 1)
            if coverType == "grassland":
                frac = 1.0 - self.var.fracVegCover[0]
            self.var.fracVegCover.append(frac)
            #self.var.fracVegCover.append(loadmap(coverType + "_fracVegCover"))
        self.var.fracForestOrig = self.var.fracVegCover[0]
        self.var.fracGrasslandOrig = self.var.fracVegCover[1]

        #  rescales natural land cover fractions (make sure the total = 1)  #TODO
        # forest  = 0, grassland = 1, irrPaddy = 2 , irrnonpaddy = 3
        # fraction of land for irrigation
        irrigatedAreaFrac = self.var.fracVegCover[2] + self.var.fracVegCover[3]
        # Correction of forest and grassland by irrigation part: #have to think if irrigation should go at the same pecentage from forest
        # BETTER adjust these maps before !!!
        self.var.fracVegCover[0] = self.var.fracVegCover[0] * (1.0- irrigatedAreaFrac)
        self.var.fracVegCover[1] = self.var.fracVegCover[1] * (1.0- irrigatedAreaFrac)

        # fraction of what type of irrigation area
        self.var.irrTypeFracOverIrr[2] = self.var.fracVegCover[2] / np.maximum(1E-9,irrigatedAreaFrac)
        self.var.irrTypeFracOverIrr[3] = self.var.fracVegCover[3] / np.maximum(1E-9,irrigatedAreaFrac)




        # ----------------------------------------------------------
        # Load initial values and calculate basic soil parameters which are not changed in time

        i = 0
        for coverType in self.var.coverTypes:
            # other paramater values
            self.var.arnoBeta.append(loadmap(coverType + "_arnoBeta"))
            # b coefficient of soil water storage capacity distribution
            self.var.minTopWaterLayer.append(loadmap(coverType + "_minTopWaterLayer"))
            self.var.minCropKC.append(loadmap(coverType + "_minCropKC"))
            self.var.minInterceptCap.append(loadmap(coverType + "_minInterceptCap"))
            self.var.cropDeplFactor.append(loadmap(coverType + "_cropDeplFactor"))
            # parameter values

            self.var.rootFraction1.append(loadmap(coverType + "_rootFraction1"))
            self.var.rootFraction2.append(loadmap(coverType + "_rootFraction2"))
            self.var.maxRootDepth.append(loadmap(coverType + "_maxRootDepth"))
            self.var.minSoilDepthFrac.append(loadmap(coverType + "_minSoilDepthFrac"))
            self.var.maxSoilDepthFrac.append(loadmap(coverType + "_maxSoilDepthFrac"))

            # filenames
            self.var.cropCoefficientNC_filename.append(coverType + "_cropCoefficientNC")
            self.var.interceptCapNC_filename.append(coverType + "_interceptCapNC")
            self.var.coverFractionNC_filename.append(coverType + "_coverFractionNC")

            # init values
            self.var.interceptStor[i] = self.var.init_module.load_initial(coverType + "_interceptStor")
            self.var.topWaterLayer[i] = self.var.init_module.load_initial(coverType + "_topWaterLayer")
            self.var.interflow[i] = self.var.init_module.load_initial(coverType + "_interflow")

            for soilLayer in xrange(self.var.soilLayers):
                self.var.soilStor[soilLayer][i] = self.var.init_module.load_initial(coverType + "_soilStorage"+str(soilLayer+1))
                # summarize the following initial storages:
                self.var.sum_soilStor[soilLayer] += self.var.fracVegCover[i] * self.var.soilStor[soilLayer][i]

            # summarize the following initial storages:
            self.var.sum_interceptStor += self.var.fracVegCover[i] * self.var.interceptStor[i]
            self.var.sum_topWaterLayer += self.var.fracVegCover[i] * self.var.topWaterLayer[i]

            for soilLayer in xrange(self.var.soilLayers):
                self.var.sum_soilStor[soilLayer] = self.var.sum_soilStor[soilLayer] + self.var.soilStor[soilLayer][i] * self.var.fracVegCover[i]


            # Improved Arno's scheme parameters:
            if self.var.arnoBeta[i] == 0:
                self.var.arnoBeta[i] = np.minimum(10.0,
                    np.maximum(0.001, (self.var.maxSoilDepthFrac[i] - 1.) / (1. - self.var.minSoilDepthFrac[i]) + self.var.orographyBeta - 0.01))
            else:
                self.var.arnoBeta[i] = np.minimum(1.0,np.maximum(0.001, self.arnoBeta))
            # PB changed to max 1.0 #TODO
            #report(decompress(self.var.arnoBeta[i]), "C:\work\output\harno.map")


            self.var.rootZoneWaterStorageMin[i] = self.var.minSoilDepthFrac[i] * self.var.rootZoneWaterStorageCap
            self.var.rootZoneWaterStorageRange[i] = self.var.rootZoneWaterStorageCap - self.var.rootZoneWaterStorageMin[i]

            # scaleRootFractions
            rootFrac = np.tile(globals.inZero,(self.var.soilLayers,1))
            rootFrac[0] = 0.05/0.30 * self.var.rootFraction1[i]
            rootFrac[1] = 0.25/0.30 * self.var.rootFraction1[i]
            rootFrac[2] = self.var.rootFraction2[i]
            rootFracSum = np.sum(rootFrac,axis=0)
            for soilLayer in xrange(self.var.soilLayers):
                self.var.adjRoot[soilLayer][i] = rootFrac[soilLayer] / rootFracSum

           # calculate rootdepth for each soillayer and each land cover class
            self.var.rootDepth[0][i] = np.minimum(self.var.soildepth[0], self.var.maxRootDepth[i])
            self.var.rootDepth[1][i] = np.minimum(self.var.soildepth[1], np.maximum(0.,self.var.maxRootDepth[i] - self.var.soildepth[0]))
            self.var.rootDepth[2][i] = np.minimum(self.var.soildepth[2], np.maximum(0., self.var.maxRootDepth[i] - self.var.soildepth[1]))


            # ------------------------------------------
            # calculateTotAvlWaterCapacityInRootZone
            # total water capacity in the root zone (upper soil layers)
            # Note: This is dependent on the land cover type.

            h = np.tile(globals.inZero, (self.var.soilLayers, 1))
            for j in xrange(self.var.soilLayers):
                h[j] = np.maximum(0., self.var.effSatAtFieldCap[j] - self.var.effSatAtWiltPoint[j]) * \
                     (self.var.satVol[j] - self.var.resVol[j]) * self.var.rootDepth[j][i]

            self.var.totAvlWater[i] = np.sum(h,axis=0)
            self.var.totAvlWater[i] = np.minimum(self.var.totAvlWater[i], self.var.rootZoneWaterStorageCap)

            h0 = np.tile(globals.inZero, (self.var.soilLayers, 1))
            h1 = np.tile(globals.inZero, (self.var.soilLayers, 1))
            h2 = np.tile(globals.inZero, (self.var.soilLayers, 1))
            h3 = np.tile(globals.inZero, (self.var.soilLayers, 1))
            # calculateParametersAtHalfTranspiration(self, parameters):
            # average soil parameters at which actual transpiration is halved
            # calculateParametersAtHalfTranspiration(self, parameters):
            # average soil parameters at which actual transpiration is halved
            for j in xrange(self.var.soilLayers):
                h0[j] = self.var.storCap[j] * self.var.adjRoot[j][i]
                h1[j] = np.maximum(0., self.var.effSatAtFieldCap[j] - self.var.effSatAtWiltPoint[j]) * \
                     (self.var.satVol[j] - self.var.resVol[j]) * self.var.rootDepth[j][i]
                h2[j] = h0[j] * (self.var.matricSuction50 / self.var.airEntry[j]) ** (-1. / self.var.poreSizeBeta[j])
                h3[j] = h0[j] * self.var.poreSizeBeta[j]

            adjrootZoneWaterStorageCap = np.sum(h0 , axis=0)
            self.var.totAvlWater[i] = np.sum(h1,axis=0)
            self.var.totAvlWater[i] = np.minimum(self.var.totAvlWater[i], self.var.rootZoneWaterStorageCap)
            self.var.effSatAt50[i] = np.sum(h2 / adjrootZoneWaterStorageCap , axis=0)
            self.var.effPoreSizeBetaAt50[i] = np.sum(h3 / adjrootZoneWaterStorageCap, axis=0)

            i += 1



        self.var.landcoverSumSum = ['directRunoff', 'totalPotET', 'potTranspiration', "Precipitation", 'ETRef','gwRecharge','Runoff']
        for variable in self.var.landcoverSumSum:
            vars(self.var)["sumsum_" + variable] = globals.inZero.copy()
        i=1



    # --------------------------------------------------------------------------

    def dynamic_fracIrrigation(self):
        """ dynamic part of the land cover type module
            calculating fraction of land cover
        """

        if option['includeIrrigation'] and option['dynamicIrrigationArea']:
        # if first day of the year or first day of run


            if dateVar['newStart'] or  dateVar['newYear']:

               # updating fracVegCover of landCover (for historical irrigation areas, done at yearly basis)
               # read historical irrigation areas
               self.var.irrigationArea = 10000.0 *readnetcdf2(binding['historicalIrrigationArea'], dateVar['currDate'], "yearly")

               # area of irrigation is limited by cellArea
               self.var.irrigationArea = np.maximum(self.var.irrigationArea, 0.0)
               self.var.irrigationArea = np.minimum(self.var.irrigationArea, self.var.cellArea)

               # calculate fracVegCover (for irrigation only)
               # forest  = 0, grassland = 1, irrPaddy = 2 , irrnonpaddy = 3
               for i in[2,3]:
                   self.var.fractionArea[i] = self.var.irrTypeFracOverIrr[i] * self.var.irrigationArea   # unit: square m
                   self.var.fracVegCover[i] = np.minimum(1.0, self.var.fractionArea[i] / self.var.cellArea)  # unit: fraction
                   # avoiding small numbers
                   self.var.fracVegCover[i] = np.where(self.var.fracVegCover[i] > 0.001, self.var.fracVegCover[i], 0.0)

               irrigatedAreaFrac = self.var.fracVegCover[2] + self.var.fracVegCover[3]
               nonirrigatedAreaFrac = self.var.fracVegCover[0] + self.var.fracVegCover[1]
               totalAreafrac = irrigatedAreaFrac + nonirrigatedAreaFrac
               # Correction of forest and grassland by irrigation part: #have to think if irrigation should go at the same pecentage from forest
               # BETTER adjust these maps before !!!

               self.var.fracVegCover[0] = self.var.fracForestOrig * (1.0 - irrigatedAreaFrac)
               self.var.fracVegCover[1] = self.var.fracGrasslandOrig * (1.0- irrigatedAreaFrac)

               #for i in xrange(0,3):
               #    self.var.fracVegCover[i] = 0.0
               #    #self.var.fracVegCover[i] = self.var.fracVegCover[i]/totalAreafrac
               #self.var.fracVegCover[1] = 1.0
# --------------------------------------------------------------------------

    def dynamic(self):
        """ dynamic part of the land cover type module
            calculating soil for each land cover class
        """


        if option['calcWaterBalance']:
            preTopWaterLayer = self.var.sum_topWaterLayer.copy()
            preIntStor = self.var.sum_interceptStor.copy()
            preStor1 = self.var.sum_soilStor[0].copy()
            preStor2 = self.var.sum_soilStor[1].copy()
            preStor3 = self.var.sum_soilStor[2].copy()
            self.var.pretotalSoil = self.var.totalSoil.copy()


        coverNo = 0
        # update soil (loop per each land cover type):
        for coverType in self.var.coverTypes:
            #print coverNo,coverType
            self.var.evaporation_module.dynamic(coverType, coverNo)
            self.var.interception_module.dynamic(coverType, coverNo)
            self.var.soil_module.dynamic(coverType, coverNo)
            coverNo += 1


        # aggregated variables by fraction of land cover
        for variable in self.var.landcoverSum:
            vars(self.var)["sum_" + variable] = globals.inZero.copy()
            for No in xrange(4):
                vars(self.var)["sum_" + variable] += self.var.fracVegCover[No] * vars(self.var)[variable][No]

        soilVars = ['soilStor']
        for variable in soilVars:
            for i in xrange(self.var.soilLayers):
                vars(self.var)["sum_" + variable][i] = globals.inZero.copy()
                for No in xrange(4):
                    vars(self.var)["sum_" + variable][i] += self.var.fracVegCover[No] * vars(self.var)[variable][i][No]


        self.var.totalSoil = self.var.sum_interceptStor + self.var.sum_topWaterLayer + \
                             self.var.sum_soilStor[0] + self.var.sum_soilStor[1] + self.var.sum_soilStor[2]
        self.var.totalSto = self.var.SnowCover + self.var.sum_interceptStor + self.var.sum_topWaterLayer + \
                            self.var.sum_soilStor[0] + self.var.sum_soilStor[1] + self.var.sum_soilStor[2]
        self.var.totalET = self.var.sum_actTransTotal + self.var.sum_actBareSoilEvap + self.var.sum_openWaterEvap + self.var.sum_interceptEvap

        #print self.var.totalSoil,self.var.soilStor[0][1],self.var.soilStor[1][1], self.var.soilStor[2][1],
        i= 1


###--------------------------------------------------------------------
### DEBUG

        if option['calcWaterBalance']:
            self.var.waterbalance_module.waterBalanceCheck(
                [self.var.Rain,self.var.SnowMelt],  # In
                [self.var.sum_availWaterInfiltration,self.var.sum_interceptEvap],  # Out
                [preIntStor],   # prev storage
                [self.var.sum_interceptStor],
                "InterAll", False)

        if option['calcWaterBalance']:
            self.var.waterbalance_module.waterBalanceCheck(
                [self.var.sum_availWaterInfiltration,self.var.sum_capRiseFromGW,self.var.sum_irrGrossDemand],                             # In  self.var.irrGrossDemand
                [self.var.sum_directRunoff,self.var.sum_interflowTotal, self.var.sum_percToGW, \
                 self.var.sum_actTransTotal, \
                 self.var.sum_actBareSoilEvap,self.var.sum_openWaterEvap],                                                                # Out
                [preTopWaterLayer,preStor1,preStor2,preStor3],                                       # prev storage
                [self.var.sum_topWaterLayer,self.var.sum_soilStor[0], self.var.sum_soilStor[1], self.var.sum_soilStor[2]],
                "Soil_sum1", True)


        if option['calcWaterBalance']:
            self.var.waterbalance_module.waterBalanceCheck(
                [self.var.Rain,self.var.SnowMelt,self.var.sum_capRiseFromGW,self.var.sum_irrGrossDemand],                             # In  self.var.irrGrossDemand
                [self.var.sum_directRunoff,self.var.sum_interflowTotal, self.var.sum_percToGW, \
                 self.var.sum_actTransTotal, \
                 self.var.sum_actBareSoilEvap,self.var.sum_openWaterEvap, self.var.sum_interceptEvap],                                                                # Out
                [preTopWaterLayer,preStor1,preStor2,preStor3,preIntStor],                                       # prev storage
                [self.var.sum_topWaterLayer,self.var.sum_soilStor[0], self.var.sum_soilStor[1], self.var.sum_soilStor[2], self.var.sum_interceptStor],
                "Soil_sum2", False)

        if option['calcWaterBalance']:
            self.var.waterbalance_module.waterBalanceCheck(
                [self.var.Precipitation,self.var.sum_capRiseFromGW,self.var.sum_irrGrossDemand],                             # In
                [self.var.sum_directRunoff,self.var.sum_interflowTotal, self.var.sum_percToGW, \
                 self.var.sum_actTransTotal, \
                 self.var.sum_actBareSoilEvap,self.var.sum_openWaterEvap, self.var.sum_interceptEvap],                                                                # Out
                [self.var.prevSnowCover, preTopWaterLayer,preStor1,preStor2,preStor3,preIntStor],                                       # prev storage
                [self.var.SnowCover, self.var.sum_topWaterLayer,self.var.sum_soilStor[0], self.var.sum_soilStor[1], self.var.sum_soilStor[2], self.var.sum_interceptStor],
                "Soil_All", True)
        i = 1




        #a = decompress(self.var.sumsum_Precipitation)
        #b = cellvalue(a,81,379)
        #print self.var.sum_directRunoff
        #report(decompress(self.var.sumsum_Precipitation), "c:\work\output\Prsum.map")
        #report(decompress(self.var.sumsum_gwRecharge), "c:\work\output\gwrsum.map")



