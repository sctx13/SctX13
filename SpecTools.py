# -*- coding: utf-8 -*-
"""
 This module offer simple function to retrieve informations from a spec file
"""
___author___   = 'Cédric Montero'
___contact___  = 'cedric.montero@esrf.fr'
___copyright__ = '2012, European Synchrotron Radiation Facility, ESRF'
___version___  = '0'

""" External modules (preliminary installation could be require) """
import specfile#ESRF module to explore Spec files (contact : jerome.kieffer@esrf.fr)
import datetime
import numpy
from collections import defaultdict # Used in detection of configuration of calibration

def get_NumberOfScans(sf):
	"""
	Get the number of scan (and mesh) of the specification file
	@type sf : specfile object from specfile module
	"""
	return sf.scanno()

def get_ScanValueInSpecHeaderComment(sf,scannumber,field):
	"""
	Retrieve the value of a scan comment field of a specified scan header
	@param  sf : specfile object from specfile module
	@type   sf : specfile object
	@param field : field to look for the value in the comments
	@type  field : string
	TODO : print a warning message for unexisting comment
	"""
	scan      = sf.select(str(scannumber))
	scan_head = scan.header('C')
	value     = scan_head[[x for x in range(len(scan_head)) if scan_head[x].split('=')[0] == field][0]].split('=')[1]
	return value

def get_ScanMeasurement(sf,scannumber,motorlabel):
	"""
	Retrieve the measurements of a motor label

	@param         sf: specfile object from specfile module 
	@type          sf: specfile object
	@param scannumber: number of the scan to read (search by '#S x' in the spec file)
	@type  scannumber: integer or string of the scan number
	@param motorlabel: label of the motor to read
	@type  motorlabel: string
	"""
	scan        = sf.select(str(scannumber))# Select the scan to look at
	data        = scan.data()# Get the data of this scan
	labels_list = scan.alllabels()# Get the motors labels of this scan
	pos_motor   = [idx for idx in range(len(labels_list)) if labels_list[idx] == motorlabel][0]
	if pos_motor == []:
		print 'ERROR : The motorlabel required does not exist in the list of the labels of this scan.'
	else:
		measurement = data[pos_motor]
	return measurement

def get_ScanMeasurementsAlongTime(sf,scannumber,motorlabel):
	"""
	Retrieve the measurements of a motor label against time
	@type sf : specfile object from specfile module
	@type scannumber : integer
	@type motorlabel : string
	"""
	#TODO : rewrite this function based on the get_ScanMeasurement function
	def get_SingleScanMeasurementAlongTime(scannumber):
		# Store the scan data:
		scan       = sf.select(str(scannumber))
		data       = scan.data()
		# Find 'Epoch' label and motorlabel column position:
		labelslist = scan.alllabels()
		pos_epoch  = [idx for idx in range(len(labelslist)) if labelslist[idx] == 'Epoch'][0]
		pos_motor  = [idx for idx in range(len(labelslist)) if labelslist[idx] == motorlabel][0]
		# Calculate time elements of the measurements:
		eptime     = sf.epoch() + numpy.array(data[pos_epoch,:])# Create a numpy 1D array with unix epoch time of each measurement
		schedule   = numpy.array([datetime.datetime.fromtimestamp(values) for values in eptime])# Create a numpy 1D array of datetime instant of each measurement
		if pos_motor == []:
			print 'ERROR : The motorlabel required does not exist in the list of the labels of this scan.'
		else:
			measurement = data[pos_motor]
		return schedule,measurement
	if scannumber == '*':
		schedule    = numpy.array([])
		measurement = numpy.array([])
		for scan in range(1,get_NumberOfScans(sf)+1):
			scan_schedule,scan_measurement = get_SingleScanMeasurementAlongTime(scan)
			schedule = numpy.hstack((schedule,scan_schedule))
			measurement = numpy.hstack((measurement,scan_measurement))
	else:
		schedule,measurement = get_SingleScanMeasurementAlongTime(scannumber)
	return schedule,measurement

def get_ScanExposureTime(sf,scannumber):
	"""
	Return the exposure time of the scan
	"""
	scan       = sf.select(str(scannumber))
	time_field = scan.header('T')
	expo_time  = float(time_field[0].split(' ')[1])
	return expo_time

def get_ScanCommandType(sf,scannumber):
	"""
	Return the scan command type (scan, mesh, loopscan...)
		. Relative scan to actual position (like ascan or dmesh) are automatically transcripted in absolute positions by spec
	"""
	specscan = sf.select(str(scannumber))
	scan_command_type = specscan.header('S')[0].split()[2]
	return scan_command_type	

def get_ScanCommandField(sf,scannumber):
	"""
	Return the command line of the scan
	"""
	specscan = sf.select(str(scannumber))
	scan_command_field = specscan.header('S')
	return scan_command_field

def get_MeshShape(sf,scannumber):
	"""
	Return the shape of the expected scan or mesh (if not user interupted)
	"""
	specscan = sf.select(str(scannumber))
	scan_command_type = specscan.header('S')[0].split()[2]
	if scan_command_type == 'mesh' or 'amesh':
		Elements_In_Scan_Command = specscan.header('S')[0].split()
		MeshShape = list([int(Elements_In_Scan_Command[6]) + 1 , int(Elements_In_Scan_Command[10]) + 1 ])
	return MeshShape
 
def get_ExpectedFilesOfScan(sf,scannumber):
	"""
	Return the expexted number of files of the scan or mesh (if not user interrupted)
	"""
	specscan = sf.select(str(scannumber))
	scan_command_type = specscan.header('S')[0].split()[2]
	if scan_command_type == 'mesh' or 'amesh':
		Elements_In_Scan_Command = specscan.header('S')[0].split()
        Expected_InFiles = (int(Elements_In_Scan_Command[6]) + 1) * (int(Elements_In_Scan_Command[10]) + 1)
	return Expected_InFiles

def get_CalibrationScan(sf,scannumber):
	"""
	Find the binning, the exposure time and the nominal distance of a scan
	"""
	nominal_dist = float(get_ScanValueInSpecHeaderComment(sf,scannumber,'#C qq.adet.nominaldist'))
	expo_time    = get_ScanExposureTime(sf,scannumber)
	det_bin_row  = int(get_ScanValueInSpecHeaderComment(sf,scannumber,'#C qq.adet.rowbin'))
	det_bin_col  = int(get_ScanValueInSpecHeaderComment(sf,scannumber,'#C qq.adet.colbin'))
	det_binning  = (det_bin_row,det_bin_col) 
	calib_config = (nominal_dist,det_binning,expo_time)	
	return calib_config


def findCalibrationConfigs(sf):
	"""
	Find the nominal detector distance, detector binning and exposure time combinations for calibration scripts
	"""
	scan_numbers = get_ScanNumbers(sf)
	calib_config = {}# Create a dictionnary with all the configurations of the scans
	# Get the configuration for calibration on each scan
	for sc in range(1,scan_numbers+1):
		nominal_dist = float(get_ScanValueInSpecHeaderComment(sf,sc,'#C qq.adet.nominaldist'))
		expo_time    = get_ScanExposureTime(sf,sc)
		det_bin_row  = get_ScanValueInSpecHeaderComment(sf,sc,'#C qq.adet.rowbin')
		det_bin_col  = get_ScanValueInSpecHeaderComment(sf,sc,'#C qq.adet.colbin')
		if det_bin_row != det_bin_col:
			print 'Warning : row binning differs with column binning.'
		det_binning = (int(det_bin_row) + int(det_bin_row))	/ 2
		calib_config[sc] = (nominal_dist,det_binning,expo_time)
		print calib_config[sc]
	# Create a reversed dictionnary for each configuration as keys and scans as values
	config_calib = defaultdict(list)
	for k,v in calib_config.iteritems():
		config_calib[v].append(k)
	return config_calib.items()

def get_EnergyOfScan(sf,scannumber):
	#Energy is set in [keV]
	return float(get_ScanValueInSpecHeaderComment(sf,scannumber,'#C qq.mono.energy'))
def get_WavelengthOfScan(sf,scannumber):
	# Wavelength is written in [angström] and is returned in [nm]
	return float(get_ScanValueInSpecHeaderComment(sf,scannumber,'#C qq.mono.lambda'))/10	
