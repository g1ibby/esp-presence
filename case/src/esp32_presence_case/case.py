import cadquery as cq


# Boards parameters
ESP32_WIDTH = 18
ESP32_LENGTH = 26.27
ESP32_PCB_THICKNESS = 1.0
USB_C_WIDTH = 8.77
USB_C_LENGTH = 7.23
USB_C_THICKNESS = 3.02
USB_C_OVERHANG = 1.73

MMWAVE_WIDTH = 22.0
MMWAVE_LENGTH = 15.80
MMWAVE_THICKNESS = 3.0

# Enclosure parameters
WALL_THICKNESS = 1.0
CORNER_RADIUS = 1.0
ESP32_SIDE_CLEARENCE = 3.5
ESP32_BOTTOM_CLEARENCE = 2.0
ESP32_TOP_CLEARENCE = 10.0

PRINT_TOLERANCE = 0.35


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


def esp32_board() -> cq.Workplane:
    board = (
        cq.Workplane("XY")
        .rect(ESP32_WIDTH + PRINT_TOLERANCE, ESP32_LENGTH + PRINT_TOLERANCE)
        .extrude(ESP32_PCB_THICKNESS)
    )

    usb_c = (
        cq.Workplane("XY")
        .rect(USB_C_WIDTH + PRINT_TOLERANCE, USB_C_LENGTH)
        .extrude(USB_C_THICKNESS + PRINT_TOLERANCE)
        .edges("|Y")
        .fillet(CORNER_RADIUS)
    )
    usb_c_loc = (0, -((ESP32_LENGTH / 2) - USB_C_OVERHANG), ESP32_PCB_THICKNESS)
    board = board.union(usb_c.translate(usb_c_loc))
    return board


def mmwave_board() -> cq.Workplane:
    board = (
        cq.Workplane("XY").rect(MMWAVE_WIDTH, MMWAVE_LENGTH).extrude(MMWAVE_THICKNESS)
    )

    return board


def base_case() -> cq.Workplane:
    case = (
        cq.Workplane("XY")
        .rect(outer_width, outer_length)
        .extrude(outer_thickness)
        .edges("|Z")
        .fillet(CORNER_RADIUS)
    )

    inner_thickness = ESP32_BOTTOM_CLEARENCE + ESP32_PCB_THICKNESS + ESP32_TOP_CLEARENCE
    cavity = (
        cq.Workplane("XY")
        .workplane(offset=WALL_THICKNESS)
        .rect(inner_width, inner_length)
        .extrude(inner_thickness)
    )

    case = case.cut(cavity)

    # Add PCB support rails for ESP32 (bottom board)
    rail = (
        cq.Workplane("XY")
        .workplane(offset=WALL_THICKNESS)
        .rect(inner_width, ESP32_SIDE_CLEARENCE + 2.0)
        .extrude(ESP32_BOTTOM_CLEARENCE)
    )
    case = case.union(
        rail.translate((0, (inner_length / 2) - ESP32_SIDE_CLEARENCE / 2, 0))
    )

    # Cut usb c and holder board
    esp32board = esp32_board().translate(
        (
            0,
            -USB_C_OVERHANG + 0.5,
            WALL_THICKNESS + ESP32_BOTTOM_CLEARENCE - ESP32_PCB_THICKNESS,
        )
    )
    case = case.cut(esp32board)

    return case


def top_cover() -> cq.Workplane:
    # Main cover plate
    cover_plate = (
        cq.Workplane("XY")
        .rect(outer_width, outer_length)
        .extrude(WALL_THICKNESS)
        .edges("|Z")
        .fillet(CORNER_RADIUS)
    )

    # Create the outer lip boundary
    lip_outer_width = inner_width
    lip_outer_height = inner_length

    # Create the inner cavity for the lip (making it just a border)
    lip_inner_width = (lip_outer_width - 2 * WALL_THICKNESS) - (0.5 * 2)
    lip_inner_height = lip_outer_height - 2 * WALL_THICKNESS

    lip_depth = MMWAVE_THICKNESS  # How far the lip extends into the cavity

    # Create solid lip
    lip_solid = (
        cq.Workplane("XY")
        .rect(lip_outer_width, lip_outer_height)
        .extrude(-lip_depth)  # Negative to extend downward
        .edges("|Z")
        .fillet(0.5)  # Small fillet for easier insertion
    )

    # Create inner cavity to cut from lip
    lip_cavity = (
        cq.Workplane("XY")
        .rect(lip_inner_width, lip_inner_height)
        .extrude(-lip_depth - 1)  # Slightly deeper to ensure clean cut
    )

    # Create hollow lip border
    lip_border = lip_solid.cut(lip_cavity)

    # Combine cover plate and lip border
    cover = cover_plate.union(lip_border)

    sensor_cut_width = 16.84
    sensor_cut_height = 7.65
    loc_sensor_cut = (lip_inner_height / 2) - 3.92 - (sensor_cut_height / 2)

    sensor_cut = (
        cq.Workplane("XY")
        .rect(sensor_cut_width, sensor_cut_height)
        .extrude(WALL_THICKNESS)
    )
    cover = cover.cut(sensor_cut.translate((0, loc_sensor_cut, 0)))

    return cover


# cover = top_cover()

# case = base_case()
asm = cq.Assembly()

asm.add(base_case(), loc=cq.Location(0, 0, 0), name="case", color=cq.Color("blue"))
asm.add(
    top_cover(),
    loc=cq.Location(0, 0, outer_thickness),
    name="cover",
    color=cq.Color("red"),
)

