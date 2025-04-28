
import time
import FreeCADGui

d = FreeCAD.ActiveDocument.getObjectsByLabel('d')[0]
board_width = float(d.board_width)
board_thickness = float(d.board_thickness)
outdir = "C:/Users/richard/Downloads/"

def getDocumentName():
	return FreeCAD.ActiveDocument.Name

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


def getBoardLength(padName):
	try:
		getConstraint(padName, 'Top Edge Length')
		return
	except: pass
	try:
		getConstraint(padName, 'Length')
		return
	except: pass


def setBoardLength(padName, length):
	if not padName or not length: raise ValueError("must pass sensible values")
	try:
		setConstraint(padName, 'Top Edge Length', length, "mm")
		return
	except: pass
	try:
		setConstraint(padName, 'Length', length, "mm")
		return
	except: pass

def setConstraint(padName, constraintName, value, units):
	if not padName or not constraintName or not value or not units: raise ValueError("must pass sensible values")
	pad = getPadByName(padName)
	sketch = getSketchFromPad(pad)
	sketch.setDatum(constraintName, App.Units.Quantity(str(value) + ' ' + units))

def getPadByName(name):
	return FreeCAD.ActiveDocument.getObjectsByLabel(name)[0]

def getAngles(padName):
	if not padName: raise ValueError("must supply a pad name")
	p = getPadByName(padName)
	if not p: raise ValueError("no such pad")
	#lets not work out how to use a quaternion! Use Euler angles in degrees
	e = p.Placement.Rotation.toEuler()
	X = e[2] #Roll
	Y = e[1] #Pitch
	Z = e[0] #Yaw
	print("X=" + str(X) + " Y=" + str(Y) + " Z=" + str(Z))

def setAngles(padName, x = None, y = None, z = None):
	if not x and not y and not z: return None
	if not padName: raise ValueError("must supply a pad name")
	p = getPadByName(padName)
	if not p: raise ValueError("no such pad")
	#lets not work out how to use a quaternion! Use Euler angles in degrees
	e = p.Placement.Rotation.toEuler()
	X = e[2] #Roll
	Y = e[1] #Pitch
	Z = e[0] #Yaw
	#print("X=" + str(X) + " Y=" + str(Y) + " Z=" + str(Z))
	if x: X = x
	if y: Y = y
	if z: Z = z
	rot = FreeCAD.Rotation(Z,Y,X)
	p.Placement.Rotation = rot

def setPosition(padName,x = None, y = None, z = None):
	if not x and not y and not z: return None
	if not padName: raise ValueError("must supply a pad name")
	p = getPadByName(padName)
	if not p: raise ValueError("no such pad")
	if x: p.Placement.Base.x = x
	if y: p.Placement.Base.y = y
	if z: p.Placement.Base.z = z

def getPosition(padName):
	if not padName: raise ValueError("must supply a pad name")
	p = getPadByName(padName)
	if not p: raise ValueError("no such pad")
	print(p.Label + " : x=" + str(p.Placement.Base.x) + " y=" + str(p.Placement.Base.y) + " z=" + str(p.Placement.Base.z))

def show_all():
	objects = FreeCAD.ActiveDocument.Objects
	for object in objects:
		try:
			object.ViewObject.Visibility = True
		except: pass
	hide_planes()

def hide_planes():
	objects = FreeCAD.ActiveDocument.Objects
	for object in objects:
		if object.isDerivedFrom("App::Origin"):
			object.ViewObject.Visibility = False

def hide_all():
	objects = FreeCAD.ActiveDocument.Objects
	for object in objects:
		if ("App::DocumentObjectGroup" == object.TypeId):
			for obj in object.Group:
			    obj.ViewObject.Visibility = False

def export_drawing(padName, fileName):
	hide_all()
	pad = getPadByName(padName)
	pad.ViewObject.Visibility = True
	sketch = getSketchFromPad(pad)
	sketch.ViewObject.Visibility = True
	Gui.getDocument(getDocumentName()).setEdit(sketch)
	Gui.ActiveDocument.ActiveView.fitAll()
	Gui.ActiveDocument.ActiveView.saveImage(outdir + fileName, 1000, 1000, 'White')
	Gui.getDocument(getDocumentName()).resetEdit()
	show_all()

def export_drawings():
	show_all()
	export_drawing("left_bottom", "bottom_x3.jpg")
	export_drawing("left_backrest", "backrest_x3.jpg")
	export_drawing("left_front", "backrest_x2.jpg")
	export_drawing("middle_front", "backrest_x1.jpg")
	export_drawing("left_middle", "middle_x3.jpg")
	export_drawing("left_armrest", "armrest_x2.jpg")
	export_drawing("sp0", "seat_planks_x4.jpg")
	export_drawing("bp0", "backrest_planks_x4.jpg")
	export_drawing("left_bracket", "backrest_brace_x3.jpg")
	export_drawing("left_floor_brace", "left_floor_brace_x1.jpg")
	export_drawing("right_floor_brace", "right_floor_brace_x1.jpg")

def reset():
	tilt_angle = 5.0
	seat_length = 2000.0
	left_end_y = 0.0
	right_end_y = left_end_y + seat_length - board_thickness
	mid_end_y = left_end_y + ((right_end_y - left_end_y) / 2)

	#left assembly
	setPosition("left_bottom", y = left_end_y, x = 125.0, z = 0.0)
	setAngles("left_bottom", x = 90.0, y = 0.0, z = 0.0)
	setBoardLength("left_bottom", 855.0)

	setPosition("left_backrest", y = left_end_y + -1 * board_thickness, x = 456.0, z = 0.0)
	setAngles("left_backrest", x = -90.0, y = -75.0, z=-180.0)
	setBoardLength("left_backrest", 890.0)

	setPosition("left_middle", y = left_end_y, x = 294.83, z = 137.0)
	setAngles("left_middle", x = 90.0, y = (-1 * tilt_angle), z = 0.0)
	setBoardLength("left_middle", 718.0)

	setPosition("left_front", y = left_end_y + -1 * board_thickness, x = 980.00, z = 0.0)
	setAngles("left_front", x = 0.0, y = -90.0, z = 90.0)
	setBoardLength("left_front", 600.0)

	setPosition("left_armrest", y = left_end_y + -106, z = 600, x = 125.0)
	setAngles("left_armrest", x = 0.0, y = 0.0, z = 0.0)
	setBoardLength("left_armrest", 832.0)

	setPosition("left_bracket", y = left_end_y + -1 * board_thickness, x = 245.0, z = 0)
	setAngles("left_bracket", x = -135.0, y = -90.0, z = -135.0)
	setBoardLength("left_bracket", 635.0)

	#right assembly
	setPosition("right_bottom", y = right_end_y, x = 125.0, z = 0.0)
	setAngles("right_bottom", x = 90.0, y = 0.0, z = 0.0)
	setBoardLength("right_bottom", 855.0)

	setPosition("right_backrest", y = right_end_y + board_thickness, x = 456.0, z = 0.0)
	setAngles("right_backrest", x = -90.0, y = -75.0, z=-180.0)
	setBoardLength("right_backrest", 890.0)

	setPosition("right_middle", y = right_end_y, x = 294.83, z = 137.0)
	setAngles("right_middle", x = 90.0, y = (-1 * tilt_angle), z = 0.0)
	setBoardLength("right_middle", 718.0)

	setPosition("right_front", y = right_end_y + board_thickness, x = 980.00, z = 0.0)
	setAngles("right_front", x = 0.0, y = -90.0, z = 90.0)
	setBoardLength("right_front", 600.0)

	setPosition("right_armrest", y = right_end_y - 44, z = 600, x = 125.0)
	setAngles("right_armrest", x = 0.0, y = 0.0, z = 0.0)
	setBoardLength("right_armrest", 830.0)

	setPosition("right_bracket", y = right_end_y + board_thickness, x = 245.0, z = 0)
	setAngles("right_bracket", x = -135.0, y = -90.0, z = -135.0)
	setBoardLength("right_bracket", 635.0)

	#mid assembly
	setPosition("middle_bottom", y = mid_end_y, x = 125.0, z = 0.0)
	setAngles("middle_bottom", x = 90.0, y = 0.0, z = 0.0)
	setBoardLength("middle_bottom", 855.0)

	setPosition("middle_backrest", y = mid_end_y + board_thickness, x = 456.0, z = 0.0)
	setAngles("middle_backrest", x = -90.0, y = -75.0, z=-180.0)
	setBoardLength("middle_backrest", 890.0)

	setPosition("middle_middle", y = mid_end_y, x = 294.83, z = 137.0)
	setAngles("middle_middle", x = 90.0, y = (-1 * tilt_angle), z = 0.0)
	setBoardLength("middle_middle", 718.0)

	setPosition("middle_front", y = mid_end_y + board_thickness, x = 980.00, z = 0.0)
	setAngles("middle_front", x = 0.0, y = -90.0, z = 90.0)
	setBoardLength("middle_front", 308.0)

	setPosition("middle_bracket", y = mid_end_y + board_thickness, x = 245.0, z = 0)
	setAngles("middle_bracket", x = -135.0, y = -90.0, z = -135.0)
	setBoardLength("middle_bracket", 635.0)

	#seat planks
	bx = 858.0
	spa = 150
	runner_length = seat_length
	setPosition("sp0", x = bx, y = -(board_thickness), z = 340.0)
	setBoardLength("sp0", runner_length)

	setPosition("sp1", x = bx - (spa * 1), y = -(board_thickness), z = 324.0)
	setBoardLength("sp1", runner_length)

	setPosition("sp2", x = bx - (spa * 2), y = -(board_thickness), z = 312.0)
	setBoardLength("sp2", runner_length)
	setPosition("sp3", x = bx - (spa * 3), y = -(board_thickness), z = 298.0)
	setBoardLength("sp3", runner_length)

	runner_length = runner_length + (2 * board_thickness)

	#backrest planks
	setPosition("bp0", x = 367.0, y = -(board_thickness * 2), z = 330.0)
	setBoardLength("bp0",runner_length)
	setPosition("bp1", x = 328.0, y = -(board_thickness * 2), z = 474.0)
	setBoardLength("bp1",runner_length)
	setPosition("bp2", x = 286.0, y = -(board_thickness * 2), z = 630.0)
	setBoardLength("bp2",runner_length)
	setPosition("bp3", x = 248.0, y = -(board_thickness * 2), z = 775.0)
	setBoardLength("bp3",runner_length)

	#bracing boards
	setPosition("left_bracket", x = 245.0, y = -(board_thickness), z = 0.0)
	setAngles("left_bracket", x = 0.0, y = -90.0, z = 90.0)
	setPosition("middle_bracket", x = 245.0, y = mid_end_y + board_thickness, z = 0.0)
	setAngles("middle_bracket", x = 0.0, y = -90.0, z = 90.0)
	setPosition("right_bracket", x = 245.0, y = right_end_y + board_thickness , z = 0.0)
	setAngles("right_bracket", x = 0.0, y = -90.0, z = 90.0)

	bl = (seat_length / 2)
	setPosition("left_floor_brace", x = 700.0, y = 0.0, z = 0.0)
	setAngles("left_floor_brace", x=0.0, y=0.0, z=90)
	setBoardLength("left_floor_brace", bl)
	setPosition("right_floor_brace", x = 700.0, y = mid_end_y, z = 0.0)
	setAngles("right_floor_brace", x=0.0, y=0.0, z=90)
	setBoardLength("right_floor_brace", bl - board_thickness)

	FreeCAD.ActiveDocument.recompute()

reset()
export_drawings()
