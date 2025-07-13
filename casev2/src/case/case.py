from build123d import (
    BuildLine,
    BuildPart,
    BuildSketch,
    Polyline,
    Rectangle,
    RectangleRounded,
    Locations,
    extrude,
    Axis,
    Mode,
    Compound,
    Location,
    Hole,
    Align,
    Select,
    Mesher,
    Color,
    fillet,
    make_face,
)
from ocp_vscode import show, show_object


# Boards parameters
ESP32_WIDTH = 18
ESP32_LENGTH = 26.27
ESP32_PCB_THICKNESS = 1.0
USB_C_WIDTH = 8.77
USB_C_LENGTH = 7.23
USB_C_THICKNESS = 3.02
USB_C_OVERHANG = 1.73

MMWAVE_WIDTH = 26.0
MMWAVE_LENGTH = 30.0
MMWAVE_THICKNESS = 3.2

# Enclosure parameters
WALL_THICKNESS = 1.0
CORNER_RADIUS = 1.0
ESP32_SIDE_CLEARENCE = 5.0
ESP32_BOTTOM_CLEARENCE = 2.0
ESP32_TOP_CLEARENCE = 10.0

PRINT_TOLERANCE = 0.35

LID_CUTS = False

outer_width = ESP32_WIDTH + (ESP32_SIDE_CLEARENCE * 2) + (WALL_THICKNESS * 2)
outer_length = (
    ESP32_LENGTH
    + ESP32_SIDE_CLEARENCE
    + (WALL_THICKNESS * 2)
    + (USB_C_OVERHANG - WALL_THICKNESS)
)
outer_thickness = (
    WALL_THICKNESS + ESP32_BOTTOM_CLEARENCE + ESP32_PCB_THICKNESS + ESP32_TOP_CLEARENCE
)


inner_width = ESP32_WIDTH + (ESP32_SIDE_CLEARENCE * 2)
inner_length = ESP32_LENGTH + ESP32_SIDE_CLEARENCE + (USB_C_OVERHANG - WALL_THICKNESS)


# Create ESP32 board with USB-C as single solid
with BuildPart() as esp32_board:
    # ESP32 PCB
    with BuildSketch() as board:
        Rectangle(ESP32_WIDTH, ESP32_LENGTH)
    extrude(amount=ESP32_PCB_THICKNESS)

    # USB-C connector - create sketch on YZ plane perpendicular to PCB top
    offset = -1 * (USB_C_LENGTH - USB_C_OVERHANG)
    with BuildSketch(
        esp32_board.faces().sort_by(Axis.Y)[0].offset(offset)
    ) as usb_sketch:
        with Locations(
            (0, ESP32_PCB_THICKNESS + (USB_C_THICKNESS - ESP32_PCB_THICKNESS) / 2)
        ):
            RectangleRounded(USB_C_WIDTH, USB_C_THICKNESS, radius=0.5)

    # Extrude in X direction (sideways)
    extrude(amount=USB_C_LENGTH)

with BuildPart() as mmwave_board:
    with BuildSketch() as board:
        RectangleRounded(MMWAVE_WIDTH, MMWAVE_LENGTH, 0.5)
    extrude(amount=MMWAVE_THICKNESS)

    # Add holes in bottom corners
    hole_diameter = 1.73
    hole_offset = 1.10

    with Locations(
        (MMWAVE_WIDTH / 2 - hole_offset, -MMWAVE_LENGTH / 2 + hole_offset),
        (-MMWAVE_WIDTH / 2 + hole_offset, -MMWAVE_LENGTH / 2 + hole_offset),
    ):
        Hole(hole_diameter / 2, depth=MMWAVE_THICKNESS)

with BuildPart() as base:
    with BuildSketch() as outer_profile:
        RectangleRounded(outer_width, outer_length, CORNER_RADIUS)
    extrude(amount=outer_thickness)

    with BuildSketch(base.faces().sort_by(Axis.Z)[-1]) as innes_profile:
        Rectangle(inner_width, inner_length)
    extrude(amount=-(outer_thickness - WALL_THICKNESS), mode=Mode.SUBTRACT)

    inner_bottom_face = base.faces().sort_by(Axis.Z)[
        1
    ]  # Second lowest face (bottom of cavity)

    # locate usb c cut on side of box
    usb_c_face = base.faces(Select.LAST).filter_by(Axis.Y).sort_by(Axis.Y).first
    with BuildSketch(usb_c_face) as usb_cut:
        # Position USB-C at ESP32_BOTTOM_CLEARENCE from inner bottom
        usb_c_z_offset = (
            inner_bottom_face.center().Z
            + ESP32_BOTTOM_CLEARENCE
            + USB_C_THICKNESS / 2
            - usb_c_face.center().Z
        )
        with Locations((0, -usb_c_z_offset)):
            RectangleRounded(
                USB_C_WIDTH + PRINT_TOLERANCE, USB_C_THICKNESS + PRINT_TOLERANCE, 0.5
            )
    extrude(amount=-1, mode=Mode.SUBTRACT)

    with BuildSketch(inner_bottom_face) as rail:
        rail_width = inner_width
        rail_length = ESP32_SIDE_CLEARENCE + 2.0
        # Use the left edge of the inner cavity to position the box
        top_edge = inner_bottom_face.edges().sort_by(Axis.Y).last
        with Locations(top_edge.center()):
            Rectangle(inner_width, rail_length, align=(Align.CENTER, Align.MAX))
    extrude(amount=ESP32_BOTTOM_CLEARENCE)

    rail_top_face = base.faces(Select.LAST).filter_by(Axis.Z).sort_by(Axis.Z).last

    with BuildSketch(rail_top_face) as board_holder:
        w = ESP32_WIDTH + PRINT_TOLERANCE
        l = 1.9 + PRINT_TOLERANCE

        bottom_edge = rail_top_face.edges().sort_by(Axis.Y).first

        # Calculate offset from rail center to edge
        offset_y = bottom_edge.center().Y - rail_top_face.center().Y
        with Locations((0, offset_y)):
            Rectangle(w, l, align=(Align.CENTER, Align.MIN))
    extrude(amount=-ESP32_PCB_THICKNESS, mode=Mode.SUBTRACT)

with BuildPart() as lid:
    lid_tight = 0.1

    with BuildSketch() as lid_plate:
        RectangleRounded(outer_width, outer_length, CORNER_RADIUS)
    extrude(amount=WALL_THICKNESS)

    # Create the outer lip boundary
    lip_outer_width = inner_width + lid_tight
    lip_outer_height = inner_length + lid_tight
    # Create the inner cavity for the lip (making it just a border)
    lip_inner_width = MMWAVE_WIDTH
    lip_inner_height = MMWAVE_LENGTH
    lip_depth = (
        MMWAVE_THICKNESS + PRINT_TOLERANCE
    )  # How far the lip extends into the cavity

    bottom_face = lid.faces(Select.LAST).filter_by(Axis.Z).sort_by(Axis.Z).last
    with BuildSketch(bottom_face) as fitting:
        RectangleRounded(lip_outer_width, lip_outer_height, CORNER_RADIUS)
        Rectangle(lip_inner_width, lip_inner_height, mode=Mode.SUBTRACT)
    extrude(amount=-lip_depth)

    # add finger grip on one lip side - creates a small bridge/tab to lift lid
    lip_face = lid.faces(Select.LAST).filter_by(Axis.Y).sort_by(Axis.Y).first
    with BuildSketch(lip_face) as lip_cut:
        # Create a rounded slot that leaves material above for fingernail grip
        grip_width = 4  # Width of the grip area
        grip_depth = 1.5  # How deep the undercut goes
        grip_height = 2.5  # Height of the slot (leaves material above)

        # Position slightly below center so there's material above for the "bridge"
        with Locations((0, -0.8)):
            RectangleRounded(grip_width, grip_height, radius=0.8)
    # Only extrude partway to create the undercut/bridge
    extrude(amount=-grip_depth, mode=Mode.SUBTRACT)

    # cut holes for sensors
    if LID_CUTS:
        with BuildSketch(bottom_face) as sensor_cuts:
            sensor_cut_width = 4.30
            sensor_cut_height = 21.23
            edge_gap = 2
            x_offset = lip_inner_width / 2 - sensor_cut_width / 2 - edge_gap
            # Position holes 2mm from top edge
            y_offset = lip_inner_height / 2 - sensor_cut_height / 2 - edge_gap

            with Locations(
                (-x_offset, y_offset), (x_offset, y_offset)
            ):  # Left and right positions near top
                Rectangle(sensor_cut_width, sensor_cut_height)

        extrude(amount=-WALL_THICKNESS, mode=Mode.SUBTRACT)


with BuildPart() as corner_holder:
    holder_base_width = outer_width + 10
    # For 90-degree angle at apex: height = base_width / 2
    holder_height = holder_base_width / 2
    holder_cut_deep = 3
    holder_tight = 0.2

    with BuildSketch() as holder_sk:
        # Create right triangle with 90-degree angle at apex
        pts = [
            (-holder_base_width / 2, 0),  # Left base corner
            (holder_base_width / 2, 0),  # Right base corner
            (0, holder_height),  # Top apex (90-degree angle)
            (-holder_base_width / 2, 0),  # Close the triangle
        ]
        with BuildLine() as ln:
            Polyline(*pts)

        make_face()

    # Extrude the triangle to create 3D shape
    extrude(amount=10)  # Extrude 10mm in Z direction
    fillet(corner_holder.edges().filter_by(Axis.Z), radius=CORNER_RADIUS)

    # Create rectangular cutout on the base edge
    base_face = corner_holder.faces().sort_by(Axis.Z)[0]  # Bottom face
    with BuildSketch(base_face) as cutout_sketch:
        # Get base edge Y in global coords (should be ~0)
        base_edge = base_face.edges().sort_by(Axis.Y)[0]
        base_y_global = base_edge.center().Y

        # Get centroid Y
        vertices = list(base_face.vertices())
        centroid_y = sum(v.Y for v in vertices) / len(vertices)

        # In sketch local coords, base is at:
        base_y_local = base_y_global - centroid_y

        # We want rectangle bottom edge at base, so its center is holder_cut_deep/2 above
        rect_y = -base_y_local - holder_cut_deep / 2

        with Locations((0, rect_y)):
            Rectangle(
                outer_width - holder_tight,
                holder_cut_deep,
            )
    extrude(amount=-10, mode=Mode.SUBTRACT)  # Cut into the triangle

show(lid)


# Position lid above base for visualization
lid_positioned = lid.part.moved(Location((0, 0, outer_thickness + 10)))

# Position ESP32 board inside the base
z_offset = WALL_THICKNESS + ESP32_BOTTOM_CLEARENCE - ESP32_PCB_THICKNESS
# Position Y so USB-C connector aligns with the cut
y_offset = -inner_length / 2 + ESP32_LENGTH / 2 + USB_C_OVERHANG - 1
esp32_positioned = esp32_board.part.moved(Location((0, y_offset, z_offset)))

# Position mmWave board attached to the lid
mmwave_positioned = mmwave_board.part.moved(
    Location((0, 0, outer_thickness + 10 - WALL_THICKNESS - MMWAVE_THICKNESS))
)


# Set colors for each part
base.part.color = Color("gray")
lid_positioned.color = Color("lightblue")
esp32_positioned.color = Color("green")
mmwave_positioned.color = Color("red")

# Create assembly
assembly = Compound(
    children=[
        base.part,
        lid_positioned,
        esp32_positioned,
        mmwave_positioned,
    ]
)

# Show the assembly
# show_object(assembly, name="Enclosure Assembly")

# Export individual parts if needed
# exporter = Mesher()
# exporter.add_shape(base.part)
# exporter.write("enclosure_base.stl")

# exporter = Mesher()
# exporter.add_shape(lid.part)
# exporter.write("enclosure_lid.stl")

# exporter = Mesher()
# exporter.add_shape(corner_holder.part)
# exporter.write("corner_holder.stl")
