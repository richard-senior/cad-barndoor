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

def cutSlot(sketch, slot_width, cx, cy, slot_radius, start_angle, arc_angle):
	# Calculate arc points
	arc_center = Base.Vector(cx, cy, 0)
	# create the arc slot
	# Part.ArcOfCircle(Part.Circle(center,axis,radius),startangle,endangle)
	geoList = []
	geoList.append(Part.ArcOfCircle(Part.Circle(arc_center, Base.Vector(0, 0, 1), slot_radius), start_angle, start_angle + arc_angle))
	geoList.append(Part.ArcOfCircle(Part.Circle(arc_center, Base.Vector(0, 0, 1), slot_radius - slot_width), start_angle, start_angle + arc_angle))
	# TODO rounded slot ends
	geoList.append(Part.LineSegment(
		Base.Vector(cx + slot_radius * math.cos(start_angle), cy + slot_radius * math.sin(start_angle), 0),
		Base.Vector(cx + (slot_radius - slot_width) * math.cos(start_angle), cy + (slot_radius - slot_width) * math.sin(start_angle), 0)))
	geoList.append(Part.LineSegment(
		Base.Vector(cx + slot_radius * math.cos(start_angle + arc_angle), cy + slot_radius * math.sin(start_angle + arc_angle), 0),
		Base.Vector(cx + (slot_radius - slot_width) * math.cos(start_angle + arc_angle), cy + (slot_radius - slot_width) * math.sin(start_angle + arc_angle), 0)))
	sketch.addGeometry(geoList, False)

# makes a whole of a given radius in the given sketch
# at the given centre x and y
def makeHole(sketch, cx, cy, radius):
	hole = sketch.addGeometry(Part.Circle(
		Base.Vector(cx, cy, 0),
		Base.Vector(0, 0, 1),
		radius
	), False)
	sketch.addConstraint(Sketcher.Constraint('Radius', hole, radius))
	return hole

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
	create_az_shoulder_bolt()
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
			top_diameter=16,
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


def create_az_flange(number):
	doc = App.ActiveDocument
	# Create a new sketch
	sketch = doc.addObject('Sketcher::SketchObject', "az_flange_" + str(number))

	# Calculate position and rotation
	# The slots are at SLOT_RADIUS (45mm) from center
	# The flange should align with the chord between slot ends at 90 degrees
	chord_length = 2 * SLOT_RADIUS * math.cos(math.pi/4)  # Distance between slot ends
	# Define dimensions
	width = chord_length   # width of rectangle - matches chord length
	height = 70  # height of rectangle
	cut = 30      # size of corner cut
	x = 35
	ra = -45
	if (number == 1):
		rotation = App.Rotation(App.Vector(1,0,0), 90)  # First rotation (to XZ)
		rotation = rotation.multiply(App.Rotation(App.Vector(0,1,0), ra))  # Second rotation (20° in XY)
		sketch.Placement = App.Placement(
			App.Vector(-1 * x, 0, DISK_THICKNESS * 2),  # Position: centered on chord, at disk height
			rotation
		)
	else:
		rotation = App.Rotation(App.Vector(1,0,0), 90)  # First rotation (to XZ)
		rotation = rotation.multiply(App.Rotation(App.Vector(0,1,0), ra))  # Same rotation as first flange
		sketch.Placement = App.Placement(
			App.Vector(0, x, DISK_THICKNESS * 2),  # Position: centered on chord, at disk height
			rotation
		)

	# Define vertices for rectangle with cut corner
	v1 = App.Vector(0, 0, 0)          # bottom left
	v2 = App.Vector(width, 0, 0)       # bottom right
	v3 = App.Vector(width, height-cut, 0)  # top right before cut
	v4 = App.Vector(width-cut, height, 0)  # top right after cut
	v5 = App.Vector(0, height, 0)      # top left

	# Add line segments using Part.LineSegment
	sketch.addGeometry(Part.LineSegment(v1, v2))  # bottom
	sketch.addGeometry(Part.LineSegment(v2, v3))  # right side
	sketch.addGeometry(Part.LineSegment(v3, v4))  # diagonal cut
	sketch.addGeometry(Part.LineSegment(v4, v5))  # top
	sketch.addGeometry(Part.LineSegment(v5, v1))  # left side

	# Add constraints
	# Connect all lines
	sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))  # v2
	sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1))  # v3
	sketch.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1))  # v4
	sketch.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 4, 1))  # v5
	sketch.addConstraint(Sketcher.Constraint("Coincident", 4, 2, 0, 1))  # back to v1

	# Add dimensions
	sketch.addConstraint(Sketcher.Constraint("Distance", 0, width))  # bottom width
	sketch.addConstraint(Sketcher.Constraint("Distance", 4, height))  # left height

	# pivot holes
	# Add a 10mm diameter hole near the 45-degree cut corner
	hole_radius = 3  # 10mm diameter = 5mm radius
	# Position the hole center 15mm from both edges (to leave enough material)
	hole_x = 10  # Move in from the cut corner
	hole_y = height - 10  # Move down from the top

	makeHole(sketch, hole_x, hole_y, hole_radius)
	slot_radius = 20
	slot_width = SLOT_WIDTH
	cutSlot(sketch, slot_width, hole_x, hole_y, slot_radius, -1.7, math.pi / 1.7)

	pad = doc.addObject("PartDesign::Pad", "az_flange_pad_" + str(number))
	pad.Profile = sketch
	pad.Length = DISK_THICKNESS
	if number == 1:
		pad.Reversed = True
	sketch.Visibility = False
	pad.Visibility = True
	pad.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray
	pad.ViewObject.Transparency = 70
	doc.recompute()

def create_alt_flange(number):
	doc = App.ActiveDocument
	# Create a new sketch
	sketch = doc.addObject('Sketcher::SketchObject', "alt_flange_" + str(number))

	# Define dimensions
	height = 35      # rectangle height
	width = 40      # rectangle width

	if number == 1:
		rotation = App.Rotation(App.Vector(1,0,0), 90)  # First rotation (to XZ)
		rotation = rotation.multiply(App.Rotation(App.Vector(0,1,0), -45))  # Second rotation (45° in XY)
		sketch.Placement = App.Placement(
			App.Vector(0, 0, 65),
			rotation
		)
	else:
		rotation = App.Rotation(App.Vector(1,0,0), 90)  # First rotation (to XZ)
		rotation = rotation.multiply(App.Rotation(App.Vector(0,1,0), -45))  # Second rotation (45° in XY)
		sketch.Placement = App.Placement(
			App.Vector(0, 45, 65),
			rotation
		)

	# Define vertices for rectangle (going clockwise from top left)
	v1 = App.Vector(0, height/2, 0)           # top left
	v2 = App.Vector(0, -height/2, 0)          # bottom left
	v3 = App.Vector(width, -height/2, 0)      # bottom right
	v4 = App.Vector(width, height/2, 0)       # top right

	# Add line segments in order
	lines = [
		Part.LineSegment(v1, v2),  # left vertical
		Part.LineSegment(v2, v3),  # bottom horizontal
		Part.LineSegment(v3, v4),  # right vertical
		Part.LineSegment(v4, v1)   # top horizontal
	]

	# Add all line segments to sketch
	for line in lines:
		sketch.addGeometry(line)

	# Add coincident constraints - ensuring each vertex connects properly
	for i in range(len(lines)):
		next_i = (i + 1) % len(lines)
		sketch.addConstraint(Sketcher.Constraint("Coincident", i, 2, next_i, 1))

	# Add horizontal/vertical constraints
	sketch.addConstraint(Sketcher.Constraint("Vertical", 0))    # left
	sketch.addConstraint(Sketcher.Constraint("Horizontal", 1))  # bottom
	sketch.addConstraint(Sketcher.Constraint("Vertical", 2))    # right
	sketch.addConstraint(Sketcher.Constraint("Horizontal", 3))  # top

	# Add dimensions
	sketch.addConstraint(Sketcher.Constraint("Distance", 0, height))    # height
	sketch.addConstraint(Sketcher.Constraint("Distance", 1, width))     # width

	# Create the pad
	pad = doc.addObject("PartDesign::Pad", "alt_flange_pad_" + str(number))
	pad.Profile = sketch
	pad.Length = DISK_THICKNESS
	sketch.Visibility = False
	pad.Visibility = True
	pad.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray

	doc.recompute()


try:
	FreeCADGui.ActiveDocument.ActiveView.setAnimationEnabled(False)
	create_top_az_disk()
	create_bottom_az_disk()
	create_az_flange(1)
	create_az_flange(2)
	create_alt_flange(1)
	create_alt_flange(2)
	FreeCADGui.ActiveDocument.ActiveView.setAnimationEnabled(True)
except Exception as e:
	print(f"Main execution error: {str(e)}")