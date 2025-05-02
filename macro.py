import FreeCAD as App
import Part
import math
import Draft
from FreeCAD import Base
import FreeCADGui
import FastenerBase
import FastenersCmd
import Sketcher  # Added this import
import os

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

def cutSlot(sketch, slot_width=6, cx=0, cy=0, slot_radius=40, start_angle=0, end_angle=180):
	# angles in degrees, so convert to rads
	sa = math.radians(start_angle)
	ea = math.radians(end_angle)
	# Calculate arc points
	arc_center = Base.Vector(cx, cy, 0)
	# create the arc slot
	# Part.ArcOfCircle(Part.Circle(center,axis,radius),startangle,endangle)
	geoList = []
	geoList.append(Part.ArcOfCircle(Part.Circle(arc_center, Base.Vector(0, 0, 1), slot_radius), sa, ea))
	geoList.append(Part.ArcOfCircle(Part.Circle(arc_center, Base.Vector(0, 0, 1), slot_radius - slot_width), sa, ea))
	# TODO rounded slot ends
	geoList.append(Part.LineSegment(
		Base.Vector(cx + slot_radius * math.cos(sa), cy + slot_radius * math.sin(sa), 0),
		Base.Vector(cx + (slot_radius - slot_width) * math.cos(sa), cy + (slot_radius - slot_width) * math.sin(sa), 0)))

	# End point connection
	geoList.append(Part.LineSegment(
		Base.Vector(cx + slot_radius * math.cos(ea), cy + slot_radius * math.sin(ea), 0),
		Base.Vector(cx + (slot_radius - slot_width) * math.cos(ea), cy + (slot_radius - slot_width) * math.sin(ea), 0)))

	sketch.addGeometry(geoList, False)

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

def addArcSegment(sketch, start_point, end_point, radius=None, center=None):
	"""
	Adds an arc segment to a sketch between two points.

	Args:
		sketch: The sketch object to add the arc to
		start_point: Starting point (x,y) tuple or Base.Vector
		end_point: Ending point (x,y) tuple or Base.Vector
		radius: Optional radius of the arc
		center: Optional center point of the arc

	Returns:
		Index of the created geometry
	"""
	# Convert tuples to vectors if needed
	if isinstance(start_point, tuple):
		start_point = Base.Vector(start_point[0], start_point[1], 0)
	if isinstance(end_point, tuple):
		end_point = Base.Vector(end_point[0], end_point[1], 0)

	# If center is not provided, we need to calculate it
	if center is None:
		if radius is None:
			# Without radius or center, create a default arc (semi-circle)
			mid_point = Base.Vector(
				(start_point.x + end_point.x) / 2,
				(start_point.y + end_point.y) / 2,
				0
			)

			# Calculate perpendicular direction for center
			direction = Base.Vector(end_point.x - start_point.x, end_point.y - start_point.y, 0)
			perpendicular = Base.Vector(-direction.y, direction.x, 0)
			perpendicular.normalize()

			# Distance between points
			chord_length = ((end_point.x - start_point.x)**2 + (end_point.y - start_point.y)**2)**0.5

			# For a semi-circle, the center is at distance r from midpoint
			# where r = chord_length/2
			center = mid_point.add(perpendicular.multiply(chord_length/2))
			radius = chord_length/2
		else:
			# With radius but no center, we need to find the center
			# This is a bit more complex - we need to find a point that is
			# radius distance from both start and end points

			# First find midpoint of the chord
			mid_point = Base.Vector(
				(start_point.x + end_point.x) / 2,
				(start_point.y + end_point.y) / 2,
				0
			)

			# Calculate perpendicular direction
			direction = Base.Vector(end_point.x - start_point.x, end_point.y - start_point.y, 0)
			perpendicular = Base.Vector(-direction.y, direction.x, 0)
			perpendicular.normalize()

			# Distance between points
			chord_length = ((end_point.x - start_point.x)**2 + (end_point.y - start_point.y)**2)**0.5

			# Calculate how far from midpoint the center is
			# Using Pythagoras: radius² = (chord_length/2)² + h²
			# where h is the height we need to calculate
			if radius < chord_length/2:
				# Radius too small to create an arc between these points
				print("Error: Radius too small to create arc between points")
				return None

			h = (radius**2 - (chord_length/2)**2)**0.5

			# Center is h units from midpoint in perpendicular direction
			center = mid_point.add(perpendicular.multiply(h))

	# Create the circle that our arc will be part of
	circle = Part.Circle(center, Base.Vector(0, 0, 1), radius)

	# Calculate the angles for start and end points
	start_angle = circle.parameter(start_point)
	end_angle = circle.parameter(end_point)

	# Create the arc
	arc = Part.ArcOfCircle(circle, start_angle, end_angle)

	# Add to sketch
	return sketch.addGeometry(arc)

def drawShape(points, name="shape"):
	# Validate input
	if not points or len(points) < 2:
		print("Error: At least 2 points are required to create a sketch")
		return None

	sketch = doc.addObject("Sketcher::SketchObject", name)

	# Add segments connecting each point
	geometries = []
	for i in range(len(points) - 1):
		start_point = (points[i].get("x", 0), points[i].get("y", 0))
		end_point = (points[i+1].get("x", 0), points[i+1].get("y", 0))

		# Check if this segment should be an arc
		if points[i+1].get("connector") == "a":
			# Get center if provided, otherwise pass None
			center = None
			if "cx" in points[i+1] and "cy" in points[i+1]:
				center = Base.Vector(points[i+1]["cx"], points[i+1]["cy"], 0)

			# Calculate radius if center is provided
			radius = None
			if center:
				# Calculate radius from center to start point
				dx = start_point[0] - center.x
				dy = start_point[1] - center.y
				radius = (dx**2 + dy**2)**0.5

			# Add arc segment
			geo_idx = addArcSegment(sketch, start_point, end_point, radius, center)
		else:
			# Add line segment
			geo_idx = sketch.addGeometry(Part.LineSegment(
				Base.Vector(start_point[0], start_point[1], 0),
				Base.Vector(end_point[0], end_point[1], 0)
			))

		geometries.append(geo_idx)

	# Check if the shape is already closed
	first_x = points[0].get("x", 0)
	first_y = points[0].get("y", 0)
	last_x = points[-1].get("x", 0)
	last_y = points[-1].get("y", 0)

	# If not closed, add a final segment to close the shape
	if first_x != last_x or first_y != last_y:
		# Check if the closing segment should be an arc
		if points[0].get("connector") == "a":
			# Get center if provided, otherwise pass None
			center = None
			if "cx" in points[0] and "cy" in points[0]:
				center = Base.Vector(points[0]["cx"], points[0]["cy"], 0)

			# Calculate radius if center is provided
			radius = None
			if center:
				# Calculate radius from center to end point
				dx = last_x - center.x
				dy = last_y - center.y
				radius = (dx**2 + dy**2)**0.5

			# Add arc segment
			geo_idx = addArcSegment(sketch, (last_x, last_y), (first_x, first_y), radius, center)
		else:
			# Add line segment
			geo_idx = sketch.addGeometry(Part.LineSegment(
				Base.Vector(last_x, last_y, 0),
				Base.Vector(first_x, first_y, 0)
			))

		geometries.append(geo_idx)

	# Add coincident constraints between segments
	for i in range(len(geometries) - 1):
		sketch.addConstraint(Sketcher.Constraint("Coincident", geometries[i], 2, geometries[i+1], 1))

	# Close the loop with a constraint if we have more than one segment
	if len(geometries) > 1:
		sketch.addConstraint(Sketcher.Constraint("Coincident", geometries[-1], 2, geometries[0], 1))

	# Add geometric constraints for line segments (but avoid redundant constraints)
	added_horizontal = set()
	added_vertical = set()

	for i, geo_idx in enumerate(geometries):
		geo = sketch.Geometry[geo_idx]

		# Only apply horizontal/vertical constraints to line segments
		if isinstance(geo, Part.LineSegment):
			start = geo.StartPoint
			end = geo.EndPoint

			# Check if line is horizontal or vertical (with small tolerance)
			dx = abs(end.x - start.x)
			dy = abs(end.y - start.y)

			if dx < 0.001 and dy > 0.001 and geo_idx not in added_vertical:  # Vertical line
				sketch.addConstraint(Sketcher.Constraint("Vertical", geo_idx))
				added_vertical.add(geo_idx)
			elif dy < 0.001 and dx > 0.001 and geo_idx not in added_horizontal:  # Horizontal line
				sketch.addConstraint(Sketcher.Constraint("Horizontal", geo_idx))
				added_horizontal.add(geo_idx)

	# Add dimensional constraints for line segments (but be more selective)
	# Only add dimensions for key features, not for every line
	key_dimensions = []
	if len(geometries) > 0:
		key_dimensions.append(geometries[0])  # First segment
	if len(geometries) > 2:
		key_dimensions.append(geometries[len(geometries)//2])  # Middle segment

	for geo_idx in key_dimensions:
		geo = sketch.Geometry[geo_idx]

		if isinstance(geo, Part.LineSegment):
			start = geo.StartPoint
			end = geo.EndPoint
			length = ((end.x - start.x)**2 + (end.y - start.y)**2)**0.5

			# Only add dimensional constraints for non-zero length lines
			if length > 0.001:
				sketch.addConstraint(Sketcher.Constraint("Distance", geo_idx, length))

	doc.recompute()
	return sketch

def draw_bolt(sections, name="cylinder_profile", start_y=0):
	profile_points = []
	current_y = start_y
	profile_points.append({"x": 0, "y": current_y})
	# Process each section to create the profile
	for i, section in enumerate(sections):
		# Get diameter and length from the section
		diameter = section.get('d', 10)  # Default to 10 if not specified
		length = section.get('l', 10)    # Default to 10 if not specified
		# Calculate radius
		radius = diameter / 2
		# Add the bottom-right corner of this section
		profile_points.append({"x": radius, "y": current_y})
		# Update the current Y position
		current_y += length
		# Add the top-right corner of this section
		profile_points.append({"x": radius, "y": current_y})

	# Add the final point back to the axis
	profile_points.append({"x": 0, "y": current_y})

	# Draw the profile using drawShape
	sketch = drawShape(profile_points, name)

	doc.recompute()
	revolution = doc.addObject("Part::Revolution", name)
	revolution.Source = sketch
	revolution.Axis = Base.Vector(0.0, 1.0, 0.0)  # Y axis
	revolution.Base = Base.Vector(0.0, 0.0, 0.0)
	revolution.Angle = 360.0
	sketch.Visibility = False
	doc.recompute()
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

def create_az_flange(number):
	# Create a new sketch
	sketch = doc.addObject('Sketcher::SketchObject', "az_flange_" + str(number))

	# Define dimensions
	width = 70   # width of rectangle - matches chord length
	height = 70  # height of rectangle
	cut = 20      # size of corner cut

	rotateSketch(sketch, plane='xz', angle=90)
	if (number == 1):
		moveSketch(sketch, x=-width/2, y=-26, z=DISK_THICKNESS * 2)
	else:
		moveSketch(sketch, x=-width/2, y=26, z=DISK_THICKNESS * 2)

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
	hole_radius = 5.01  # 10mm diameter = 5mm radius
	# Position the hole center 15mm from both edges (to leave enough material)
	hole_x = 25  # Move in from the cut corner
	hole_y = height - 25  # Move down from the top
	slot_radius=20
	makeHole(sketch, hole_x, hole_y, hole_radius)
	cutSlot(sketch, slot_width=SLOT_WIDTH, slot_radius=slot_radius, cx=hole_x, cy=hole_y, start_angle=250, end_angle=15)

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
	# Define dimensions
	height = 50      # rectangle height
	width = 50       # rectangle width

	# Define the flange profile points using the dictionary format
	p = [
		{"x": 0, "y": height/2},           # top left
		{"x": 0, "y": -height/2},          # bottom left
		{"x": width, "y": -height/2},      # bottom right
		{"x": width, "y": height/2},       # top right
		{"x": 0, "y": height/2}            # back to top left to close the shape
	]

	# Draw the flange profile using drawShape
	sketch = drawShape(points=p, name="alt_flange_" + str(number))
	# Add holes to the sketch
	hole_x = 25
	hole_y = 0
	makeHole(sketch, x=hole_x, y=hole_y, radius=5.01)
	makeHole(sketch, x=hole_x + 20 - (SLOT_WIDTH/2), y=hole_y, radius=TAPPING_SIZE_6 / 2)
	# Create the pad
	pad = doc.addObject("PartDesign::Pad", "alt_flange_pad_" + str(number))
	pad.Profile = sketch
	pad.Length = DISK_THICKNESS
	sketch.Visibility = False
	pad.Visibility = True
	pad.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray
	doc.recompute()
	x = -width + 15
	z = height + 7
	if number == 1:
		moveObject(pad, x=x, y=20, z=z)
	else:
		y = -20 + (DISK_THICKNESS)
		moveObject(pad, x=x, y=y, z=z)
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
	# create bolts to secure the az angle
	#az_fastner1 = create_shoulder_bolt(top_diameter=16, top_length=5, middle_diameter=6, middle_length=12)
	# az_fastner2 = create_shoulder_bolt(x=0, y=0, top_diameter=16, top_length=5, middle_diameter=6, middle_length=6, bottom_diameter=6, bottom_length=6)
	create_az_flange(1)
	create_az_flange(2)
	create_alt_flange(1)
	create_alt_flange(2)
	FreeCADGui.ActiveDocument.ActiveView.setAnimationEnabled(True)
except Exception as e:
	print(f"Main execution error: {str(e)}")