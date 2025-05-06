import FreeCAD as App
import os
import Part
import math
import Draft
from FreeCAD import Base
import FreeCADGui
import FastenerBase
import FastenersCmd
import Sketcher  # Added this import
import os
import importSVG

DOCUMENT_NAME="BarnDoor"
# Dimensions in mm
DISK_DIAMETER = 100
DISK_THICKNESS = 6
TAPPING_SIZE_8 = 6.8
TAPPING_SIZE_6 = 5
SLOT_RADIUS = 45
SLOT_WIDTH=6

# global variable to hold the document
doc = None

# screw_maker = FastenersCmd.screwMaker
def exportSketch(sketch):
	__objs__ = [sketch]
	# Save the current placement
	original_placement = sketch.Placement

	# Temporarily reset to default orientation (XY plane)
	default_placement = App.Placement(
		Base.Vector(0, 0, 0),
		Base.Rotation(0, 0, 0, 1)  # Identity rotation
	)

	try:
		# Apply the default placement for export
		sketch.Placement = default_placement
		doc.recompute()  # Ensure the change takes effect

		# Use the user's home directory to ensure write permissions
		home_dir = os.path.expanduser("~")
		path = os.path.join(home_dir, "barndoor", "cad-barndoor", f"{sketch.Name}.svg")
		print("Exporting sketch to: " + path)

		importSVG.export(__objs__, path)
		print(f"Successfully exported to {path}")
	except Exception as e:
		print(f"Export error: {str(e)}")
		# Try alternative location directly in home directory
		alt_path = os.path.join(home_dir, f"{sketch.Name}.svg")
		print(f"Trying alternative path: {alt_path}")
		try:
			importSVG.export(__objs__, alt_path)
			print(f"Successfully exported to {alt_path}")
		except Exception as e2:
			print(f"Alternative export also failed: {str(e2)}")
	finally:
		# Restore the original placement
		sketch.Placement = original_placement
		doc.recompute()  # Ensure the restoration takes effect


def cutSlot(sketch, slot_width=6, cx=0, cy=0, slot_radius=40, start_angle=0, end_angle=180, direction=True):
	# Convert angles to radians
	sa = math.radians(start_angle)
	ea = math.radians(end_angle)

	# Calculate the outer and inner radii
	outer_radius = slot_radius
	inner_radius = slot_radius - slot_width

	# Calculate the points for the outer arc
	outer_start_x = cx + outer_radius * math.cos(sa)
	outer_start_y = cy + outer_radius * math.sin(sa)
	outer_end_x = cx + outer_radius * math.cos(ea)
	outer_end_y = cy + outer_radius * math.sin(ea)

	# Calculate the points for the inner arc
	inner_start_x = cx + inner_radius * math.cos(sa)
	inner_start_y = cy + inner_radius * math.sin(sa)
	inner_end_x = cx + inner_radius * math.cos(ea)
	inner_end_y = cy + inner_radius * math.sin(ea)

	# Calculate the centers for the end cap arcs
	end_cap_center_x = (outer_end_x + inner_end_x) / 2
	end_cap_center_y = (outer_end_y + inner_end_y) / 2

	start_cap_center_x = (outer_start_x + inner_start_x) / 2
	start_cap_center_y = (outer_start_y + inner_start_y) / 2

	# Define the slot profile as lines with arc connectors
	# The connector type depends on the direction parameter
	# 'a' for counterclockwise, 'c' for clockwise
	oc = "c" if direction else "a"
	ic = "a" if direction else "c"

	slot_lines = [
		# Outer arc
		{
			"sx": outer_start_x, "sy": outer_start_y,
			"ex": outer_end_x, "ey": outer_end_y,
			"cx": cx, "cy": cy,
			"connector": oc,
		},
		{
			"sx": outer_end_x, "sy": outer_end_y,
			"ex": inner_end_x, "ey": inner_end_y,
			"cx": end_cap_center_x, "cy": end_cap_center_y,
			"connector": "a"
		},
		{
			"sx": inner_start_x, "sy": inner_start_y,
			"ex": inner_end_x, "ey": inner_end_y,
			"cx": cx, "cy": cy,
			"connector": ic,
		},
		{
			"sx": inner_start_x, "sy": inner_start_y,
			"ex": outer_start_x, "ey": outer_start_y,
			"cx": start_cap_center_x, "cy": start_cap_center_y,
			"connector": "a"
		}
	]
	drawShape(sketch, lines=slot_lines, name="slot")


# makes a whole of a given radius in the given sketch
# at the given centre x and y
def makeHole(sketch, x=0, y=0, radius=5):
	hole = sketch.addGeometry(Part.Circle(
		Base.Vector(x, y, 0),
		Base.Vector(0, 0, 1),
		radius
	), False)
	sketch.addConstraint(Sketcher.Constraint('Radius', hole, radius))
	return hole

def moveObject(obj, x=0, y=0, z=0):
	"""
	Moves any FreeCAD object by the specified amounts along each axis

	Args:
		obj: The FreeCAD object to move (pad, part, body, etc.)
		x: Distance to move in X axis (default 0)
		y: Distance to move in Y axis (default 0)
		z: Distance to move in Z axis (default 0)
	"""
	# Check if the object has a Placement property
	if not hasattr(obj, "Placement"):
		print(f"Error: Object {obj.Name} does not have a Placement property")
		return

	current_placement = obj.Placement
	new_placement = App.Placement(
		Base.Vector(
			current_placement.Base.x + x,
			current_placement.Base.y + y,
			current_placement.Base.z + z
		),
		current_placement.Rotation  # Keep current rotation
	)
	obj.Placement = new_placement

	# Recompute the document to update the view
	doc.recompute()

def rotateObject(obj, plane='xy', angle=90):
	"""
	Rotates any FreeCAD object around the specified axis

	Args:
		obj: The FreeCAD object to rotate (pad, part, body, etc.)
		plane: Rotation plane ('xy', 'yz', or 'xz')
		angle: Rotation angle in degrees
	"""
	# Check if the object has a Placement property
	if not hasattr(obj, "Placement"):
		print(f"Error: Object {obj.Name} does not have a Placement property")
		return

	# Determine rotation axis based on plane
	rotation = None
	if plane == 'xz':
		rotation = App.Rotation(App.Vector(1, 0, 0), angle)  # Rotate around X axis
	elif plane == 'yz':
		rotation = App.Rotation(App.Vector(0, 1, 0), angle)  # Rotate around Y axis
	else:  # Default to xy plane
		rotation = App.Rotation(App.Vector(0, 0, 1), angle)  # Rotate around Z axis

	current_placement = obj.Placement
	new_placement = App.Placement(
		current_placement.Base,  # Keep current position
		rotation.multiply(current_placement.Rotation)  # Apply rotation
	)
	obj.Placement = new_placement

	# Recompute the document to update the view
	doc.recompute()

def rotateSketch(sketch, plane='xy', angle=90):
	"""
	Rotates a sketch into the XZ plane (90 degrees around X axis)
	Args:
		sketch: The sketch object to rotate
	"""
	rotation = None
	if plane == 'xz':
		rotation = App.Rotation(App.Vector(1,0,0), angle)
	elif plane =='xz':
		rotation = App.Rotation(App.Vector(0,1,0), angle)
	else:
		rotation = App.Rotation(App.Vector(0,0,1), angle)

	current_placement = sketch.Placement
	new_placement = App.Placement(
		current_placement.Base,  # Keep current position
		rotation.multiply(current_placement.Rotation)  # Apply rotation
	)
	sketch.Placement = new_placement

def moveSketch(sketch, x=0, y=0, z=0):
	"""
	Moves a sketch by the specified amounts along each axis
	Args:
		sketch: The sketch object to move
		x: Distance to move in X axis (default 0)
		y: Distance to move in Y axis (default 0)
		z: Distance to move in Z axis (default 0)
	"""
	current_placement = sketch.Placement
	new_placement = App.Placement(
		Base.Vector(
			current_placement.Base.x + x,
			current_placement.Base.y + y,
			current_placement.Base.z + z
		),
		current_placement.Rotation  # Keep current rotation
	)
	sketch.Placement = new_placement


def drawShape(sketch=None, lines=[], name="shape"):
	print("in drawshape")
	# Validate input
	if not lines or len(lines) < 2:
		print("Error: At least 2 points are required to create a sketch")
		return None

	if not sketch:
		sketch = doc.addObject("Sketcher::SketchObject", name)

	# Add segments connecting each point
	geometries = []
	for i in range(len(lines)):
		start_point = (lines[i].get("sx", 0), lines[i].get("sy", 0))
		end_point = (lines[i].get("ex", 0), lines[i].get("ey", 0))
		con = lines[i].get("connector")

		# Check if this segment should be an arc
		if con and con in "ac":
			# Get center if provided, otherwise calculate it
			center = None
			if "cx" in lines[i] and "cy" in lines[i]:
				center = Base.Vector(lines[i]["cx"], lines[i]["cy"], 0)

			# Convert tuple points to vectors
			start_vector = Base.Vector(start_point[0], start_point[1], 0)
			end_vector = Base.Vector(end_point[0], end_point[1], 0)

			# Calculate radius from center to start point
			dx = start_point[0] - center.x
			dy = start_point[1] - center.y
			radius = math.sqrt(dx**2 + dy**2)

			# Create a circle
			circle = Part.Circle(center, Base.Vector(0, 0, 1), radius)

			# Calculate angles for start and end points
			start_angle = math.atan2(start_point[1] - center.y, start_point[0] - center.x)
			end_angle = math.atan2(end_point[1] - center.y, end_point[0] - center.x)

			# Determine if arc should be counterclockwise (con == "a") or clockwise
			is_ccw = (con == "a")

			# Adjust angles based on direction
			if is_ccw:  # Counterclockwise
				if end_angle < start_angle:
					end_angle += 2 * math.pi  # Ensure end_angle > start_angle for CCW
			else:  # Clockwise
				if end_angle > start_angle:
					end_angle -= 2 * math.pi  # Ensure end_angle < start_angle for CW
				elif end_angle == start_angle:
					end_angle -= 2 * math.pi  # Full circle case

			# Create the arc directly using Part.ArcOfCircle
			arc = Part.ArcOfCircle(circle, start_angle, end_angle)

			# Add to sketch
			geo_idx = sketch.addGeometry(arc)

			# Add radius constraint for the arc
			#sketch.addConstraint(Sketcher.Constraint('Radius', geo_idx, radius))
		else:
			# Add line segment
			geo_idx = sketch.addGeometry(Part.LineSegment(
				Base.Vector(start_point[0], start_point[1], 0),
				Base.Vector(end_point[0], end_point[1], 0)
			))

			# Add distance constraint for the line if it's not too small
			dx = end_point[0] - start_point[0]
			dy = end_point[1] - start_point[1]
			length = math.sqrt(dx**2 + dy**2)
			if length > 0.1:  # Only add constraint if line is long enough
				sketch.addConstraint(Sketcher.Constraint('Distance', geo_idx, length))

		geometries.append(geo_idx)

	doc.recompute()
	return sketch

def draw_bolt(sections, name="cylinder_profile", start_y=0):
	profile_lines = []
	current_y = start_y
	prev_radius = None

	# Process each section to create the profile
	for i, section in enumerate(sections):
		# Get diameter and length from the section
		diameter = section.get('d', 10)  # Default to 10 if not specified
		length = section.get('l', 10)    # Default to 10 if not specified
		# Calculate radius
		radius = diameter / 2

		if i == 0:
			# First line: from bottom center to bottom right of first section
			profile_lines.append({"sx": 0, "sy": current_y, "ex": radius, "ey": current_y})
		else:
			# If this section has a different radius than the previous one,
			# add a horizontal line to create a step
			if radius != prev_radius:
				profile_lines.append({"sx": prev_radius, "sy": current_y, "ex": radius, "ey": current_y})

		# Line from bottom right to top right of this section
		profile_lines.append({"sx": radius, "sy": current_y, "ex": radius, "ey": current_y + length})

		# Update the current Y position
		current_y += length
		prev_radius = radius

		# If this is the last section, add line from top right to top center
		if i == len(sections) - 1:
			profile_lines.append({"sx": radius, "sy": current_y, "ex": 0, "ey": current_y})

	# Add closing line from top center back to bottom center
	profile_lines.append({"sx": 0, "sy": current_y, "ex": 0, "ey": start_y})

	# Draw the profile using drawShape
	sketch = drawShape(lines=profile_lines, name=name)

	doc.recompute()
	revolution = doc.addObject("Part::Revolution", name)
	revolution.Source = sketch
	revolution.Axis = Base.Vector(0.0, 1.0, 0.0)  # Y axis
	revolution.Base = Base.Vector(0.0, 0.0, 0.0)
	revolution.Angle = 360.0
	sketch.Visibility = False
	doc.recompute()
	# exportSketch(sketch)
	return revolution

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
	cutSlot(sketch, slot_width=SLOT_WIDTH, slot_radius=SLOT_RADIUS, start_angle=0, end_angle=90)
	cutSlot(sketch, slot_width=SLOT_WIDTH, slot_radius=SLOT_RADIUS, start_angle=180, end_angle=270)
	# rotate the disk allowing for easier placement of later components
	moveSketch(sketch, z=DISK_THICKNESS)
	rotateSketch(sketch, angle=45)

	# Extrude the sketch
	pad = doc.addObject("PartDesign::Pad", "top-az-disk-pad")
	pad.Profile = sketch
	pad.Length = DISK_THICKNESS
	sketch.Visibility = False
	pad.Visibility = True
	pad.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray
	doc.recompute()
	exportSketch(sketch)

def create_bottom_az_disk():
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
		makeHole(sketch, x=x, y=y, radius=MOUNT_THREAD_RADIUS)
		# we're going to rotate the sketch by 45 degrees so
		# we'll add the bolts in a pre-rotated orientation
		x = center_radius * math.cos(math.radians(angle + 45))
		y = center_radius * math.sin(math.radians(angle + 45))

	rotateSketch(sketch, angle=45)
	# Extrude the sketch
	pad = doc.addObject("PartDesign::Pad", "bottom-az-disk-pad")
	pad.Profile = sketch
	pad.Length = DISK_THICKNESS
	sketch.Visibility = False
	pad.Visibility = True
	pad.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray
	doc.recompute()
	exportSketch(sketch)

def create_az_flange(number):
	"""
	Creates an azimuth flange using drawShape for the profile.

	Args:
		number: Flange number (1 or 2)
	"""
	width = 70
	height = 70
	hole_radius = 5.01
	# Position the hole center 15mm from both edges (to leave enough material)
	hole_x = 25
	hole_y = height - 25
	slot_radius = 20
	cut = 20
	arc_radius = 25

	# Define the flange profile as lines with an arc in the top-left corner
	flange_lines = [
		# Bottom edge: bottom left to bottom right
		{"sx": 0, "sy": 0, "ex": width, "ey": 0},

		# Right edge: bottom right to top right before cut
		{"sx": width, "sy": 0, "ex": width, "ey": height-cut},

		# Cut edge: top right before cut to top right after cut
		{"sx": width, "sy": height-cut, "ex": width-cut, "ey": height},

		# Top edge: top right after cut to top left + arc_radius
		{"sx": width-cut, "sy": height, "ex": arc_radius, "ey": height},

		# Arc: from top edge to left edge (12 o'clock to 9 o'clock, anticlockwise)
		{"sx": arc_radius, "sy": height, "ex": 0, "ey": height - arc_radius, "connector": "a", "cx": arc_radius, "cy": height - arc_radius},

		# Left edge: arc end to bottom left
		{"sx": 0, "sy": height - arc_radius, "ex": 0, "ey": 0}
	]

	# Draw the flange profile using drawShape
	sketch = drawShape(lines=flange_lines, name="az_flange_" + str(number))
	makeHole(sketch, hole_x, hole_y, hole_radius)
	cutSlot(sketch, slot_width=SLOT_WIDTH, slot_radius=slot_radius, cx=hole_x, cy=hole_y, start_angle=250, end_angle=15)

	# Export the sketch before rotation for proper top view
	exportSketch(sketch)

	# Rotate the sketch to the XZ plane
	rotateSketch(sketch, plane='xz', angle=90)

	# Position the sketch based on the flange number
	if (number == 1):
		moveSketch(sketch, x=-width/2, y=-26, z=DISK_THICKNESS * 2)
	else:
		moveSketch(sketch, x=-width/2, y=26, z=DISK_THICKNESS * 2)

	# Create the pad
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
	return pad

def create_alt_flange(number):
	# Define dimensions
	height = 50      # rectangle height
	width = 50       # rectangle width
	hole_x = 25      # x position of the large hole
	hole_y = 0       # y position of the large hole

	# Define the flange profile as lines with an arc centered on the large hole
	flange_lines = [
		# Left edge: arc end to bottom left
		{"sx": 0, "sy": hole_y, "ex": 0, "ey": -height/2},

		# Bottom edge: bottom left to bottom right
		{"sx": 0, "sy": -height/2, "ex": width, "ey": -height/2},

		# Right edge: bottom right to top right
		{"sx": width, "sy": -height/2, "ex": width, "ey": height/2},

		# Top edge: top right to arc start
		{"sx": width, "sy": height/2, "ex": hole_x, "ey": height/2},

		# Arc: from top edge to left edge (12 o'clock to 9 o'clock, anticlockwise)
		{"sx": hole_x, "sy": height/2, "ex": 0, "ey": hole_y, "connector": "a", "cx": hole_x, "cy": hole_y}
	]

	# Draw the flange profile using drawShape
	sketch = drawShape(lines=flange_lines, name="alt_flange_" + str(number))

	# Add holes to the sketch
	makeHole(sketch, x=hole_x, y=hole_y, radius=5.01)
	makeHole(sketch, x=hole_x + 20 - (SLOT_WIDTH/2), y=hole_y, radius=TAPPING_SIZE_6 / 2)

	# Export the sketch before rotation for proper top view
	exportSketch(sketch)

	rotateSketch(sketch, plane='xz', angle=90)

	# Position the flange
	x = -width + 15
	#z = height + 7
	z=57
	if number == 1:
		moveSketch(sketch, x=x, y=20, z=z)
	else:
		moveSketch(sketch, x=x, y=-14, z=z)


	# Create the pad
	pad = doc.addObject("PartDesign::Pad", "alt_flange_pad_" + str(number))
	pad.Profile = sketch
	pad.Length = DISK_THICKNESS
	sketch.Visibility = False
	pad.Visibility = True
	pad.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray
	doc.recompute()
	return pad

def create_eq_base():
	# Define dimensions
	height = 50      # rectangle height
	width = 100       # rectangle width

	# Define the flange profile as lines with an arc centered on the large hole
	lines = [
        # Bottom edge: bottom left to bottom right
        {"sx": 0, "sy": 0, "ex": width, "ey": 0},

        # Right edge: bottom right to top right
        {"sx": width, "sy": 0, "ex": width, "ey": height},

        # Top edge: top right to top left
        {"sx": width, "sy": height, "ex": 0, "ey": height},

        # Left edge: top left to bottom left (closing line)
        {"sx": 0, "sy": height, "ex": 0, "ey": 0}
	]

	# Draw the flange profile using drawShape
	sketch = drawShape(lines=lines, name="eq_base")

	# Export the sketch before rotation for proper top view
	exportSketch(sketch)

	rotateSketch(sketch, plane='xy', angle=90)
	moveSketch(sketch, x=15, y=-50, z=82)

	# Create the pad
	pad = doc.addObject("PartDesign::Pad", "eq_base_pad")
	pad.Profile = sketch
	pad.Length = DISK_THICKNESS
	sketch.Visibility = False
	pad.Visibility = True
	pad.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray
	pad.ViewObject.Transparency = 70
	doc.recompute()
	return pad

def deleteExistingDocument(name):
	"""
	Deletes any existing document with the specified name
	Args:
		name: The name of the document to delete
	"""
	# Check if a document with this name already exists
	for doc in App.listDocuments().values():
		if doc.Name == name:
			print(f"Deleting existing document: {name}")
			App.closeDocument(name)
			break

try:
	# Delete existing document if it exists
	deleteExistingDocument(DOCUMENT_NAME)
	doc = App.newDocument(DOCUMENT_NAME)
	FreeCADGui.ActiveDocument.ActiveView.setAnimationEnabled(False)

	# create the central alt axis pin
	alt_axis = draw_bolt(sections=[{"d": 10, "l": 2}, {"d": 9.6, "l": 1.1}, {"d": 10, "l": 54}, {"d": 9.6, "l": 1.1}, {"d": 10, "l": 2}], name="alt_axis")
	moveObject(alt_axis, x=-10, y=-30, z=57)

	# create the central az axis shoulder bolt
	az_bolt = draw_bolt(sections=[{"d": TAPPING_SIZE_8, "l": 6},{"d": 10, "l": 6},{"d": 16, "l": 3}], name="az_axle")
	rotateObject(az_bolt, plane="xz", angle=90)

	# make the az disk clamp bolts
	az_clamp_bolt_1 = draw_bolt(sections=[{"d": TAPPING_SIZE_6, "l": 6},{"d": 6, "l": 6},{"d": 10, "l": 5}], name="az_clamp_bolt_1")
	rotateObject(az_clamp_bolt_1, plane="xz", angle=90)
	moveObject(az_clamp_bolt_1, y=42)
	az_clamp_bolt_2 = draw_bolt(sections=[{"d": TAPPING_SIZE_6, "l": 6},{"d": 6, "l": 6},{"d": 10, "l": 5}], name="az_clamp_bolt_2")
	rotateObject(az_clamp_bolt_2, plane="xz", angle=90)
	moveObject(az_clamp_bolt_2, y=-42)
	# now create the azimuth disks
	create_top_az_disk()
	create_bottom_az_disk()
	create_az_flange(1)
	create_az_flange(2)
	create_alt_flange(1)
	create_alt_flange(2)
	create_eq_base()
	FreeCADGui.ActiveDocument.ActiveView.setAnimationEnabled(True)
except Exception as e:
	print(f"Main execution error: {str(e)}")