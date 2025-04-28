import FreeCAD as App
import Part
import math
import Draft
from FreeCAD import Base
import FreeCADGui
import FastenerBase
import FastenersCmd
import Sketcher  # Added this import

DOCUMENT_NAME="BarnDoor1"
# Dimensions in mm
DISK_DIAMETER = 100
DISK_THICKNESS = 6
TAPPING_SIZE_8 = 6.8
TAPPING_SIZE_6 = 5
SLOT_RADIUS = 45
SLOT_WIDTH=6

# Create a new document
doc = App.newDocument(DOCUMENT_NAME)
screw_maker = FastenersCmd.screwMaker

def getDocumentName():
	return App.ActiveDocument.Name

def createSketch(name) -> 'Sketcher.SketchObject':
	# create a sketch oriented in the xy plane
	FreeCADGui.activateWorkbench("SketcherWorkbench")
	sketch = doc.addObject("Sketcher::SketchObject", name)
	sketch.Placement = Base.Placement(Base.Vector(0, 0, 0), Base.Rotation(0, 0, 0, 1))
	return sketch

def getSketch(name) -> 'Sketcher.SketchObject':
	return App.ActiveDocument.getObjectsByLabel(name)[0]

def getPadByName(name):
	return App.ActiveDocument.getObjectsByLabel(name)[0]

def getSketchFromPad(pad):
	if not pad: raise ValueError("must pass a pad")
	g = pad.Group
	for o in g:
		if str(type(o)) == "<class 'Sketcher.SketchObject'>":
			return o
	return None

def getConstraint(padName, constraintName):
	pad = getPadByName(padName)
	sketch = getSketchFromPad(pad)
	current = sketch.getDatum(constraintName)
	print(padName +"[" + constraintName + "] : " + str(current.Value))


def setConstraint(padName, constraintName, value, units):
	if not padName or not constraintName or not value or not units: raise ValueError("must pass sensible values")
	pad = getPadByName(padName)
	sketch = getSketchFromPad(pad)
	sketch.setDatum(constraintName, App.Units.Quantity(str(value) + ' ' + units))


def create_top_az_disk():
	doc = App.ActiveDocument
	# Create a new sketch
	sketch = doc.addObject('Sketcher::SketchObject', 'top_az_disk')
	sketch.MapMode = 'FlatFace'
	# Draw the main disk
	disk = sketch.addGeometry(Part.Circle(Base.Vector(0, 0, 0), Base.Vector(0, 0, 1), DISK_DIAMETER / 2), False)
	sketch.addConstraint(Sketcher.Constraint('Radius', disk, DISK_DIAMETER / 2))
	sketch.renameConstraint(disk, u'top-az-disk-radius')
	units = str(DISK_DIAMETER / 2) + ' mm'
	sketch.setDatum(disk, App.Units.Quantity(units))
	# Draw the center hole
	hole = sketch.addGeometry(Part.Circle(Base.Vector(0, 0, 0), Base.Vector(0, 0, 1), 10 / 2), False)
	sketch.addConstraint(Sketcher.Constraint('Radius', hole, 10 / 2))
	sketch.renameConstraint(hole, u'top-az-hole-radius')
	units = str(10 / 2) + ' mm'
	sketch.setDatum(hole, App.Units.Quantity(units))
	# Ensure both circles are centered at the same point
	sketch.addConstraint(Sketcher.Constraint('Coincident', disk, 3, hole, 3))
	# Draw two semicircular slots
	slot_radius = SLOT_RADIUS
	slot_width = SLOT_WIDTH
	arc_angle = math.pi / 2
	# Calculate arc points
	arc1_center = Base.Vector(0, 0, 0)
	# Create the arc slot
	geoList = []
	geoList.append(Part.ArcOfCircle(Part.Circle(arc1_center, Base.Vector(0, 0, 1), slot_radius), 0, arc_angle))
	geoList.append(Part.ArcOfCircle(Part.Circle(arc1_center, Base.Vector(0, 0, 1), slot_radius - slot_width), 0, arc_angle))
	# TODO rounded slot ends
	geoList.append(Part.LineSegment(Base.Vector(slot_radius, 0, 0), Base.Vector(slot_radius - slot_width, 0, 0)))
	geoList.append(Part.LineSegment(Base.Vector(slot_radius * math.cos(arc_angle), slot_radius * math.sin(arc_angle), 0), Base.Vector((slot_radius - slot_width) * math.cos(arc_angle), (slot_radius - slot_width) * math.sin(arc_angle), 0)))
	# Create the second arc slot
	geoList.append(Part.ArcOfCircle(Part.Circle(arc1_center, Base.Vector(0, 0, 1), slot_radius), math.pi, math.pi + arc_angle))
	geoList.append(Part.ArcOfCircle(Part.Circle(arc1_center, Base.Vector(0, 0, 1), slot_radius - slot_width), math.pi, math.pi + arc_angle))
	geoList.append(Part.LineSegment(Base.Vector(-slot_radius, 0, 0), Base.Vector(-slot_radius + slot_width, 0, 0)))
	geoList.append(Part.LineSegment(Base.Vector(-slot_radius * math.cos(arc_angle), -slot_radius * math.sin(arc_angle), 0), Base.Vector((-slot_radius + slot_width) * math.cos(arc_angle), (-slot_radius + slot_width) * math.sin(arc_angle), 0)))
	# Add geometry to the sketch
	sketch.addGeometry(geoList, False)
	sketch.Placement = App.Placement(App.Vector(0, 0, DISK_THICKNESS), App.Rotation(App.Vector(0,0,1),0))
	#sketch.addConstraint(Sketcher.Constraint('Coincident', arc1_index, 1, line1_index, 1))
	#sketch.addConstraint(Sketcher.Constraint('Coincident', arc1_index, 2, line1_index, 2))
	# Extrude the sketch
	pad = doc.addObject("PartDesign::Pad", "top-az-disk-pad")
	pad.Profile = sketch
	pad.Length = DISK_THICKNESS
	sketch.Visibility = False
	pad.Visibility = True
	pad.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray
	# move pad vertically by 6mm
	#pad.Placement = Base.Placement(Base.Vector(0, 0, DISK_THICKNESS), Base.Rotation(0, 0, 0, 1))
	doc.recompute()

def create_bottom_az_disk():
	doc = App.ActiveDocument
	# Create a new sketch
	sketch = doc.addObject('Sketcher::SketchObject', 'bottom_az_disk')
	sketch.MapMode = 'FlatFace'

	# Draw the main disk
	disk = sketch.addGeometry(Part.Circle(Base.Vector(0, 0, 0), Base.Vector(0, 0, 1), DISK_DIAMETER / 2), False)
	sketch.addConstraint(Sketcher.Constraint('Radius', disk, DISK_DIAMETER / 2))
	sketch.renameConstraint(disk, u'bottom-az-disk-radius')
	units = str(DISK_DIAMETER / 2) + ' mm'
	sketch.setDatum(disk, App.Units.Quantity(units))

	# Draw the center hole
	hole = sketch.addGeometry(Part.Circle(Base.Vector(0, 0, 0), Base.Vector(0, 0, 1), 10 / 2), False)
	sketch.addConstraint(Sketcher.Constraint('Radius', hole, TAPPING_SIZE_8 / 2))
	sketch.renameConstraint(hole, u'bottom-az-hole-radius')
	units = str(TAPPING_SIZE_8 / 2) + ' mm'
	sketch.setDatum(hole, App.Units.Quantity(units))
	# Ensure both circles are centered at the same point
	sketch.addConstraint(Sketcher.Constraint('Coincident', disk, 3, hole, 3))

	# Draw 4 equidistant holes around a circle of radius 30mm
	# These holes are for mounting to the tripod/pillar
	MOUNT_HOLE_RADIUS = 4
	MOUNT_THREAD_RADIUS = TAPPING_SIZE_6 / 2
	MOUNT_HOLE_DISTANCE = 30
	for i in range(4):
		angle = i * 90
		x = MOUNT_HOLE_DISTANCE * math.cos(math.radians(angle))
		y = MOUNT_HOLE_DISTANCE * math.sin(math.radians(angle))
		h = sketch.addGeometry(Part.Circle(Base.Vector(x, y, 0), Base.Vector(0, 0, 1), MOUNT_HOLE_RADIUS), False)
		sketch.addConstraint(Sketcher.Constraint('Radius', h, MOUNT_HOLE_RADIUS))
		#units = str(MOUNT_HOLE_RADIUS) + ' mm'

	# az rotation bolt tightening holes
	for i in range(2):
		angle = (i * 180) + SLOT_RADIUS
		#angle = i * 180
		center_radius = SLOT_RADIUS - (SLOT_WIDTH/2)  # Position holes at center of slot width
		x = center_radius * math.cos(math.radians(angle))
		y = center_radius * math.sin(math.radians(angle))
		h = sketch.addGeometry(Part.Circle(Base.Vector(x, y, 0), Base.Vector(0, 0, 1), MOUNT_THREAD_RADIUS), False)
		sketch.addConstraint(Sketcher.Constraint('Radius', h, MOUNT_THREAD_RADIUS))
		create_az_shoulder_bolt(
			x=x, y=y,
			top_diameter=10,
			top_length=5,
			middle_diameter=6,
			middle_length=6,
			bottom_diameter=6,
			bottom_length=6
		)

	# Extrude the sketch
	pad = doc.addObject("PartDesign::Pad", "bottom-az-disk-pad")
	pad.Profile = sketch
	pad.Length = DISK_THICKNESS
	sketch.Visibility = False
	pad.Visibility = True
	pad.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray
	doc.recompute()

def create_az_shoulder_bolt(
	top_diameter=16,    # default values match original
	top_length=5,
	middle_diameter=10,
	middle_length=6,
	bottom_diameter=8,
	bottom_length=6,
	x=0,
	y=0,
):

	# Create the three sections
	top_section = Part.makeCylinder(
		top_diameter/2,     # radius
		top_length,         # height
		Base.Vector(x,y,middle_length + bottom_length)  # position
	)

	middle_section = Part.makeCylinder(
		middle_diameter/2,  # radius
		middle_length,      # height
		Base.Vector(x,y,bottom_length)  # position
	)

	bottom_section = Part.makeCylinder(
		bottom_diameter/2,  # radius
		bottom_length,      # height
		Base.Vector(x,y,0)  # position
	)

	# Create the parts
	top_part = doc.addObject("Part::Feature", "bolt_top")
	top_part.Shape = top_section

	middle_part = doc.addObject("Part::Feature", "bolt_middle")
	middle_part.Shape = middle_section

	bottom_part = doc.addObject("Part::Feature", "bolt_bottom")
	bottom_part.Shape = bottom_section

	# Union the parts together
	fusion1 = doc.addObject("Part::Fuse", "fusion1")
	fusion1.Base = top_part
	fusion1.Tool = middle_part

	fusion2 = doc.addObject("Part::Fuse", "shoulder_bolt")
	fusion2.Base = fusion1
	fusion2.Tool = bottom_part

	# Hide intermediate parts
	top_part.Visibility = False
	middle_part.Visibility = False
	bottom_part.Visibility = False
	fusion1.Visibility = False

	# Set the color
	fusion2.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray

	doc.recompute()
	return fusion2

try:
	FreeCADGui.ActiveDocument.ActiveView.setAnimationEnabled(False)
	create_top_az_disk()
	create_bottom_az_disk()
	create_az_shoulder_bolt()
	FreeCADGui.ActiveDocument.ActiveView.setAnimationEnabled(True)
except Exception as e:
	print(f"Main execution error: {str(e)}")
