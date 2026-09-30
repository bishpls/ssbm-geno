"""Texture sizes (w, h) for every texture key; shared by paint.py and the Blender build."""
SIZES = {  # (w, h)
    'face': (128, 128), 'nose': (32, 32), 'headback': (128, 128), 'ears': (64, 64), 'eyeR': (128, 128), 'eyeL': (128, 128),
    'band': (256, 64), 'crown': (256, 128), 'emblem': (128, 64), 'curls': (32, 128),
    'collar': (128, 64), 'collarin': (128, 64), 'cape': (256, 256), 'lining': (128, 128), 'clasp': (64, 64),
    'chest': (128, 128), 'pelvis': (128, 64), 'joint': (64, 64),
    'upperarm': (64, 64), 'forearm': (64, 64), 'thigh': (64, 64), 'shin': (64, 64),
    'palm': (64, 64), 'finger': (64, 64), 'boot': (128, 128), 'cuff': (128, 32), 'lowface': (64, 64), 'forms': (128, 128),
    'fcbarrel': (256, 128), 'fccarriage': (128, 128),        # Geno Flash's cannon (geno_cannon.py)
}

# the specular colour per material (datkit writes it as the material's SPC, shininess 50; Gate 2: replaces Gate 1d's TEX1
# specular maps, which only dimmed the importer's white). Tuned in game beside Mario (his shoes are (102,102,102) under a
# map). Materials not listed are matte: felt, cloth, paper, the eyes, the nose.
WOOD_SPEC, DIM_SPEC = (48, 40, 32), (34, 28, 22)
SPEC = {'face': (36, 30, 24), 'headback': WOOD_SPEC, 'ears': (40, 33, 27), 'chest': WOOD_SPEC, 'pelvis': DIM_SPEC,
        'joint': DIM_SPEC, 'upperarm': WOOD_SPEC, 'forearm': WOOD_SPEC, 'thigh': WOOD_SPEC, 'shin': WOOD_SPEC,
        'palm': (40, 33, 27), 'finger': (40, 33, 27), 'boot': (46, 36, 28), 'cuff': (36, 28, 22), 'clasp': (120, 100, 64),
        'lowface': (32, 26, 21), 'forms': (104, 96, 84), 'fcbarrel': (96, 90, 80), 'fccarriage': (72, 62, 48)}
