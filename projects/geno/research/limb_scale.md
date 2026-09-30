# Limb scale in the cast's attacks

Which body parts grow (or shrink) while a move plays, from the animation data (`limb_scale.py`). "own" is the joint's own scale at its peak, "chain end" the effective scale at the hand or foot it carries (scale is inherited). Frames are the animation's, from 0; "active" the move's hit windows.

| Fighter | Move | Active | Joint | Scaled frames (peak) | Own peak | Chain end (effective) |
|---|---|---|---|---|---|---|
| Falcon | ftilt_hi | [[9, 11]] | R4thNa | 7-16 (11) | 0.89 | R4thNa 1.0 |
| Falcon | ftilt | [[9, 11]] | R4thNa | 7-16 (11) | 0.89 | R4thNa 1.0 |
| Falcon | ftilt_lw | [[9, 11]] | R4thNa | 7-16 (11) | 0.89 | R4thNa 1.0 |
| Falcon | utilt | [[17, 21]] | R4thNa | 11-19 (16) | 0.88 | R4thNa 1.0 |
| Falcon | fsmash_hi | [[18, 65]] | R4thNa | 18-43 (28) | 0.71 | R4thNa 1.0 |
| Falcon | fsmash | [[18, 21]] | R4thNa | 18-43 (28) | 0.71 | R4thNa 1.0 |
| Falcon | fsmash_lw | [[18, 21]] | R4thNa | 18-43 (28) | 0.71 | R4thNa 1.0 |
| Falcon | usmash | [[21, 22], [27, 28]] | R4thNa | 20-29 (24) | 0.81 | R4thNa 1.0 |
| Falcon | dsmash | [[19, 22], [29, 32]] | R4thNa | 30-35 (33) | 0.85 | R4thNa 1.0 |
| Falcon | bair | [[10, 13], [14, 17]] | NeckN | 10-12 (10) | 1.28 | j25 1.53 |
| Falcon | bair | [[10, 13], [14, 17]] | j25 | 10-12 (10) | 1.2 | j26 1.53 |
| Falcon | dair | [[16, 20]] | LShoulderJA | 3-18 (17) | 1.25 | LShoulderJ 1.25 |
| Falcon | dair | [[16, 20]] | L2ndNa | 3-18 (17) | 1.25 | L2ndNb 1.25 |
| Falcon | ledge_quick | [[24, 29]] | L2ndNb | 25-29 (25) | 1.2 | L3rdNa 1.2 |
| Falcon | ledge_quick | [[24, 29]] | R4thNa | 24-29 (27) | 0.88 | R4thNa 1.0 |
| Falcon | getup_d | [[20, 21], [26, 27]] | R4thNa | 10-38 (23) | 0.92 | R4thNa 1.0 |
| DK | usmash | [[14, 16]] | L2ndNb | 15-15 (15) | 1.39 | L3rdNa 1.39 |
| DK | usmash | [[14, 16]] | RShoulderN | 15-15 (15) | 1.28 | RShoulderJA 1.28 |
| DK | fair | [[25, 26], [27, 29]] | L2ndNb | 23-49 (26) | 1.74 | L3rdNa 1.74 |
| DK | fair | [[25, 26], [27, 29]] | RShoulderN | 23-49 (26) | 1.74 | RShoulderJA 1.74 |
| DK | bair | [[7, 8], [9, 15]] | LLegJ | 6-25 (7) | 1.75 | LKneeJ 1.75 |
| DK | dair | [[18, 23]] | j16 | 18-24 (18) | 1.66 | j17 1.66 |
| DK | getup_u | [[6, 7], [18, 19]] | j16 | 7-20 (10) | 1.3 | j17 1.3 |
| DK | getup_u | [[6, 7], [18, 19]] | LLegJ | 9-20 (10) | 1.3 | LKneeJ 1.3 |
| DK | getup_u | [[6, 7], [18, 19]] | TransN2 | 11-22 (17) | 1.11 | TransN2 1.11 |
| Fox | jab1 | [[2, 3]] | L1stNb | 1-9 (5) | 1.34 | L2ndNa 1.95 |
| Fox | jab1 | [[2, 3]] | LHandN | 3-4 (3) | 1.5 | L1stNb 1.95 |
| Fox | jab2 | [[2, 3]] | R4thNb | 2-3 (2) | 1.5 | RHandNb 2.4 |
| Fox | jab2 | [[2, 3]] | RHandNb | 2-9 (2) | 1.6 | RThumbNa 2.4 |
| Fox | dash_attack | [[4, 7], [8, 17]] | LLegJA | 4-5 (4) | 1.3 | LLegJ 1.3 |
| Fox | dash_attack | [[4, 7], [8, 17]] | RHandNb | 27-40 (40) | 0.94 | RThumbNa 1.0 |
| Fox | ftilt_hi | [[5, 8]] | RLegJA | 5-16 (6) | 1.21 | RLegJ 1.21 |
| Fox | ftilt | [[5, 8]] | RLegJA | 5-16 (6) | 1.21 | RLegJ 1.21 |
| Fox | ftilt_lw | [[5, 8]] | RLegJA | 5-16 (6) | 1.21 | RLegJ 1.21 |
| Fox | utilt | [[5, 11]] | RLegJA | 5-10 (7) | 1.35 | RLegJ 1.35 |
| Fox | dtilt | [[7, 9]] | j17 | 1-12 (8) | 2 | WaistB 2.0 |
| Fox | dsmash | [[6, 10]] | LLegJA | 4-9 (6) | 1.3 | LLegJ 1.3 |
| Fox | dsmash | [[6, 10]] | RLegJA | 4-9 (6) | 1.3 | RLegJ 1.3 |
| Fox | nair | [[4, 7], [8, 31]] | LFootJA | 4-31 (17) | 1.25 | LFootJ 1.25 |
| Fox | ledge_slow | [[57, 59]] | RLegJA | 56-60 (58) | 1.6 | RLegJ 1.6 |
| Fox | getup_u | [[17, 19], [24, 26]] | LLegJA | 21-29 (25) | 1.5 | LLegJ 1.5 |
| Fox | getup_u | [[17, 19], [24, 26]] | R4thNb | 16-23 (18) | 1.45 | j56 1.45 |
| Fox | getup_d | [[19, 20], [25, 26]] | RLegJA | 20-27 (20) | 1.5 | RLegJ 1.5 |
| G&W | jab1 | [[4, 6]] | j21 | 0-18 (0) | 0.0 | j21 0.0 |
| G&W | jab1 | [[4, 6]] | BustN | 1-17 (1) | 1.3 | LShoulderN 1.3 |
| G&W | jab1 | [[4, 6]] | j11 | 1-17 (1) | 1.2 | j12 1.2 |
| G&W | jab1 | [[4, 6]] | LShoulderJ | 1-17 (1) | 0.9 | LArmJ 1.17 |
| G&W | jab1 | [[4, 6]] | j14 | 1-17 (1) | 0.9 | RLegJA 1.08 |
| G&W | dash_attack | [[6, 29]] | j21 | 0-38 (0) | 0.0 | j21 1.0 |
| G&W | dash_attack | [[6, 29]] | j11 | 6-37 (6) | 0.8 | j12 1.0 |
| G&W | dash_attack | [[6, 29]] | j14 | 6-37 (6) | 0.95 | RLegJA 1.0 |
| G&W | dash_attack | [[6, 29]] | LShoulderN | 6-37 (6) | 0.7 | LShoulderJA 1.0 |
| G&W | dash_attack | [[6, 29]] | LShoulderJ | 6-37 (6) | 0.85 | LArmJ 1.0 |
| G&W | ftilt | [[13, 30]] | LFootJ | 1-12 (1) | 0.01 | j10 1.0 |
| G&W | ftilt | [[13, 30]] | j24 | 1-12 (1) | 0.01 | WaistB 1.0 |
| G&W | utilt | [[9, 29]] | j14 | 1-29 (1) | 0.8 | RKneeJ 1.44 |
| G&W | utilt | [[9, 29]] | RKneeJ | 1-29 (9) | 1.6 | RKneeJ 1.44 |
| G&W | utilt | [[9, 29]] | BustN | 1-29 (1) | 0.9 | LShoulderN 1.0 |
| G&W | dtilt | [[6, 13]] | HipN | 0-30 (0) | 0.5 | LLegJA 1.0 |
| G&W | dtilt | [[6, 13]] | j12 | 0-30 (0) | 0.85 | j13 1.0 |
| G&W | dtilt | [[6, 13]] | j14 | 0-30 (0) | 0.9 | RLegJA 1.0 |
| G&W | dtilt | [[6, 13]] | LShoulderN | 0-30 (0) | 0.85 | LShoulderJA 1.0 |
| G&W | dtilt | [[6, 13]] | LShoulderJ | 0-30 (0) | 0.9 | LArmJ 1.0 |
| G&W | usmash | [[24, 28]] | RFootJ | 25-44 (25) | 1.1 | j20 1.1 |
| G&W | nair | [[20, 29]] | j23 | 0-45 (0) | 0.8 | j23 0.8 |
| G&W | fair | [[10, 12], [13, 32]] | RKneeJ | 1-19 (10) | 1.3 | RKneeJ 1.3 |
| G&W | fair | [[10, 12], [13, 32]] | j23 | 0-45 (0) | 0.8 | j23 0.8 |
| G&W | bair | [[10, 12], [13, 15], [16, 18], [19, 21]] | j23 | 0-40 (0) | 0.8 | j23 0.8 |
| G&W | uair | [[7, 16], [21, 22]] | j23 | 0-40 (0) | 0.8 | j23 1.1 |
| G&W | uair | [[7, 16], [21, 22]] | LFootJ | 1-39 (1) | 0.01 | j10 1.0 |
| G&W | uair | [[7, 16], [21, 22]] | j24 | 1-39 (1) | 0.01 | WaistB 1.0 |
| G&W | dair | [[12, 12], [12, 38], [13, 38]] | j23 | 0-50 (0) | 0.8 | j23 0.8 |
| G&W | dair | [[12, 12], [12, 38], [13, 38]] | RKneeJ | 1-11 (1) | 0.8 | RKneeJ 1.0 |
| G&W | grab | [[6, 7]] | BustN | 6-14 (6) | 1.1 | LShoulderN 1.21 |
| G&W | grab | [[6, 7]] | LShoulderN | 6-14 (6) | 1.1 | LShoulderJA 1.21 |
| G&W | grab | [[6, 7]] | j11 | 6-29 (6) | 0.9 | j12 1.0 |
| G&W | dash_grab | [[10, 11]] | BustN | 10-39 (20) | 0.85 | LShoulderN 1.21 |
| G&W | dash_grab | [[10, 11]] | LShoulderN | 10-19 (10) | 1.1 | LShoulderJA 1.21 |
| G&W | dash_grab | [[10, 11]] | j11 | 10-39 (10) | 0.9 | j12 1.0 |
| G&W | pummel | [[12, 12]] | BustN | 0-30 (1) | 0.01 | LShoulderN 1.37 |
| G&W | pummel | [[12, 12]] | LShoulderN | 0-30 (0) | 1.1 | LShoulderJA 1.37 |
| G&W | pummel | [[12, 12]] | j11 | 0-30 (0) | 0.9 | RKneeJ 1.17 |
| G&W | pummel | [[12, 12]] | RKneeJ | 1-29 (1) | 1.3 | RKneeJ 1.17 |
| G&W | ledge_quick | [[42, 47]] | j14 | 0-28 (0) | 0.51 | RLegJA 1.0 |
| G&W | ledge_slow | [[55, 59]] | j14 | 0-36 (0) | 0.51 | RLegJA 1.0 |
| G&W | getup_d | [[20, 21], [32, 33]] | j14 | 0-19 (0) | 0.79 | RLegJA 1.0 |
| Kirby | jab1 | [[3, 4]] | j29 | 3-11 (4) | 2 | j30 1.94 |
| Kirby | jab1 | [[3, 4]] | j6 | 3-15 (4) | 1.24 | j7 1.24 |
| Kirby | jab2 | [[2, 3]] | j24 | 2-11 (3) | 2.4 | j25 2.28 |
| Kirby | jab2 | [[2, 3]] | WaistN | 3-3 (3) | 0.95 | j24 2.28 |
| Kirby | jab2 | [[2, 3]] | j6 | 1-18 (1) | 1.14 | j7 1.14 |
| Kirby | jab2 | [[2, 3]] | j29 | 0-1 (0) | 1.1 | j30 1.07 |
| Kirby | dash_attack | [[9, 15], [16, 43]] | WaistN | 3-56 (9) | 0.8 | j6 1.19 |
| Kirby | dash_attack | [[9, 15], [16, 43]] | j6 | 26-62 (55) | 0.5 | j7 1.19 |
| Kirby | dash_attack | [[9, 15], [16, 43]] | LHandNb | 0-28 (0) | 1.1 | RShoulderN 1.1 |
| Kirby | dash_attack | [[9, 15], [16, 43]] | LShoulderJA | 25-60 (58) | 0.9 | LShoulderJ 1.1 |
| Kirby | dash_attack | [[9, 15], [16, 43]] | RShoulderJ | 0-38 (0) | 0.85 | RArmJ 1.0 |
| Kirby | ftilt_hi | [[5, 8]] | LShoulderJA | 3-12 (5) | 2 | LShoulderJ 2.0 |
| Kirby | ftilt_hi | [[5, 8]] | WaistN | 5-31 (27) | 0.83 | j6 1.06 |
| Kirby | ftilt | [[5, 8]] | LShoulderJA | 3-10 (5) | 2 | LShoulderJ 2.0 |
| Kirby | ftilt | [[5, 8]] | WaistN | 5-31 (26) | 0.83 | j6 1.06 |
| Kirby | ftilt_lw | [[5, 8]] | LShoulderJA | 3-12 (5) | 2 | LShoulderJ 2.0 |
| Kirby | ftilt_lw | [[5, 8]] | WaistN | 5-31 (26) | 0.83 | j6 1.06 |
| Kirby | utilt | [[4, 4], [5, 7]] | RShoulderJ | 4-13 (6) | 1.55 | RArmJ 1.55 |
| Kirby | utilt | [[4, 4], [5, 7]] | j6 | 1-23 (2) | 0.69 | j7 1.14 |
| Kirby | dtilt | [[4, 7]] | WaistN | 0-30 (0) | 1.15 | j6 0.57 |
| Kirby | dtilt | [[4, 7]] | HipN | 0-30 (0) | 0.5 | RShoulderJ 0.93 |
| Kirby | dtilt | [[4, 7]] | RShoulderJ | 1-21 (5) | 1.86 | RArmJ 0.93 |
| Kirby | fsmash_hi | [[13, 15], [16, 21]] | LShoulderN | 0-50 (0) | 1.1 | LShoulderJA 1.48 |
| Kirby | fsmash_hi | [[13, 15], [16, 21]] | LShoulderJA | 12-22 (13) | 1.35 | LShoulderJ 1.48 |
| Kirby | fsmash_hi | [[13, 15], [16, 21]] | j6 | 1-49 (25) | 0.66 | j7 1.12 |
| Kirby | fsmash | [[13, 15], [16, 21]] | LShoulderN | 0-50 (0) | 1.1 | LShoulderJA 1.59 |
| Kirby | fsmash | [[13, 15], [16, 21]] | LShoulderJA | 12-22 (13) | 1.45 | LShoulderJ 1.59 |
| Kirby | fsmash | [[13, 15], [16, 21]] | j6 | 1-49 (25) | 0.66 | j7 1.12 |
| Kirby | fsmash_lw | [[13, 15], [16, 21]] | LShoulderN | 0-50 (0) | 1.1 | LShoulderJA 1.54 |
| Kirby | fsmash_lw | [[13, 15], [16, 21]] | LShoulderJA | 12-22 (13) | 1.4 | LShoulderJ 1.54 |
| Kirby | fsmash_lw | [[13, 15], [16, 21]] | j6 | 1-49 (25) | 0.66 | j7 1.12 |
| Kirby | usmash | [[13, 13], [14, 15], [16, 23]] | YRotN | 1-49 (38) | 0.48 | RShoulderJ 1.75 |
| Kirby | usmash | [[13, 13], [14, 15], [16, 23]] | RShoulderJ | 11-23 (15) | 1.75 | RArmJ 1.75 |
| Kirby | usmash | [[13, 13], [14, 15], [16, 23]] | LShoulderJA | 12-22 (15) | 1.25 | LShoulderJ 1.25 |
| Kirby | usmash | [[13, 13], [14, 15], [16, 23]] | WaistN | 2-49 (46) | 1.35 | j6 1.1 |
| Kirby | dsmash | [[7, 22]] | YRotN | 2-54 (10) | 0.72 | j33 1.18 |
| Kirby | dsmash | [[7, 22]] | j33 | 7-28 (8) | 1.5 | j34 1.18 |
| Kirby | dsmash | [[7, 22]] | LHandNb | 7-37 (8) | 1.5 | RShoulderN 1.18 |
| Kirby | dsmash | [[7, 22]] | WaistN | 42-54 (49) | 0.8 | j6 1.13 |
| Kirby | nair | [[10, 34]] | YRotN | 1-13 (7) | 0.48 | WaistN 1.06 |
| Kirby | nair | [[10, 34]] | WaistN | 69-78 (73) | 0.77 | j6 1.06 |
| Kirby | nair | [[10, 34]] | LShoulderJA | 0-80 (0) | 0.9 | LShoulderJ 0.95 |
| Kirby | nair | [[10, 34]] | RShoulderJ | 0-80 (0) | 0.9 | RArmJ 0.95 |
| Kirby | fair | [[10, 11], [17, 18], [25, 26]] | LShoulderJA | 0-50 (10) | 1.45 | LShoulderJ 1.39 |
| Kirby | fair | [[10, 11], [17, 18], [25, 26]] | YRotN | 1-47 (11) | 0.73 | LShoulderJA 1.39 |
| Kirby | fair | [[10, 11], [17, 18], [25, 26]] | RShoulderJ | 0-50 (19) | 1.45 | RArmJ 1.22 |
| Kirby | bair | [[6, 8], [9, 20]] | RShoulderJ | 0-44 (8) | 1.7 | RArmJ 2.42 |
| Kirby | bair | [[6, 8], [9, 20]] | YRotN | 1-12 (2) | 0.51 | RShoulderJ 2.42 |
| Kirby | bair | [[6, 8], [9, 20]] | LShoulderJA | 0-44 (13) | 1.5 | LShoulderJ 2.13 |
| Kirby | bair | [[6, 8], [9, 20]] | WaistN | 5-18 (7) | 0.84 | j6 1.19 |
| Kirby | uair | [[11, 13]] | RShoulderJ | 0-40 (12) | 1.4 | RArmJ 1.61 |
| Kirby | uair | [[11, 13]] | YRotN | 6-18 (9) | 1.17 | RShoulderJ 1.61 |
| Kirby | uair | [[11, 13]] | WaistN | 2-13 (4) | 0.9 | j6 1.08 |
| Kirby | uair | [[11, 13]] | LShoulderJA | 0-40 (0) | 0.9 | LShoulderJ 1.05 |
| Kirby | dair | [[18, 19], [21, 22], [24, 25], [27, 28], [30, 31], [33, 34]] | LShoulderJA | 0-60 (37) | 0.69 | LShoulderJ 1.5 |
| Kirby | dair | [[18, 19], [21, 22], [24, 25], [27, 28], [30, 31], [33, 34]] | RShoulderJ | 0-60 (37) | 0.75 | RArmJ 1.5 |
| Kirby | dair | [[18, 19], [21, 22], [24, 25], [27, 28], [30, 31], [33, 34]] | YRotN | 1-57 (13) | 0.6 | LShoulderJA 1.5 |
| Kirby | grab | [[6, 7]] | WaistN | 1-11 (9) | 1.1 | j24 1.43 |
| Kirby | grab | [[6, 7]] | j24 | 6-10 (6) | 1.4 | j25 1.43 |
| Kirby | dash_grab | [[10, 11], [10, 9]] | j24 | 5-22 (10) | 1.4 | j25 1.49 |
| Kirby | dash_grab | [[10, 11], [10, 9]] | WaistN | 12-37 (17) | 1.12 | j24 1.49 |
| Kirby | dash_grab | [[10, 11], [10, 9]] | LHandNb | 0-19 (0) | 1.1 | RShoulderN 1.1 |
| Kirby | dash_grab | [[10, 11], [10, 9]] | RShoulderJ | 0-26 (0) | 0.85 | RArmJ 1.0 |
| Kirby | pummel | [[9, 9]] | WaistN | 1-24 (2) | 0.88 | j29 1.58 |
| Kirby | pummel | [[9, 9]] | j29 | 8-28 (12) | 1.52 | j30 1.58 |
| Kirby | pummel | [[9, 9]] | j24 | 0-30 (0) | 1.4 | j25 1.47 |
| Kirby | pummel | [[9, 9]] | j6 | 19-27 (23) | 1.12 | j7 1.1 |
| Kirby | ledge_quick | [[19, 23]] | LShoulderJA | 14-34 (19) | 1.62 | LShoulderJ 1.62 |
| Kirby | ledge_quick | [[19, 23]] | YRotN | 23-29 (23) | 0.67 | LShoulderJA 1.62 |
| Kirby | ledge_quick | [[19, 23]] | WaistN | 37-54 (38) | 1.21 | j6 1.21 |
| Kirby | ledge_slow | [[43, 59]] | YRotN | 27-69 (29) | 1.29 | HipN 1.29 |
| Kirby | ledge_slow | [[43, 59]] | j33 | 43-61 (47) | 1.5 | j34 1.29 |
| Kirby | ledge_slow | [[43, 59]] | LHandNb | 43-61 (47) | 1.5 | RShoulderN 1.29 |
| Kirby | ledge_slow | [[43, 59]] | WaistN | 65-69 (68) | 0.8 | j6 1.29 |
| Kirby | getup_u | [[19, 20], [24, 25]] | YRotN | 0-48 (10) | 0.75 | RShoulderJ 1.56 |
| Kirby | getup_u | [[19, 20], [24, 25]] | RShoulderJ | 17-28 (22) | 1.56 | RArmJ 1.56 |
| Kirby | getup_d | [[20, 21], [24, 24], [26, 27]] | YRotN | 0-48 (12) | 0.54 | RShoulderJ 1.23 |
| Kirby | getup_d | [[20, 21], [24, 24], [26, 27]] | LShoulderJA | 0-24 (22) | 1.23 | LShoulderJ 1.23 |
| Kirby | getup_d | [[20, 21], [24, 24], [26, 27]] | RShoulderJ | 0-27 (24) | 1.23 | RArmJ 1.23 |
| Bowser | utilt | [[7, 10]] | LShoulderJ | 7-11 (8) | 1.17 | LArmJ 1.29 |
| Bowser | utilt | [[7, 10]] | LArmJ | 7-11 (8) | 1.1 | LHandN 1.29 |
| Bowser | dtilt | [[14, 18], [27, 31]] | LShoulderJ | 27-30 (28) | 1.3 | LArmJ 1.82 |
| Bowser | dtilt | [[14, 18], [27, 31]] | LArmJ | 27-30 (28) | 1.4 | LHandN 1.82 |
| Bowser | dtilt | [[14, 18], [27, 31]] | RArmJ | 10-16 (13) | 1.35 | RHandN 1.69 |
| Bowser | dtilt | [[14, 18], [27, 31]] | RShoulderJ | 13-16 (14) | 1.3 | RArmJ 1.69 |
| Bowser | nair | [[8, 23]] | LShoulderJ | 7-36 (7) | 0.1 | LHandN 1.82 |
| Bowser | nair | [[8, 23]] | LHandN | 7-36 (7) | 13 | L1stNa 1.82 |
| Bowser | nair | [[8, 23]] | RShoulderJ | 7-36 (7) | 0.1 | RHandN 1.82 |
| Bowser | nair | [[8, 23]] | RHandN | 7-36 (7) | 13 | R1stNa 1.82 |
| Bowser | nair | [[8, 23]] | YRotN | 8-43 (21) | 1.4 | LHandN 1.82 |
| Bowser | nair | [[8, 23]] | HipN | 37-37 (37) | 1.1 | LHandN 1.82 |
| Bowser | nair | [[8, 23]] | NeckN | 7-36 (7) | 0.1 | j52 1.81 |
| Bowser | nair | [[8, 23]] | j52 | 7-36 (7) | 12.89 | j52 1.81 |
| Bowser | nair | [[8, 23]] | j56 | 7-36 (7) | 12.89 | j56 1.81 |
| Bowser | nair | [[8, 23]] | LLegJ | 7-36 (7) | 0.1 | LFootJ 1.4 |
| Bowser | nair | [[8, 23]] | LFootJ | 7-36 (7) | 10 | j10 1.4 |
| Bowser | nair | [[8, 23]] | RLegJ | 7-36 (7) | 0.1 | RFootJ 1.4 |
| Bowser | nair | [[8, 23]] | RFootJ | 7-36 (7) | 10 | j19 1.4 |
| Bowser | bair | [[9, 10], [11, 17]] | XRotN | 9-31 (10) | 1.3 | YRotN 1.3 |
| Bowser | uair | [[22, 25]] | YRotN | 36-37 (36) | 1.07 | HipN 1.07 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | LShoulderJ | 14-49 (14) | 0.1 | LHandN 1.69 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | LHandN | 14-49 (14) | 13 | L1stNa 1.69 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | RShoulderJ | 14-49 (14) | 0.1 | RHandN 1.69 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | RHandN | 14-49 (14) | 13 | R1stNa 1.69 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | YRotN | 23-42 (34) | 1.3 | LHandN 1.69 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | HipN | 50-52 (50) | 1.1 | LHandN 1.69 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | NeckN | 14-49 (14) | 0.1 | j52 1.68 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | j52 | 14-49 (14) | 12.89 | j52 1.68 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | j56 | 14-49 (14) | 12.89 | j56 1.68 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | LLegJ | 14-49 (14) | 0.1 | LFootJ 1.3 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | LFootJ | 14-49 (14) | 10 | j10 1.3 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | RLegJ | 14-49 (14) | 0.1 | RFootJ 1.3 |
| Bowser | dair | [[14, 15], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [32, 33], [35, 36], [38, 39]] | RFootJ | 14-49 (14) | 10 | j19 1.3 |
| Bowser | grab | [[8, 9]] | RHandNb | 0-40 (0) | 0.01 | RHandNb 0.01 |
| Bowser | dash_grab | [[9, 11]] | RHandNb | 0-50 (0) | 0.01 | RHandNb 0.01 |
| Bowser | pummel | [[9, 9]] | RHandNb | 0-24 (0) | 0.01 | RHandNb 0.01 |
| Bowser | ledge_quick | [[7, 34]] | j23 | 8-36 (9) | 1.1 | j23 1.1 |
| Bowser | ledge_quick | [[7, 34]] | j24 | 4-34 (5) | 0.3 | j25 1.0 |
| Link | jab1 | [[6, 8]] | j48 | 0-25 (0) | 0.89 | j48 0.89 |
| Link | jab2 | [[6, 7]] | j48 | 0-22 (10) | 0.88 | j48 0.89 |
| Link | jab3 | [[6, 10]] | j48 | 0-50 (0) | 0.88 | j48 0.89 |
| Link | dash_attack | [[7, 12]] | j48 | 0-54 (0) | 0.89 | j48 0.89 |
| Link | ftilt | [[16, 19]] | j48 | 0-40 (0) | 0.89 | j48 0.89 |
| Link | utilt | [[9, 15]] | j48 | 0-30 (0) | 0.89 | j48 0.89 |
| Link | dtilt | [[14, 16]] | j48 | 0-40 (0) | 0.89 | j48 0.89 |
| Link | fsmash | [[15, 18]] | j48 | 0-50 (16) | 0.66 | j48 0.89 |
| Link | fsmash | [[15, 18]] | j26 | 13-16 (15) | 1.1 | j26 1.1 |
| Link | usmash | [[11, 15], [26, 28], [41, 43]] | j48 | 0-61 (43) | 0.77 | j48 0.89 |
| Link | dsmash | [[9, 11], [21, 23]] | j48 | 0-50 (0) | 0.89 | j48 0.89 |
| Link | nair | [[4, 5], [6, 40]] | j48 | 0-40 (0) | 0.89 | j48 0.89 |
| Link | fair | [[14, 16], [30, 33]] | j48 | 0-56 (0) | 0.89 | j48 0.89 |
| Link | bair | [[6, 9], [18, 23]] | j48 | 0-40 (0) | 0.89 | j48 0.89 |
| Link | uair | [[5, 49]] | j48 | 0-70 (0) | 0.89 | j48 0.89 |
| Link | dair | [[13, 64]] | j48 | 0-90 (0) | 0.89 | j48 0.89 |
| Link | grab | [[10, 12], [13, 17]] | j48 | 0-85 (0) | 0.89 | j48 0.89 |
| Link | dash_grab | [[11, 11], [12, 17]] | j48 | 0-95 (0) | 0.89 | j48 0.89 |
| Link | pummel | [[9, 9]] | j48 | 0-25 (0) | 0.89 | j48 0.89 |
| Link | ledge_quick | [[27, 29]] | j48 | 0-56 (0) | 0.89 | j48 0.89 |
| Link | ledge_slow | [[50, 55]] | j48 | 0-70 (0) | 0.89 | j48 0.89 |
| Link | getup_u | [[19, 20], [28, 29]] | j48 | 0-50 (0) | 0.83 | j48 0.89 |
| Link | getup_d | [[15, 16], [24, 26]] | j48 | 0-50 (0) | 0.89 | j48 0.89 |
| Luigi | jab1 | [[2, 3]] | LFootJA | 2-13 (2) | 1.3 | j10 2.08 |
| Luigi | jab1 | [[2, 3]] | j10 | 2-4 (2) | 1.6 | RLegJA 2.08 |
| Luigi | jab2 | [[2, 3]] | L4thNb | 2-7 (2) | 1.4 | LThumbNb 1.96 |
| Luigi | jab2 | [[2, 3]] | LThumbNb | 2-4 (2) | 1.4 | j34 1.96 |
| Luigi | jab2 | [[2, 3]] | LFootJA | 0-2 (0) | 1.06 | LFootJ 1.06 |
| Luigi | jab3 | [[4, 5]] | HipN | 4-7 (4) | 1.9 | R2ndNa 1.9 |
| Luigi | jab3 | [[4, 5]] | R3rdNa | 4-7 (4) | 0.7 | R3rdNb 1.26 |
| Luigi | jab3 | [[4, 5]] | R3rdNb | 4-4 (4) | 0.95 | R4thNa 1.26 |
| Luigi | jab3 | [[4, 5]] | RThumbNb | 4-7 (4) | 0.7 | j55 1.26 |
| Luigi | jab3 | [[4, 5]] | j55 | 4-4 (4) | 0.95 | ThrowN 1.26 |
| Luigi | jab3 | [[4, 5]] | LLegJA | 4-7 (4) | 0.65 | LFootJA 1.24 |
| Luigi | jab3 | [[4, 5]] | R4thNb | 4-4 (4) | 0.95 | RHandNb 1.21 |
| Luigi | jab3 | [[4, 5]] | TransN2 | 4-4 (4) | 0.95 | TopN 1.21 |
| Luigi | jab3 | [[4, 5]] | L4thNb | 4-4 (4) | 0.95 | LThumbNa 1.19 |
| Luigi | jab3 | [[4, 5]] | LHandN | 4-6 (4) | 0.85 | L1stNa 1.11 |
| Luigi | dash_attack | [[4, 4], [10, 10], [16, 16], [22, 22], [29, 29], [37, 37]] | L4thNb | 3-53 (4) | 1.2 | LThumbNb 1.68 |
| Luigi | dash_attack | [[4, 4], [10, 10], [16, 16], [22, 22], [29, 29], [37, 37]] | LThumbNb | 3-53 (4) | 1.4 | j34 1.68 |
| Luigi | dash_attack | [[4, 4], [10, 10], [16, 16], [22, 22], [29, 29], [37, 37]] | LFootJA | 8-41 (10) | 1.2 | j10 1.68 |
| Luigi | dash_attack | [[4, 4], [10, 10], [16, 16], [22, 22], [29, 29], [37, 37]] | j10 | 8-42 (10) | 1.4 | RLegJA 1.68 |
| Luigi | ftilt_hi | [[4, 8]] | j55 | 3-6 (3) | 1.1 | ThrowN 1.51 |
| Luigi | ftilt_hi | [[4, 8]] | RThumbNb | 5-19 (5) | 1.4 | j55 1.51 |
| Luigi | ftilt | [[4, 8]] | j55 | 3-6 (3) | 1.1 | ThrowN 1.51 |
| Luigi | ftilt | [[4, 8]] | RThumbNb | 5-19 (5) | 1.4 | j55 1.51 |
| Luigi | ftilt_lw | [[4, 8]] | j55 | 3-6 (3) | 1.1 | ThrowN 1.51 |
| Luigi | ftilt_lw | [[4, 8]] | RThumbNb | 5-19 (5) | 1.4 | j55 1.51 |
| Luigi | utilt | [[4, 12]] | L4thNb | 5-10 (6) | 1.5 | LThumbNb 2.34 |
| Luigi | utilt | [[4, 12]] | LThumbNa | 6-10 (8) | 1.21 | LThumbNb 2.34 |
| Luigi | utilt | [[4, 12]] | LThumbNb | 6-10 (8) | 1.34 | j34 2.34 |
| Luigi | utilt | [[4, 12]] | R1stNb | 5-8 (7) | 1.2 | R1stNb 2.16 |
| Luigi | dtilt | [[5, 8]] | RThumbNb | 5-9 (5) | 1.3 | j55 1.43 |
| Luigi | dtilt | [[5, 8]] | j55 | 5-7 (5) | 1.1 | ThrowN 1.43 |
| Luigi | fsmash_hi | [[12, 13]] | LFootJA | 11-17 (12) | 1.35 | j10 1.86 |
| Luigi | fsmash_hi | [[12, 13]] | YRotN | 12-13 (12) | 1.15 | j10 1.86 |
| Luigi | fsmash_hi | [[12, 13]] | j10 | 12-16 (12) | 1.2 | RLegJA 1.86 |
| Luigi | fsmash_hi | [[12, 13]] | LHandN | 12-12 (12) | 0.95 | L1stNa 1.09 |
| Luigi | fsmash_hi | [[12, 13]] | L4thNb | 12-12 (12) | 0.95 | LThumbNa 1.09 |
| Luigi | fsmash | [[12, 13]] | LFootJA | 11-17 (12) | 1.35 | j10 1.86 |
| Luigi | fsmash | [[12, 13]] | YRotN | 12-13 (12) | 1.15 | j10 1.86 |
| Luigi | fsmash | [[12, 13]] | j10 | 12-16 (12) | 1.2 | RLegJA 1.86 |
| Luigi | fsmash | [[12, 13]] | LHandN | 12-12 (12) | 0.95 | L1stNa 1.09 |
| Luigi | fsmash | [[12, 13]] | L4thNb | 12-12 (12) | 0.95 | LThumbNa 1.09 |
| Luigi | fsmash_lw | [[12, 13]] | LFootJA | 11-17 (12) | 1.35 | j10 1.86 |
| Luigi | fsmash_lw | [[12, 13]] | YRotN | 12-13 (12) | 1.15 | j10 1.86 |
| Luigi | fsmash_lw | [[12, 13]] | j10 | 12-16 (12) | 1.2 | RLegJA 1.86 |
| Luigi | fsmash_lw | [[12, 13]] | LHandN | 12-12 (12) | 0.95 | L1stNa 1.09 |
| Luigi | fsmash_lw | [[12, 13]] | L4thNb | 12-12 (12) | 0.95 | LThumbNa 1.09 |
| Luigi | usmash | [[9, 11]] | LArmJ | 11-12 (11) | 1.1 | LHandN 1.1 |
| Luigi | dsmash | [[5, 6], [14, 15]] | R3rdNa | 5-16 (7) | 0.89 | R3rdNb 1.39 |
| Luigi | dsmash | [[5, 6], [14, 15]] | R3rdNb | 5-17 (5) | 1.3 | R4thNa 1.39 |
| Luigi | dsmash | [[5, 6], [14, 15]] | RThumbNb | 5-16 (7) | 0.89 | j55 1.39 |
| Luigi | dsmash | [[5, 6], [14, 15]] | j55 | 5-17 (5) | 1.3 | ThrowN 1.39 |
| Luigi | nair | [[3, 6], [7, 31]] | R3rdNa | 3-4 (3) | 1.1 | R3rdNb 1.12 |
| Luigi | fair | [[7, 10]] | LFootJA | 7-10 (9) | 1.2 | j10 2.03 |
| Luigi | fair | [[7, 10]] | j10 | 7-10 (9) | 1.3 | RLegJA 2.03 |
| Luigi | fair | [[7, 10]] | LFootJ | 8-16 (9) | 1.3 | j10 2.03 |
| Luigi | bair | [[6, 17]] | R3rdNa | 3-10 (7) | 1.8 | R3rdNb 1.8 |
| Luigi | bair | [[6, 17]] | RThumbNb | 6-10 (7) | 1.8 | j55 1.8 |
| Luigi | uair | [[5, 7]] | RThumbNb | 3-13 (4) | 1.75 | j55 1.75 |
| Luigi | dair | [[10, 14]] | R3rdNa | 10-15 (12) | 1.3 | R3rdNb 1.3 |
| Luigi | dair | [[10, 14]] | RThumbNb | 10-15 (12) | 1.3 | j55 1.3 |
| Luigi | grab | [[6, 7]] | LFootJA | 2-13 (6) | 1.2 | LFootJ 1.2 |
| Luigi | grab | [[6, 7]] | L4thNb | 2-13 (6) | 1.2 | LThumbNa 1.2 |
| Luigi | dash_grab | [[10, 11]] | LFootJA | 4-18 (10) | 1.2 | LFootJ 1.2 |
| Luigi | dash_grab | [[10, 11]] | L4thNb | 4-18 (10) | 1.2 | LThumbNa 1.2 |
| Luigi | pummel | [[16, 16]] | LFootJA | 0-24 (0) | 1.2 | LFootJ 1.2 |
| Luigi | pummel | [[16, 16]] | L4thNb | 0-24 (0) | 1.2 | LThumbNa 1.2 |
| Luigi | ledge_quick | [[24, 36]] | R3rdNa | 24-32 (26) | 1.56 | R3rdNb 1.82 |
| Luigi | ledge_quick | [[24, 36]] | R3rdNb | 24-31 (26) | 1.17 | R4thNa 1.82 |
| Luigi | ledge_quick | [[24, 36]] | RThumbNb | 24-32 (26) | 1.56 | j55 1.82 |
| Luigi | ledge_quick | [[24, 36]] | j55 | 24-31 (26) | 1.17 | ThrowN 1.82 |
| Luigi | ledge_slow | [[40, 44]] | RThumbNb | 39-46 (40) | 1.4 | j55 1.88 |
| Luigi | ledge_slow | [[40, 44]] | j55 | 39-46 (41) | 1.36 | ThrowN 1.88 |
| Luigi | getup_u | [[20, 21], [24, 25]] | RThumbNb | 9-28 (20) | 1.5 | j55 1.5 |
| Luigi | getup_u | [[20, 21], [24, 25]] | R3rdNa | 19-28 (20) | 1.5 | R3rdNb 1.5 |
| Luigi | getup_d | [[19, 20], [25, 26]] | LThumbNb | 17-43 (33) | 1.56 | j34 1.56 |
| Mario | jab1 | [[2, 3]] | LShoulderJA | 2-12 (2) | 1.4 | LArmJ 2.24 |
| Mario | jab1 | [[2, 3]] | LArmJ | 2-4 (2) | 1.6 | LHandN 2.24 |
| Mario | jab2 | [[2, 3]] | RShoulderJ | 2-7 (2) | 1.4 | RHandN 1.96 |
| Mario | jab2 | [[2, 3]] | RHandN | 2-3 (2) | 1.4 | R1stNa 1.96 |
| Mario | jab2 | [[2, 3]] | LShoulderJA | 0-2 (0) | 1.06 | LShoulderJ 1.06 |
| Mario | jab3 | [[4, 8]] | RLegJ | 3-7 (4) | 1.5 | RFootJA 2.18 |
| Mario | jab3 | [[4, 8]] | RLegJA | 5-8 (5) | 1.48 | RFootJA 2.18 |
| Mario | jab3 | [[4, 8]] | RFootJA | 5-8 (5) | 1.23 | RFootJ 2.18 |
| Mario | ftilt_hi | [[5, 7]] | RLegJ | 3-6 (3) | 1.1 | RKneeJ 1.51 |
| Mario | ftilt_hi | [[5, 7]] | RLegJA | 5-19 (5) | 1.4 | RLegJ 1.51 |
| Mario | ftilt | [[5, 7]] | RLegJ | 3-6 (3) | 1.1 | RKneeJ 1.51 |
| Mario | ftilt | [[5, 7]] | RLegJA | 5-19 (5) | 1.4 | RLegJ 1.51 |
| Mario | ftilt_lw | [[5, 7]] | RLegJ | 3-6 (3) | 1.1 | RKneeJ 1.51 |
| Mario | ftilt_lw | [[5, 7]] | RLegJA | 5-19 (5) | 1.4 | RLegJ 1.51 |
| Mario | utilt | [[4, 12]] | RShoulderN | 3-17 (6) | 1.3 | RHandN 3.01 |
| Mario | utilt | [[4, 12]] | RHandN | 3-28 (12) | 1.62 | R1stNa 3.01 |
| Mario | utilt | [[4, 12]] | RArmJ | 4-23 (6) | 1.26 | RHandN 3.01 |
| Mario | utilt | [[4, 12]] | RShoulderJ | 5-18 (6) | 1.14 | RHandN 3.01 |
| Mario | dtilt | [[5, 8]] | RLegJA | 5-8 (5) | 2 | RLegJ 2.0 |
| Mario | fsmash_hi | [[12, 16]] | YRotN | 12-13 (12) | 1.15 | LArmJ 1.64 |
| Mario | fsmash_hi | [[12, 16]] | LShoulderJA | 12-13 (12) | 1.3 | LArmJ 1.64 |
| Mario | fsmash_hi | [[12, 16]] | LArmJ | 12-12 (12) | 1.1 | LHandN 1.64 |
| Mario | fsmash_hi | [[12, 16]] | LThumbNb | 12-36 (12) | 0.73 | LThumbNb 1.09 |
| Mario | fsmash_hi | [[12, 16]] | L1stNa | 12-26 (14) | 0.55 | L1stNa 1.05 |
| Mario | fsmash_hi | [[12, 16]] | L2ndNa | 12-26 (12) | 0.53 | L2ndNa 1.0 |
| Mario | fsmash_hi | [[12, 16]] | L3rdNa | 12-26 (12) | 0.44 | L3rdNa 1.0 |
| Mario | fsmash_hi | [[12, 16]] | L4thNa | 12-26 (12) | 0.48 | L4thNa 1.0 |
| Mario | fsmash | [[12, 16]] | YRotN | 12-13 (12) | 1.15 | LArmJ 1.64 |
| Mario | fsmash | [[12, 16]] | LShoulderJA | 12-17 (12) | 1.3 | LArmJ 1.64 |
| Mario | fsmash | [[12, 16]] | LArmJ | 12-12 (12) | 1.1 | LHandN 1.64 |
| Mario | fsmash | [[12, 16]] | LThumbNb | 3-36 (12) | 0.73 | LThumbNb 1.09 |
| Mario | fsmash | [[12, 16]] | L1stNa | 12-26 (14) | 0.55 | L1stNa 1.05 |
| Mario | fsmash | [[12, 16]] | L2ndNa | 12-26 (12) | 0.53 | L2ndNa 1.0 |
| Mario | fsmash | [[12, 16]] | L3rdNa | 12-26 (12) | 0.44 | L3rdNa 1.0 |
| Mario | fsmash | [[12, 16]] | L4thNa | 12-26 (12) | 0.48 | L4thNa 1.0 |
| Mario | fsmash_lw | [[12, 16]] | YRotN | 12-13 (12) | 1.1 | LThumbNb 2.06 |
| Mario | fsmash_lw | [[12, 16]] | LShoulderJA | 12-13 (12) | 1.3 | LThumbNb 2.06 |
| Mario | fsmash_lw | [[12, 16]] | LThumbNb | 12-24 (21) | 1.5 | LThumbNb 2.06 |
| Mario | fsmash_lw | [[12, 16]] | LArmJ | 12-12 (12) | 1.1 | LHandN 1.57 |
| Mario | fsmash_lw | [[12, 16]] | L1stNa | 12-26 (14) | 0.55 | L1stNa 1.01 |
| Mario | fsmash_lw | [[12, 16]] | L2ndNa | 12-26 (12) | 0.53 | L2ndNa 1.0 |
| Mario | fsmash_lw | [[12, 16]] | L3rdNa | 12-26 (12) | 0.44 | L3rdNa 1.0 |
| Mario | fsmash_lw | [[12, 16]] | L4thNa | 12-26 (12) | 0.48 | L4thNa 1.0 |
| Mario | usmash | [[9, 11]] | j22 | 11-12 (11) | 1.1 | NeckN 1.1 |
| Mario | dsmash | [[5, 6], [14, 14]] | LLegJ | 5-16 (7) | 0.89 | LKneeJ 1.39 |
| Mario | dsmash | [[5, 6], [14, 14]] | LKneeJ | 5-17 (5) | 1.3 | LFootJA 1.39 |
| Mario | dsmash | [[5, 6], [14, 14]] | RLegJA | 5-16 (7) | 0.89 | RLegJ 1.39 |
| Mario | dsmash | [[5, 6], [14, 14]] | RLegJ | 5-17 (5) | 1.3 | RKneeJ 1.39 |
| Mario | fair | [[18, 22]] | RHandN | 6-37 (17) | 1.5 | R1stNa 2.4 |
| Mario | fair | [[18, 22]] | RShoulderJ | 13-36 (17) | 1.6 | RHandN 2.4 |
| Mario | fair | [[18, 22]] | RHandNb | 13-39 (17) | 0.45 | RHandNb 1.15 |
| Mario | bair | [[6, 8], [9, 17]] | LLegJ | 3-15 (7) | 2 | LKneeJ 2.0 |
| Mario | bair | [[6, 8], [9, 17]] | RLegJA | 6-15 (7) | 2 | RLegJ 2.0 |
| Mario | uair | [[4, 9]] | RLegJA | 3-13 (4) | 1.75 | RLegJ 1.75 |
| Mario | grab | [[6, 7]] | LShoulderJA | 2-13 (6) | 1.2 | LShoulderJ 1.2 |
| Mario | grab | [[6, 7]] | RShoulderJ | 2-13 (6) | 1.2 | RArmJ 1.2 |
| Mario | dash_grab | [[10, 11]] | LShoulderJA | 4-18 (10) | 1.2 | LShoulderJ 1.2 |
| Mario | dash_grab | [[10, 11]] | RShoulderJ | 4-18 (10) | 1.2 | RArmJ 1.2 |
| Mario | pummel | [[16, 16]] | LShoulderJA | 0-24 (0) | 1.2 | LShoulderJ 1.2 |
| Mario | pummel | [[16, 16]] | RShoulderJ | 0-24 (0) | 1.2 | RArmJ 1.2 |
| Mario | ledge_quick | [[24, 36]] | LLegJ | 24-32 (26) | 1.56 | LKneeJ 1.82 |
| Mario | ledge_quick | [[24, 36]] | LKneeJ | 24-31 (26) | 1.17 | LFootJA 1.82 |
| Mario | ledge_quick | [[24, 36]] | RLegJA | 24-32 (26) | 1.56 | RLegJ 1.82 |
| Mario | ledge_quick | [[24, 36]] | RLegJ | 24-31 (26) | 1.17 | RKneeJ 1.82 |
| Mario | ledge_slow | [[40, 44]] | RLegJA | 39-46 (40) | 1.4 | RLegJ 1.88 |
| Mario | ledge_slow | [[40, 44]] | RLegJ | 39-46 (41) | 1.36 | RKneeJ 1.88 |
| Mario | getup_u | [[20, 21], [24, 25]] | RLegJA | 9-28 (20) | 1.5 | RLegJ 1.5 |
| Mario | getup_u | [[20, 21], [24, 25]] | LLegJ | 19-28 (20) | 1.5 | LKneeJ 1.5 |
| Mario | getup_d | [[19, 20], [25, 26]] | RHandN | 17-43 (33) | 1.56 | R1stNa 1.56 |
| Ness | jab1 | [[3, 4]] | LArmJ | 3-6 (3) | 1.5 | LHandN 2.7 |
| Ness | jab1 | [[3, 4]] | LHandN | 3-6 (3) | 1.8 | L3rdNa 2.7 |
| Ness | jab2 | [[3, 4]] | j32 | 3-4 (3) | 1.5 | j33 2.7 |
| Ness | jab2 | [[3, 4]] | j33 | 3-20 (3) | 1.8 | j34 2.7 |
| Ness | jab3 | [[6, 9]] | j55 | 6-9 (6) | 1.5 | j58 2.7 |
| Ness | jab3 | [[6, 9]] | j56 | 6-8 (6) | 1.2 | j58 2.7 |
| Ness | jab3 | [[6, 9]] | j58 | 6-9 (6) | 1.5 | j59 2.7 |
| Ness | dash_attack | [[8, 8], [15, 15], [22, 22]] | LShoulderJ | 8-8 (8) | 1.1 | LHandN 6.05 |
| Ness | dash_attack | [[8, 8], [15, 15], [22, 22]] | LArmJ | 8-25 (8) | 2.2 | LHandN 6.05 |
| Ness | dash_attack | [[8, 8], [15, 15], [22, 22]] | LHandN | 8-29 (8) | 2.5 | L3rdNa 6.05 |
| Ness | dash_attack | [[8, 8], [15, 15], [22, 22]] | RThumbNb | 8-8 (8) | 1.1 | j33 6.05 |
| Ness | dash_attack | [[8, 8], [15, 15], [22, 22]] | j32 | 8-25 (8) | 2.2 | j33 6.05 |
| Ness | dash_attack | [[8, 8], [15, 15], [22, 22]] | j33 | 8-29 (8) | 2.5 | j34 6.05 |
| Ness | ftilt_hi | [[7, 11]] | j58 | 5-20 (8) | 1.68 | j59 2.09 |
| Ness | ftilt_hi | [[7, 11]] | j55 | 6-18 (8) | 1.24 | j58 2.09 |
| Ness | ftilt | [[7, 11]] | j58 | 5-20 (8) | 1.68 | j59 2.09 |
| Ness | ftilt | [[7, 11]] | j55 | 6-18 (8) | 1.24 | j58 2.09 |
| Ness | ftilt_lw | [[7, 11]] | j58 | 5-20 (8) | 1.68 | j59 2.09 |
| Ness | ftilt_lw | [[7, 11]] | j55 | 6-18 (8) | 1.24 | j58 2.09 |
| Ness | utilt | [[5, 9]] | LShoulderJ | 4-17 (5) | 1.27 | LHandN 2.54 |
| Ness | utilt | [[5, 9]] | LHandN | 4-19 (5) | 2 | L3rdNa 2.54 |
| Ness | utilt | [[5, 9]] | RThumbNb | 4-17 (6) | 1.27 | j33 2.54 |
| Ness | utilt | [[5, 9]] | j33 | 4-19 (5) | 2 | j34 2.54 |
| Ness | utilt | [[5, 9]] | j53 | 15-24 (19) | 1.23 | j53 1.23 |
| Ness | utilt | [[5, 9]] | j60 | 15-24 (19) | 1.23 | j60 1.23 |
| Ness | dtilt | [[3, 5]] | j55 | 2-11 (7) | 1.23 | j58 2.66 |
| Ness | dtilt | [[3, 5]] | j58 | 2-13 (5) | 2.17 | j59 2.66 |
| Ness | fsmash | [[16, 17]] | RThumbNb | 15-35 (29) | 1.34 | j32 1.49 |
| Ness | fsmash | [[16, 17]] | j32 | 15-34 (29) | 1.11 | j33 1.49 |
| Ness | fsmash | [[16, 17]] | j33 | 15-18 (16) | 0.9 | j34 1.49 |
| Ness | nair | [[5, 12], [13, 23]] | LShoulderJ | 4-22 (12) | 1.24 | LArmJ 1.48 |
| Ness | nair | [[5, 12], [13, 23]] | LArmJ | 4-22 (6) | 1.2 | LHandN 1.48 |
| Ness | nair | [[5, 12], [13, 23]] | RThumbNb | 4-22 (12) | 1.24 | j32 1.48 |
| Ness | nair | [[5, 12], [13, 23]] | j32 | 4-22 (6) | 1.2 | j33 1.48 |
| Ness | fair | [[8, 10], [11, 13], [14, 16], [17, 19], [20, 21]] | LShoulderJ | 8-9 (8) | 1.4 | LHandN 3.36 |
| Ness | fair | [[8, 10], [11, 13], [14, 16], [17, 19], [20, 21]] | LArmJ | 8-24 (8) | 1.2 | LHandN 3.36 |
| Ness | fair | [[8, 10], [11, 13], [14, 16], [17, 19], [20, 21]] | LHandN | 8-24 (8) | 2 | L3rdNa 3.36 |
| Ness | fair | [[8, 10], [11, 13], [14, 16], [17, 19], [20, 21]] | RThumbNb | 8-9 (8) | 1.4 | j33 3.36 |
| Ness | fair | [[8, 10], [11, 13], [14, 16], [17, 19], [20, 21]] | j32 | 8-24 (8) | 1.2 | j33 3.36 |
| Ness | fair | [[8, 10], [11, 13], [14, 16], [17, 19], [20, 21]] | j33 | 8-24 (8) | 2 | j34 3.36 |
| Ness | bair | [[10, 11], [12, 19]] | TransN2 | 10-16 (10) | 1.1 | TopN 1.45 |
| Ness | bair | [[10, 11], [12, 19]] | TopN | 10-16 (10) | 1.1 | TopN 1.45 |
| Ness | bair | [[10, 11], [12, 19]] | TopN | 10-18 (10) | 1.2 | j52 1.45 |
| Ness | bair | [[10, 11], [12, 19]] | j55 | 10-16 (10) | 1.1 | j58 1.45 |
| Ness | bair | [[10, 11], [12, 19]] | j56 | 10-16 (10) | 1.1 | j58 1.45 |
| Ness | bair | [[10, 11], [12, 19]] | j58 | 10-18 (10) | 1.2 | j59 1.45 |
| Ness | uair | [[8, 11]] | RShoulderJ | 8-11 (9) | 1.35 | RArmJ 1.35 |
| Ness | dair | [[20, 28]] | j55 | 20-33 (20) | 1.2 | j58 1.87 |
| Ness | dair | [[20, 28]] | j56 | 20-34 (20) | 1.3 | j58 1.87 |
| Ness | dair | [[20, 28]] | j58 | 20-21 (20) | 1.2 | j59 1.87 |
| Ness | pummel | [[15, 15]] | LShoulderJ | 1-14 (7) | 1.12 | LArmJ 1.26 |
| Ness | pummel | [[15, 15]] | LArmJ | 1-14 (7) | 1.12 | LHandN 1.26 |
| Ness | ledge_slow | [[39, 41]] | j55 | 38-57 (40) | 1.5 | j58 2.77 |
| Ness | ledge_slow | [[39, 41]] | j56 | 38-56 (40) | 1.43 | j58 2.77 |
| Ness | ledge_slow | [[39, 41]] | j58 | 39-42 (40) | 1.29 | j59 2.77 |
| Ness | ledge_slow | [[39, 41]] | R3rdNb | 38-45 (41) | 0.85 | R3rdNb 1.0 |
| Ness | getup_u | [[20, 21], [24, 25]] | LHandN | 0-50 (0) | 0.9 | L3rdNa 0.9 |
| Ness | getup_u | [[20, 21], [24, 25]] | R3rdNb | 0-0 (0) | 0.94 | R3rdNb 1.0 |
| Ness | getup_d | [[19, 20], [25, 26]] | j33 | 14-44 (32) | 1.64 | j34 1.64 |
| Ness | getup_d | [[19, 20], [25, 26]] | LHandN | 0-50 (0) | 0.9 | L3rdNa 0.9 |
| Peach | jab1 | [[2, 3]] | j93 | 0-20 (0) | 0.9 | j93 0.9 |
| Peach | jab2 | [[2, 3]] | j93 | 0-20 (0) | 0.9 | j93 0.9 |
| Peach | dash_attack | [[6, 8], [9, 20]] | j93 | 0-38 (0) | 0.9 | j93 0.9 |
| Peach | dash_attack | [[6, 8], [9, 20]] | j20 | 0-8 (0) | 0.94 | j21 1.0 |
| Peach | dash_attack | [[6, 8], [9, 20]] | j38 | 0-29 (0) | 0.8 | RLegJA 1.0 |
| Peach | dash_attack | [[6, 8], [9, 20]] | j44 | 0-27 (0) | 0.85 | j45 1.0 |
| Peach | dash_attack | [[6, 8], [9, 20]] | j50 | 0-27 (0) | 0.85 | ThrowN 1.0 |
| Peach | dash_attack | [[6, 8], [9, 20]] | j56 | 0-22 (0) | 0.9 | j57 1.0 |
| Peach | dash_attack | [[6, 8], [9, 20]] | j62 | 0-22 (0) | 0.9 | j63 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | j93 | 0-42 (0) | 0.9 | j93 0.9 |
| Peach | ftilt | [[6, 7], [8, 13]] | j21 | 1-34 (2) | 0.61 | RShoulderN 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | j27 | 1-34 (2) | 0.61 | j28 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | LKneeJ | 1-34 (2) | 0.61 | LFootJA 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | j63 | 1-34 (2) | 0.7 | j64 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | j37 | 2-38 (9) | 0.59 | j38 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | RFootJ | 2-38 (9) | 0.6 | j44 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | j49 | 2-39 (9) | 0.53 | j50 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | RArmJ | 3-39 (9) | 0.76 | RHandN 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | TopN | 3-39 (9) | 0.7 | j56 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | j61 | 3-38 (9) | 0.7 | j62 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | j19 | 4-39 (9) | 0.82 | j20 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | LLegJA | 4-38 (13) | 0.85 | LLegJ 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | RLegJA | 6-34 (32) | 0.75 | RLegJ 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | j45 | 6-34 (32) | 0.75 | j46 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | ThrowN | 6-34 (32) | 0.75 | TransN2 1.0 |
| Peach | ftilt | [[6, 7], [8, 13]] | j57 | 6-34 (32) | 0.75 | j58 1.0 |
| Peach | utilt | [[9, 13]] | j93 | 0-40 (0) | 0.9 | j93 0.9 |
| Peach | utilt | [[9, 13]] | LLegJ | 3-39 (33) | 0.58 | LKneeJ 1.0 |
| Peach | utilt | [[9, 13]] | j20 | 6-39 (33) | 0.5 | j21 1.0 |
| Peach | utilt | [[9, 13]] | j62 | 6-38 (29) | 0.57 | j63 1.0 |
| Peach | dtilt | [[12, 13]] | RLegJA | 0-28 (12) | 0.27 | RLegJ 0.51 |
| Peach | dtilt | [[12, 13]] | j45 | 0-28 (17) | 0.53 | j46 0.77 |
| Peach | dtilt | [[12, 13]] | j93 | 0-28 (0) | 0.9 | j93 0.9 |
| Peach | dtilt | [[12, 13]] | j63 | 0-28 (0) | 0.91 | j64 0.91 |
| Peach | dtilt | [[12, 13]] | ThrowN | 0-28 (0) | 0.68 | TransN2 1.06 |
| Peach | dtilt | [[12, 13]] | RHandN | 1-26 (2) | 0.45 | j27 1.0 |
| Peach | dtilt | [[12, 13]] | j20 | 10-26 (17) | 0.73 | j21 1.0 |
| Peach | dtilt | [[12, 13]] | j57 | 10-26 (17) | 0.71 | j58 1.0 |
| Peach | fsmash | [] | j93 | 0-48 (0) | 0.9 | j93 0.9 |
| Peach | usmash | [[13, 22]] | j93 | 0-45 (0) | 0.9 | j93 0.9 |
| Peach | dsmash | [[5, 6], [9, 10], [13, 14], [17, 18], [21, 22]] | j93 | 0-40 (0) | 0.9 | j93 0.9 |
| Peach | dsmash | [[5, 6], [9, 10], [13, 14], [17, 18], [21, 22]] | j21 | 4-35 (17) | 0.38 | RShoulderN 1.0 |
| Peach | dsmash | [[5, 6], [9, 10], [13, 14], [17, 18], [21, 22]] | j27 | 4-35 (17) | 0.38 | j28 1.0 |
| Peach | dsmash | [[5, 6], [9, 10], [13, 14], [17, 18], [21, 22]] | LKneeJ | 4-35 (17) | 0.38 | LFootJA 1.0 |
| Peach | dsmash | [[5, 6], [9, 10], [13, 14], [17, 18], [21, 22]] | RLegJA | 4-35 (17) | 0.38 | RLegJ 1.0 |
| Peach | dsmash | [[5, 6], [9, 10], [13, 14], [17, 18], [21, 22]] | j45 | 4-35 (17) | 0.38 | j46 1.0 |
| Peach | dsmash | [[5, 6], [9, 10], [13, 14], [17, 18], [21, 22]] | ThrowN | 4-35 (17) | 0.38 | TransN2 1.0 |
| Peach | dsmash | [[5, 6], [9, 10], [13, 14], [17, 18], [21, 22]] | j57 | 4-35 (17) | 0.38 | j58 1.0 |
| Peach | dsmash | [[5, 6], [9, 10], [13, 14], [17, 18], [21, 22]] | j63 | 4-35 (17) | 0.38 | j64 1.0 |
| Peach | nair | [[3, 6], [7, 23]] | j93 | 0-50 (0) | 0.9 | j93 0.9 |
| Peach | fair | [[16, 20]] | j93 | 0-55 (0) | 0.9 | j93 0.9 |
| Peach | fair | [[16, 20]] | j20 | 1-54 (5) | 0.22 | j21 1.0 |
| Peach | fair | [[16, 20]] | RHandN | 1-53 (8) | 0.42 | j27 1.0 |
| Peach | fair | [[16, 20]] | LLegJ | 1-52 (8) | 0.4 | LKneeJ 1.0 |
| Peach | fair | [[16, 20]] | j44 | 3-48 (15) | 0.72 | j45 1.0 |
| Peach | fair | [[16, 20]] | TopN | 4-43 (15) | 0.49 | j56 1.0 |
| Peach | fair | [[16, 20]] | j62 | 4-47 (17) | 0.75 | j63 1.0 |
| Peach | bair | [[6, 9], [10, 22]] | j93 | 0-45 (0) | 0.9 | j93 0.9 |
| Peach | bair | [[6, 9], [10, 22]] | j56 | 1-26 (18) | 0.54 | j57 1.08 |
| Peach | bair | [[6, 9], [10, 22]] | j20 | 23-38 (27) | 0.45 | j21 1.07 |
| Peach | bair | [[6, 9], [10, 22]] | LLegJ | 13-36 (27) | 0.58 | LKneeJ 1.06 |
| Peach | bair | [[6, 9], [10, 22]] | j50 | 1-33 (18) | 0.52 | ThrowN 1.05 |
| Peach | bair | [[6, 9], [10, 22]] | j38 | 2-33 (18) | 0.52 | RLegJA 1.05 |
| Peach | bair | [[6, 9], [10, 22]] | j44 | 2-25 (18) | 0.55 | j45 1.05 |
| Peach | bair | [[6, 9], [10, 22]] | j62 | 1-25 (18) | 0.72 | j63 1.03 |
| Peach | uair | [[7, 11]] | j56 | 5-29 (9) | 0.37 | j57 1.09 |
| Peach | uair | [[7, 11]] | j93 | 0-36 (8) | 0.7 | j93 0.92 |
| Peach | uair | [[7, 11]] | j49 | 2-30 (20) | 0.45 | j50 1.06 |
| Peach | uair | [[7, 11]] | j37 | 7-23 (9) | 0.62 | j38 1.04 |
| Peach | uair | [[7, 11]] | RFootJ | 2-23 (9) | 0.68 | j44 1.02 |
| Peach | uair | [[7, 11]] | j20 | 1-25 (3) | 0.62 | j21 1.01 |
| Peach | uair | [[7, 11]] | LLegJ | 1-34 (10) | 0.39 | LKneeJ 1.0 |
| Peach | uair | [[7, 11]] | j62 | 1-34 (9) | 0.47 | j63 1.0 |
| Peach | uair | [[7, 11]] | RArmJ | 4-35 (21) | 0.21 | RHandN 1.0 |
| Peach | dair | [[12, 13], [18, 19], [24, 25], [30, 31]] | j38 | 7-35 (16) | 0.49 | RLegJA 1.32 |
| Peach | dair | [[12, 13], [18, 19], [24, 25], [30, 31]] | j37 | 17-38 (18) | 1.27 | j38 1.32 |
| Peach | dair | [[12, 13], [18, 19], [24, 25], [30, 31]] | j93 | 0-40 (0) | 0.9 | j93 0.9 |
| Peach | dair | [[12, 13], [18, 19], [24, 25], [30, 31]] | j56 | 1-39 (5) | 0.53 | j57 1.04 |
| Peach | dair | [[12, 13], [18, 19], [24, 25], [30, 31]] | j20 | 1-38 (20) | 0.51 | j21 1.0 |
| Peach | dair | [[12, 13], [18, 19], [24, 25], [30, 31]] | RHandN | 1-39 (5) | 0.5 | j27 1.0 |
| Peach | dair | [[12, 13], [18, 19], [24, 25], [30, 31]] | j62 | 1-39 (25) | 0.4 | j63 1.0 |
| Peach | dair | [[12, 13], [18, 19], [24, 25], [30, 31]] | j44 | 3-38 (22) | 0.61 | j45 1.0 |
| Peach | grab | [[6, 7]] | j93 | 0-30 (0) | 0.9 | j93 0.9 |
| Peach | dash_grab | [[6, 7]] | j93 | 0-40 (0) | 0.9 | j93 0.9 |
| Peach | pummel | [[13, 15]] | j93 | 0-25 (0) | 0.9 | j93 0.9 |
| Peach | pummel | [[13, 15]] | j27 | 2-22 (8) | 0.4 | j28 1.0 |
| Peach | pummel | [[13, 15]] | j45 | 2-23 (13) | 0.35 | j46 1.0 |
| Peach | pummel | [[13, 15]] | j57 | 2-22 (8) | 0.5 | j58 1.0 |
| Peach | pummel | [[13, 15]] | ThrowN | 4-22 (13) | 0.7 | TransN2 1.0 |
| Peach | pummel | [[13, 15]] | j63 | 4-22 (13) | 0.7 | j64 1.0 |
| Peach | ledge_quick | [[10, 14]] | j93 | 0-55 (0) | 0.9 | j93 0.9 |
| Peach | ledge_quick | [[10, 14]] | j57 | 5-54 (48) | 0.35 | j58 1.0 |
| Peach | ledge_quick | [[10, 14]] | j63 | 5-54 (48) | 0.35 | j64 1.0 |
| Peach | ledge_quick | [[10, 14]] | j21 | 6-54 (48) | 0.42 | RShoulderN 1.0 |
| Peach | ledge_quick | [[10, 14]] | j27 | 6-54 (48) | 0.42 | j28 1.0 |
| Peach | ledge_quick | [[10, 14]] | LKneeJ | 6-54 (48) | 0.42 | LFootJA 1.0 |
| Peach | ledge_quick | [[10, 14]] | RLegJA | 6-54 (48) | 0.42 | RLegJ 1.0 |
| Peach | ledge_quick | [[10, 14]] | j45 | 6-54 (48) | 0.42 | j46 1.0 |
| Peach | ledge_quick | [[10, 14]] | ThrowN | 6-54 (48) | 0.42 | TransN2 1.0 |
| Peach | ledge_slow | [[44, 47]] | j93 | 0-70 (0) | 0.9 | j93 0.9 |
| Peach | ledge_slow | [[44, 47]] | j63 | 5-68 (52) | 0.44 | j64 1.0 |
| Peach | ledge_slow | [[44, 47]] | j21 | 6-68 (49) | 0.53 | RShoulderN 1.0 |
| Peach | ledge_slow | [[44, 47]] | j27 | 6-68 (49) | 0.53 | j28 1.0 |
| Peach | ledge_slow | [[44, 47]] | LKneeJ | 6-68 (49) | 0.53 | LFootJA 1.0 |
| Peach | ledge_slow | [[44, 47]] | j57 | 6-68 (49) | 0.53 | j58 1.0 |
| Peach | ledge_slow | [[44, 47]] | RLegJA | 16-66 (52) | 0.66 | RLegJ 1.0 |
| Peach | ledge_slow | [[44, 47]] | j45 | 16-66 (52) | 0.66 | j46 1.0 |
| Peach | ledge_slow | [[44, 47]] | ThrowN | 16-66 (52) | 0.66 | TransN2 1.0 |
| Peach | getup_u | [[17, 19], [25, 27]] | j93 | 0-50 (0) | 0.9 | j93 0.9 |
| Peach | getup_d | [[17, 18], [25, 26]] | j93 | 0-50 (0) | 0.9 | j93 0.9 |
| Pikachu | jab1 | [[2, 3]] | LHandNb | 0-22 (6) | 1.3 | LThumbNa 1.3 |
| Pikachu | jab1 | [[2, 3]] | j45 | 0-22 (7) | 1.3 | j46 1.3 |
| Pikachu | jab1 | [[2, 3]] | L1stNb | 1-16 (1) | 0 | L1stNb 1.14 |
| Pikachu | dash_attack | [[5, 16]] | LHandNb | 0-50 (17) | 1.3 | LThumbNa 1.68 |
| Pikachu | dash_attack | [[5, 16]] | YRotN | 9-28 (17) | 0.6 | LHandNb 1.68 |
| Pikachu | dash_attack | [[5, 16]] | j45 | 0-50 (40) | 1.33 | j46 1.57 |
| Pikachu | dash_attack | [[5, 16]] | RShoulderJA | 5-28 (17) | 0.05 | RShoulderJ 1.19 |
| Pikachu | ftilt_hi | [[5, 14]] | L2ndNb | 2-8 (5) | 1.8 | L4thNa 2.7 |
| Pikachu | ftilt_hi | [[5, 14]] | L4thNa | 2-8 (5) | 1.5 | L4thNb 2.7 |
| Pikachu | ftilt_hi | [[5, 14]] | j40 | 2-8 (5) | 1.8 | RShoulderN 2.7 |
| Pikachu | ftilt_hi | [[5, 14]] | RShoulderN | 2-8 (5) | 1.5 | j44 2.7 |
| Pikachu | ftilt_hi | [[5, 14]] | LHandNb | 0-30 (3) | 1.29 | LThumbNa 1.44 |
| Pikachu | ftilt_hi | [[5, 14]] | j45 | 0-30 (18) | 1.3 | j46 1.44 |
| Pikachu | ftilt_hi | [[5, 14]] | L1stNb | 2-25 (4) | 0.63 | L1stNb 1.0 |
| Pikachu | ftilt | [[5, 14]] | L2ndNb | 2-8 (5) | 1.6 | L4thNa 2.4 |
| Pikachu | ftilt | [[5, 14]] | L4thNa | 2-8 (5) | 1.5 | L4thNb 2.4 |
| Pikachu | ftilt | [[5, 14]] | j40 | 2-8 (5) | 1.6 | RShoulderN 2.4 |
| Pikachu | ftilt | [[5, 14]] | RShoulderN | 2-8 (5) | 1.5 | j44 2.4 |
| Pikachu | ftilt | [[5, 14]] | j45 | 0-30 (18) | 1.3 | j46 1.3 |
| Pikachu | ftilt | [[5, 14]] | LHandNb | 0-30 (3) | 1.29 | LThumbNa 1.28 |
| Pikachu | ftilt | [[5, 14]] | L1stNb | 2-25 (4) | 0.63 | L1stNb 1.0 |
| Pikachu | ftilt_lw | [[5, 14]] | L2ndNb | 2-8 (5) | 1.6 | L4thNa 2.4 |
| Pikachu | ftilt_lw | [[5, 14]] | L4thNa | 2-8 (5) | 1.5 | L4thNb 2.4 |
| Pikachu | ftilt_lw | [[5, 14]] | j40 | 2-8 (5) | 1.6 | RShoulderN 2.4 |
| Pikachu | ftilt_lw | [[5, 14]] | RShoulderN | 2-8 (5) | 1.5 | j44 2.4 |
| Pikachu | ftilt_lw | [[5, 14]] | j45 | 0-30 (18) | 1.3 | j46 1.3 |
| Pikachu | ftilt_lw | [[5, 14]] | LHandNb | 0-30 (3) | 1.29 | LThumbNa 1.28 |
| Pikachu | ftilt_lw | [[5, 14]] | L1stNb | 2-23 (4) | 0.63 | L1stNb 1.0 |
| Pikachu | utilt | [[7, 14]] | LHandNb | 0-24 (20) | 1.3 | LThumbNa 1.3 |
| Pikachu | utilt | [[7, 14]] | j45 | 0-24 (0) | 1.28 | j46 1.28 |
| Pikachu | dtilt | [[7, 9]] | RShoulderJA | 6-19 (7) | 1.6 | RShoulderJ 1.52 |
| Pikachu | dtilt | [[7, 9]] | YRotN | 7-15 (7) | 0.95 | RShoulderJA 1.52 |
| Pikachu | dtilt | [[7, 9]] | LHandNb | 0-22 (20) | 1.27 | LThumbNa 1.3 |
| Pikachu | dtilt | [[7, 9]] | j45 | 0-22 (2) | 1.3 | j46 1.3 |
| Pikachu | fsmash | [[16, 18], [19, 21], [22, 23]] | LHandNb | 0-50 (42) | 1.33 | LThumbNa 1.33 |
| Pikachu | fsmash | [[16, 18], [19, 21], [22, 23]] | j45 | 0-50 (27) | 1.3 | j46 1.3 |
| Pikachu | usmash | [[8, 10], [11, 13], [14, 17]] | LHandNb | 0-44 (3) | 1.34 | LThumbNa 1.45 |
| Pikachu | usmash | [[8, 10], [11, 13], [14, 17]] | j45 | 0-44 (1) | 1.3 | j46 1.45 |
| Pikachu | usmash | [[8, 10], [11, 13], [14, 17]] | XRotN | 22-29 (22) | 0.8 | LHandNb 1.45 |
| Pikachu | dsmash | [[7, 8], [10, 11], [13, 14], [16, 17], [19, 20], [22, 23], [25, 25]] | j45 | 0-55 (33) | 1.39 | j46 1.33 |
| Pikachu | dsmash | [[7, 8], [10, 11], [13, 14], [16, 17], [19, 20], [22, 23], [25, 25]] | XRotN | 6-34 (7) | 0.9 | j45 1.33 |
| Pikachu | dsmash | [[7, 8], [10, 11], [13, 14], [16, 17], [19, 20], [22, 23], [25, 25]] | j40 | 6-37 (7) | 0.8 | j45 1.33 |
| Pikachu | dsmash | [[7, 8], [10, 11], [13, 14], [16, 17], [19, 20], [22, 23], [25, 25]] | LHandNb | 0-55 (53) | 1.29 | LThumbNa 1.29 |
| Pikachu | dsmash | [[7, 8], [10, 11], [13, 14], [16, 17], [19, 20], [22, 23], [25, 25]] | RShoulderN | 6-36 (7) | 1.2 | j44 1.0 |
| Pikachu | nair | [[3, 10], [11, 28]] | LHandNb | 0-40 (12) | 1.39 | LThumbNa 1.39 |
| Pikachu | nair | [[3, 10], [11, 28]] | j45 | 0-40 (26) | 1.3 | j46 1.3 |
| Pikachu | fair | [[10, 12], [14, 16], [18, 20], [22, 24]] | j45 | 0-40 (3) | 1.31 | j46 1.31 |
| Pikachu | fair | [[10, 12], [14, 16], [18, 20], [22, 24]] | YRotN | 7-12 (10) | 0.8 | j45 1.31 |
| Pikachu | fair | [[10, 12], [14, 16], [18, 20], [22, 24]] | LHandNb | 0-40 (2) | 1.3 | LThumbNa 1.3 |
| Pikachu | fair | [[10, 12], [14, 16], [18, 20], [22, 24]] | RShoulderJA | 32-39 (34) | 0.55 | RShoulderJ 1.0 |
| Pikachu | bair | [[4, 7], [8, 37]] | j45 | 0-60 (0) | 1.28 | j46 1.28 |
| Pikachu | bair | [[4, 7], [8, 37]] | YRotN | 2-33 (5) | 0.9 | j45 1.28 |
| Pikachu | bair | [[4, 7], [8, 37]] | LHandNb | 0-60 (1) | 1.22 | LThumbNa 1.22 |
| Pikachu | uair | [[3, 4], [5, 6], [7, 8]] | RShoulderJA | 1-18 (4) | 1.4 | RShoulderJ 1.4 |
| Pikachu | uair | [[3, 4], [5, 6], [7, 8]] | j45 | 0-28 (0) | 1.28 | j46 1.28 |
| Pikachu | uair | [[3, 4], [5, 6], [7, 8]] | LHandNb | 0-28 (0) | 1.2 | LThumbNa 1.2 |
| Pikachu | dair | [[14, 26]] | YRotN | 6-17 (14) | 1.4 | HipN 1.4 |
| Pikachu | dair | [[14, 26]] | LHandNb | 0-58 (38) | 1.3 | LThumbNa 1.3 |
| Pikachu | dair | [[14, 26]] | j45 | 0-58 (37) | 1.28 | j46 1.28 |
| Pikachu | dair | [[14, 26]] | RShoulderJA | 7-49 (13) | 0.8 | RShoulderJ 1.19 |
| Pikachu | grab | [[6, 7]] | j45 | 0-30 (13) | 1.3 | j46 1.3 |
| Pikachu | grab | [[6, 7]] | LHandNb | 0-30 (22) | 1.29 | LThumbNa 1.29 |
| Pikachu | dash_grab | [[10, 11]] | LHandNb | 0-40 (22) | 1.3 | LThumbNa 1.3 |
| Pikachu | dash_grab | [[10, 11]] | j45 | 0-40 (39) | 1.28 | j46 1.28 |
| Pikachu | pummel | [[2, 2]] | RShoulderJA | 3-21 (12) | 1.59 | RShoulderJ 1.59 |
| Pikachu | pummel | [[2, 2]] | j45 | 0-24 (17) | 1.32 | j46 1.32 |
| Pikachu | pummel | [[2, 2]] | LHandNb | 0-24 (22) | 1.17 | LThumbNa 1.17 |
| Pikachu | ledge_quick | [[22, 24]] | j40 | 22-36 (23) | 1.65 | RShoulderN 2.14 |
| Pikachu | ledge_quick | [[22, 24]] | RShoulderN | 22-25 (23) | 1.3 | j44 2.14 |
| Pikachu | ledge_quick | [[22, 24]] | j45 | 0-54 (46) | 1.27 | j46 1.32 |
| Pikachu | ledge_quick | [[22, 24]] | LHandNb | 0-54 (24) | 1.28 | LThumbNa 1.28 |
| Pikachu | ledge_slow | [[54, 59]] | RShoulderJA | 54-59 (55) | 1.7 | RShoulderJ 1.7 |
| Pikachu | ledge_slow | [[54, 59]] | LHandNb | 0-70 (35) | 1.3 | LThumbNa 1.3 |
| Pikachu | ledge_slow | [[54, 59]] | j45 | 0-70 (70) | 1.26 | j46 1.26 |
| Pikachu | getup_u | [[13, 14], [18, 19]] | L2ndNb | 12-19 (13) | 1.3 | L4thNa 1.56 |
| Pikachu | getup_u | [[13, 14], [18, 19]] | L4thNa | 12-19 (13) | 1.2 | L4thNb 1.56 |
| Pikachu | getup_u | [[13, 14], [18, 19]] | j40 | 12-19 (13) | 1.3 | RShoulderN 1.56 |
| Pikachu | getup_u | [[13, 14], [18, 19]] | RShoulderN | 12-19 (13) | 1.2 | j44 1.56 |
| Pikachu | getup_u | [[13, 14], [18, 19]] | j45 | 0-50 (6) | 1.3 | j46 1.3 |
| Pikachu | getup_u | [[13, 14], [18, 19]] | LHandNb | 0-50 (50) | 1.27 | LThumbNa 1.27 |
| Pikachu | getup_d | [[17, 18], [23, 24]] | LHandNb | 0-51 (18) | 1.31 | LThumbNa 1.31 |
| Pikachu | getup_d | [[17, 18], [23, 24]] | j45 | 0-51 (12) | 1.3 | j46 1.3 |
| Popo | jab1 | [[4, 7]] | j21 | 3-27 (12) | 0.77 | j21 1.0 |
| Popo | jab2 | [[4, 6]] | j21 | 0-3 (1) | 0.87 | j21 1.0 |
| Popo | ftilt_hi | [[6, 9]] | j21 | 6-30 (15) | 0.78 | j21 1.0 |
| Popo | ftilt | [[6, 9]] | j21 | 6-30 (15) | 0.78 | j21 1.0 |
| Popo | ftilt_lw | [[6, 9]] | j21 | 6-30 (15) | 0.78 | j21 1.0 |
| Popo | fsmash | [[13, 14]] | BustN | 1-47 (14) | 1.37 | LShoulderN 1.37 |
| Popo | fsmash | [[13, 14]] | LFootJA | 1-13 (13) | 1.3 | LFootJ 1.3 |
| Popo | fsmash | [[13, 14]] | RKneeJ | 1-13 (13) | 0.78 | RFootJA 1.01 |
| Popo | nair | [[6, 23]] | LShoulderN | 0-50 (0) | 1.1 | LShoulderJA 1.1 |
| Popo | fair | [[19, 22]] | LShoulderN | 0-60 (0) | 1.1 | LShoulderJA 1.43 |
| Popo | fair | [[19, 22]] | BustN | 1-20 (1) | 1.3 | LShoulderN 1.43 |
| Popo | fair | [[19, 22]] | LFootJA | 1-20 (1) | 1.3 | LFootJ 1.3 |
| Popo | fair | [[19, 22]] | RKneeJ | 1-20 (1) | 0.75 | RFootJA 1.03 |
| Popo | bair | [[8, 11]] | LShoulderN | 0-40 (0) | 1.1 | LShoulderJA 1.1 |
| Popo | uair | [[6, 9], [10, 23]] | LShoulderN | 0-40 (0) | 1.1 | LShoulderJA 1.1 |
| Popo | dair | [[3, 52]] | LShoulderN | 0-66 (0) | 1.1 | LShoulderJA 1.44 |
| Popo | dair | [[3, 52]] | BustN | 10-63 (57) | 1.31 | LShoulderN 1.44 |
| Popo | ledge_slow | [[39, 42]] | LFootJ | 40-43 (40) | 1.3 | j10 1.3 |
| Popo | getup_d | [[19, 20], [25, 26]] | LShoulderN | 0-37 (13) | 1.11 | LShoulderJA 1.11 |
| Popo | getup_d | [[19, 20], [25, 26]] | LFootJ | 19-37 (22) | 1.11 | j10 1.11 |
| Popo | getup_d | [[19, 20], [25, 26]] | RKneeJ | 13-34 (22) | 0.91 | RFootJA 1.01 |
| Puff | jab1 | [[5, 6]] | LShoulderJ | 2-12 (5) | 2.3 | LArmJ 2.3 |
| Puff | jab1 | [[5, 6]] | j6 | 5-15 (5) | 0.88 | j7 1.01 |
| Puff | jab2 | [[5, 6]] | RShoulderJ | 1-15 (5) | 2.6 | RArmJ 2.6 |
| Puff | jab2 | [[5, 6]] | LShoulderJ | 0-17 (8) | 1.31 | LArmJ 1.31 |
| Puff | jab2 | [[5, 6]] | j6 | 3-17 (5) | 0.88 | j7 1.0 |
| Puff | dash_attack | [[4, 8], [9, 14]] | j6 | 0-39 (20) | 0.8 | j7 1.15 |
| Puff | ftilt_hi | [[6, 9]] | LFootJ | 2-23 (7) | 2.3 | j41 2.3 |
| Puff | ftilt_hi | [[6, 9]] | WaistN | 21-23 (22) | 0.85 | LShoulderN 1.02 |
| Puff | ftilt_hi | [[6, 9]] | j6 | 6-15 (7) | 0.93 | j7 1.01 |
| Puff | ftilt | [[6, 9]] | LFootJ | 2-23 (7) | 2.3 | j41 2.3 |
| Puff | ftilt | [[6, 9]] | WaistN | 21-23 (22) | 0.85 | LShoulderN 1.02 |
| Puff | ftilt | [[6, 9]] | j6 | 6-15 (7) | 0.93 | j7 1.01 |
| Puff | ftilt_lw | [[6, 9]] | LFootJ | 2-23 (7) | 2.3 | j41 2.3 |
| Puff | ftilt_lw | [[6, 9]] | WaistN | 21-23 (22) | 0.85 | LShoulderN 1.02 |
| Puff | ftilt_lw | [[6, 9]] | j6 | 6-15 (7) | 0.93 | j7 1.01 |
| Puff | utilt | [[8, 9], [10, 14]] | RFootJ | 9-20 (10) | 2.2 | j47 2.21 |
| Puff | utilt | [[8, 9], [10, 14]] | HipN | 19-23 (23) | 0.9 | RFootJ 2.21 |
| Puff | utilt | [[8, 9], [10, 14]] | j6 | 10-19 (14) | 1.1 | j7 1.1 |
| Puff | dtilt | [[10, 12]] | LFootJ | 9-18 (11) | 3.2 | j41 3.2 |
| Puff | dtilt | [[10, 12]] | WaistN | 0-40 (0) | 0.5 | j6 0.79 |
| Puff | fsmash | [[12, 15], [16, 20]] | LFootJ | 7-29 (16) | 1.91 | j41 1.91 |
| Puff | fsmash | [[12, 15], [16, 20]] | RFootJ | 9-28 (16) | 1.46 | j47 1.46 |
| Puff | fsmash | [[12, 15], [16, 20]] | j6 | 2-41 (36) | 0.59 | j7 1.02 |
| Puff | usmash | [[7, 10]] | j6 | 1-28 (8) | 1.4 | j7 1.4 |
| Puff | dsmash | [[9, 10]] | LLegJ | 9-11 (9) | 1.1 | LFootJ 2.78 |
| Puff | dsmash | [[9, 10]] | LKneeJ | 9-11 (9) | 1.1 | LFootJ 2.78 |
| Puff | dsmash | [[9, 10]] | LFootJ | 9-12 (9) | 2.3 | j41 2.78 |
| Puff | dsmash | [[9, 10]] | RLegJ | 9-11 (9) | 1.1 | RFootJ 2.78 |
| Puff | dsmash | [[9, 10]] | RKneeJ | 9-11 (9) | 1.1 | RFootJ 2.78 |
| Puff | dsmash | [[9, 10]] | RFootJ | 9-12 (9) | 2.3 | j47 2.78 |
| Puff | dsmash | [[9, 10]] | j6 | 1-33 (11) | 0.65 | j7 1.23 |
| Puff | nair | [[6, 7], [8, 28]] | LFootJ | 6-30 (6) | 2.5 | j41 2.5 |
| Puff | nair | [[6, 7], [8, 28]] | WaistN | 5-33 (11) | 0.8 | j6 1.0 |
| Puff | fair | [[7, 8], [9, 22]] | YRotN | 1-7 (4) | 0.65 | LFootJ 3.15 |
| Puff | fair | [[7, 8], [9, 22]] | LFootJ | 3-33 (11) | 3.05 | j41 3.15 |
| Puff | fair | [[7, 8], [9, 22]] | RFootJ | 3-33 (11) | 3.05 | j47 3.15 |
| Puff | fair | [[7, 8], [9, 22]] | WaistN | 7-21 (10) | 0.89 | j6 1.0 |
| Puff | bair | [[9, 12]] | RFootJ | 9-28 (10) | 3 | j47 3.0 |
| Puff | bair | [[9, 12]] | WaistN | 8-15 (11) | 0.84 | j6 1.02 |
| Puff | uair | [[9, 12]] | WaistN | 1-16 (6) | 0.76 | LShoulderJ 2.29 |
| Puff | uair | [[9, 12]] | LShoulderJ | 1-31 (10) | 2.2 | LArmJ 2.29 |
| Puff | dair | [[5, 6], [8, 9], [11, 12], [14, 15], [17, 18], [20, 21], [23, 24], [26, 27]] | HipN | 1-23 (2) | 0.53 | LFootJ 1.63 |
| Puff | dair | [[5, 6], [8, 9], [11, 12], [14, 15], [17, 18], [20, 21], [23, 24], [26, 27]] | LFootJ | 4-48 (21) | 1.37 | j41 1.63 |
| Puff | dair | [[5, 6], [8, 9], [11, 12], [14, 15], [17, 18], [20, 21], [23, 24], [26, 27]] | RFootJ | 4-48 (21) | 1.37 | j47 1.63 |
| Puff | grab | [[6, 7]] | WaistN | 1-11 (9) | 1.1 | LShoulderJ 1.61 |
| Puff | grab | [[6, 7]] | LShoulderJ | 2-20 (6) | 1.5 | LArmJ 1.61 |
| Puff | dash_grab | [[10, 11]] | LShoulderJ | 3-33 (10) | 1.4 | LArmJ 1.52 |
| Puff | dash_grab | [[10, 11]] | WaistN | 12-37 (17) | 1.12 | LShoulderJ 1.52 |
| Puff | dash_grab | [[10, 11]] | j6 | 0-0 (0) | 0.95 | j7 1.12 |
| Puff | pummel | [[10, 11]] | WaistN | 1-24 (2) | 0.88 | RShoulderJA 1.61 |
| Puff | pummel | [[10, 11]] | RShoulderJA | 9-16 (9) | 1.53 | RShoulderJ 1.61 |
| Puff | pummel | [[10, 11]] | LShoulderJ | 0-30 (0) | 1.4 | LArmJ 1.47 |
| Puff | pummel | [[10, 11]] | j7 | 6-17 (10) | 1.3 | j8 1.36 |
| Puff | pummel | [[10, 11]] | j6 | 19-27 (23) | 1.12 | j7 1.36 |
| Puff | ledge_quick | [[19, 23]] | LFootJ | 13-39 (22) | 3 | j41 3.0 |
| Puff | ledge_quick | [[19, 23]] | YRotN | 26-33 (26) | 0.67 | LFootJ 3.0 |
| Puff | ledge_quick | [[19, 23]] | WaistN | 42-55 (42) | 1.21 | j6 1.21 |
| Puff | ledge_slow | [[43, 59]] | YRotN | 27-69 (29) | 1.29 | LFootJ 1.5 |
| Puff | ledge_slow | [[43, 59]] | LFootJ | 42-60 (47) | 2 | j41 1.5 |
| Puff | ledge_slow | [[43, 59]] | RFootJ | 42-60 (47) | 2 | j47 1.5 |
| Puff | ledge_slow | [[43, 59]] | LLegJ | 52-61 (58) | 1.12 | LFootJ 1.5 |
| Puff | ledge_slow | [[43, 59]] | RLegJ | 52-61 (58) | 1.12 | RFootJ 1.5 |
| Puff | ledge_slow | [[43, 59]] | WaistN | 65-69 (68) | 0.8 | j6 1.29 |
| Puff | getup_u | [[19, 20], [24, 25]] | YRotN | 0-48 (10) | 0.75 | RFootJ 1.56 |
| Puff | getup_u | [[19, 20], [24, 25]] | RFootJ | 17-28 (22) | 1.56 | j47 1.56 |
| Puff | getup_d | [[20, 21], [24, 26]] | YRotN | 0-48 (12) | 0.54 | LFootJ 2.5 |
| Puff | getup_d | [[20, 21], [24, 26]] | LFootJ | 3-32 (20) | 2.5 | j41 2.5 |
| Samus | ledge_quick | [[24, 27]] | RLegJ | 25-29 (25) | 1.2 | RKneeJ 1.2 |
| Yoshi | jab1 | [[3, 5]] | LShoulderN | 3-4 (3) | 1.6 | LShoulderJA 2.08 |
| Yoshi | jab1 | [[3, 5]] | LShoulderJA | 3-4 (3) | 1.3 | LShoulderJ 2.08 |
| Yoshi | jab2 | [[3, 5]] | L2ndNa | 3-6 (3) | 1.6 | L2ndNb 1.92 |
| Yoshi | jab2 | [[3, 5]] | L2ndNb | 3-4 (3) | 1.2 | L3rdNa 1.92 |
| Yoshi | jab2 | [[3, 5]] | R4thNb | 1-19 (6) | 0.1 | R4thNb 1.0 |
| Yoshi | ftilt_hi | [[6, 8]] | L2ndNa | 6-10 (6) | 1.6 | L2ndNb 2.72 |
| Yoshi | ftilt_hi | [[6, 8]] | L2ndNb | 6-10 (6) | 1.7 | L3rdNa 2.72 |
| Yoshi | ftilt_hi | [[6, 8]] | L3rdNb | 6-9 (6) | 0.8 | L4thNa 2.18 |
| Yoshi | ftilt | [[6, 8]] | L2ndNa | 6-10 (6) | 1.6 | L2ndNb 2.72 |
| Yoshi | ftilt | [[6, 8]] | L2ndNb | 6-10 (6) | 1.7 | L3rdNa 2.72 |
| Yoshi | ftilt | [[6, 8]] | L3rdNb | 6-9 (6) | 0.8 | L4thNa 2.18 |
| Yoshi | ftilt_lw | [[6, 8]] | L2ndNa | 6-10 (6) | 1.6 | L2ndNb 2.72 |
| Yoshi | ftilt_lw | [[6, 8]] | L2ndNb | 6-10 (6) | 1.7 | L3rdNa 2.72 |
| Yoshi | ftilt_lw | [[6, 8]] | L3rdNb | 6-9 (6) | 0.8 | L4thNa 2.18 |
| Yoshi | utilt | [[8, 12]] | LThumbNa | 6-13 (10) | 1.7 | j21 3.54 |
| Yoshi | utilt | [[8, 12]] | LThumbNb | 6-16 (8) | 1.6 | j21 3.54 |
| Yoshi | utilt | [[8, 12]] | j21 | 6-16 (8) | 1.3 | j21 3.54 |
| Yoshi | dtilt | [[8, 10]] | LThumbNa | 6-10 (7) | 1.64 | j21 4.37 |
| Yoshi | dtilt | [[8, 10]] | LThumbNb | 6-20 (8) | 2.1 | j21 4.37 |
| Yoshi | dtilt | [[8, 10]] | j21 | 6-10 (8) | 1.3 | j21 4.37 |
| Yoshi | fsmash_hi | [[14, 16]] | R2ndNb | 14-24 (14) | 1.8 | R3rdNa 1.44 |
| Yoshi | fsmash_hi | [[14, 16]] | R3rdNa | 14-22 (17) | 0.76 | R3rdNb 1.44 |
| Yoshi | fsmash | [[14, 16]] | R2ndNb | 14-24 (14) | 1.7 | R3rdNa 1.36 |
| Yoshi | fsmash | [[14, 16]] | R3rdNa | 14-22 (17) | 0.76 | R3rdNb 1.36 |
| Yoshi | fsmash_lw | [[14, 16]] | R2ndNb | 14-24 (14) | 1.7 | R3rdNa 1.36 |
| Yoshi | fsmash_lw | [[14, 16]] | R3rdNa | 14-22 (17) | 0.76 | R3rdNb 1.36 |
| Yoshi | usmash | [[11, 15]] | R2ndNb | 13-18 (14) | 1.3 | R3rdNa 1.3 |
| Yoshi | usmash | [[11, 15]] | R3rdNa | 15-36 (15) | 0.8 | R3rdNb 1.3 |
| Yoshi | dsmash | [[6, 8], [21, 22]] | LThumbNa | 4-24 (6) | 1.1 | j21 5.28 |
| Yoshi | dsmash | [[6, 8], [21, 22]] | LThumbNb | 5-24 (6) | 3.2 | j21 5.28 |
| Yoshi | dsmash | [[6, 8], [21, 22]] | j21 | 5-24 (6) | 1.5 | j21 5.28 |
| Yoshi | nair | [[3, 6], [7, 33]] | L2ndNb | 2-31 (3) | 1.25 | L3rdNb 1.16 |
| Yoshi | nair | [[3, 6], [7, 33]] | L2ndNa | 3-33 (3) | 0.85 | L3rdNb 1.16 |
| Yoshi | fair | [[19, 21]] | R3rdNa | 19-19 (19) | 1.3 | R3rdNb 1.3 |
| Yoshi | bair | [[10, 12], [16, 18], [23, 25], [28, 30]] | LThumbNa | 8-38 (13) | 1.5 | j21 3.12 |
| Yoshi | bair | [[10, 12], [16, 18], [23, 25], [28, 30]] | LThumbNb | 8-39 (13) | 1.6 | j21 3.12 |
| Yoshi | bair | [[10, 12], [16, 18], [23, 25], [28, 30]] | j21 | 9-38 (13) | 1.3 | j21 3.12 |
| Yoshi | uair | [[5, 6]] | LThumbNa | 3-7 (5) | 1.4 | j21 3.53 |
| Yoshi | uair | [[5, 6]] | LThumbNb | 3-17 (5) | 1.8 | j21 3.53 |
| Yoshi | uair | [[5, 6]] | j21 | 3-7 (5) | 1.4 | j21 3.53 |
| Yoshi | uair | [[5, 6]] | R3rdNa | 10-19 (14) | 0.8 | R3rdNb 1.01 |
| Yoshi | dair | [[18, 18], [20, 20], [22, 22], [24, 24], [26, 26], [28, 28], [30, 30], [32, 32], [34, 34], [36, 36], [38, 38], [40, 40], [42, 42], [44, 44], [46, 45]] | LShoulderN | 14-52 (16) | 1.25 | LShoulderJA 1.25 |
| Yoshi | dair | [[18, 18], [20, 20], [22, 22], [24, 24], [26, 26], [28, 28], [30, 30], [32, 32], [34, 34], [36, 36], [38, 38], [40, 40], [42, 42], [44, 44], [46, 45]] | L2ndNa | 14-52 (16) | 1.25 | L2ndNb 1.25 |
| Yoshi | grab | [[17, 22], [17, 18]] | R4thNb | 14-46 (28) | 22.87 | R4thNb 22.87 |
| Yoshi | grab | [[17, 22], [17, 18]] | R3rdNa | 49-50 (49) | 0.6 | R4thNb 22.87 |
| Yoshi | dash_grab | [[10, 15]] | R4thNb | 7-35 (19) | 23.2 | R4thNb 23.2 |
| Yoshi | dash_grab | [[10, 15]] | R3rdNa | 38-39 (38) | 0.6 | R4thNb 23.2 |
| Yoshi | pummel | [[9, 9]] | R3rdNa | 0-24 (14) | 1.4 | R3rdNb 2.21 |
| Yoshi | pummel | [[9, 9]] | R3rdNb | 0-24 (8) | 1.7 | R3rdNb 2.21 |
| Yoshi | pummel | [[9, 9]] | R4thNa | 0-24 (0) | 1.5 | R4thNb 2.1 |
| Yoshi | pummel | [[9, 9]] | RHandNb | 0-24 (0) | 1.5 | RHandNb 2.1 |
| Yoshi | ledge_quick | [[19, 23]] | LThumbNa | 17-33 (21) | 2.89 | j21 8.57 |
| Yoshi | ledge_quick | [[19, 23]] | LThumbNb | 17-31 (21) | 1.6 | j21 8.57 |
| Yoshi | ledge_quick | [[19, 23]] | j21 | 17-31 (21) | 1.86 | j21 8.57 |
| Yoshi | ledge_slow | [[33, 37]] | R2ndNb | 33-39 (35) | 1.44 | R3rdNa 3.26 |
| Yoshi | ledge_slow | [[33, 37]] | R3rdNa | 33-39 (35) | 2.26 | R3rdNb 3.26 |
| Yoshi | getup_u | [[13, 14], [19, 20]] | L2ndNa | 13-17 (15) | 1.81 | L2ndNb 1.81 |
| Yoshi | getup_u | [[13, 14], [19, 20]] | LShoulderN | 19-22 (21) | 1.75 | LShoulderJA 1.75 |
| Yoshi | getup_d | [[14, 15], [25, 26]] | R2ndNb | 14-26 (14) | 1.45 | R3rdNa 2.21 |
| Yoshi | getup_d | [[14, 15], [25, 26]] | R3rdNa | 14-27 (14) | 1.5 | R3rdNb 2.21 |
| Zelda | jab1 | [[11, 11], [13, 13], [15, 15]] | j94 | 0-30 (0) | 0.9 | j94 0.9 |
| Zelda | jab1 | [[11, 11], [13, 13], [15, 15]] | LShoulderJA | 0-30 (0) | 0.95 | LShoulderJ 0.95 |
| Zelda | jab1 | [[11, 11], [13, 13], [15, 15]] | j45 | 0-30 (0) | 0.95 | j46 0.95 |
| Zelda | jab1 | [[11, 11], [13, 13], [15, 15]] | j57 | 0-30 (0) | 0.95 | j58 0.95 |
| Zelda | dash_attack | [[6, 8], [9, 13]] | j94 | 0-38 (0) | 0.9 | j94 0.9 |
| Zelda | dash_attack | [[6, 8], [9, 13]] | j26 | 0-31 (0) | 0.68 | LShoulderJA 0.95 |
| Zelda | dash_attack | [[6, 8], [9, 13]] | LShoulderJA | 0-38 (0) | 0.95 | LShoulderJ 0.95 |
| Zelda | dash_attack | [[6, 8], [9, 13]] | j45 | 0-38 (0) | 0.76 | j46 0.95 |
| Zelda | dash_attack | [[6, 8], [9, 13]] | j56 | 0-24 (0) | 0.86 | j57 0.95 |
| Zelda | dash_attack | [[6, 8], [9, 13]] | j57 | 0-38 (0) | 0.95 | j58 0.95 |
| Zelda | dash_attack | [[6, 8], [9, 13]] | j20 | 0-32 (0) | 0.65 | WaistB 1.0 |
| Zelda | dash_attack | [[6, 8], [9, 13]] | L1stNa | 0-25 (0) | 0.85 | L1stNb 1.0 |
| Zelda | dash_attack | [[6, 8], [9, 13]] | L4thNb | 0-27 (0) | 0.82 | LHandNb 1.0 |
| Zelda | dash_attack | [[6, 8], [9, 13]] | j51 | 0-26 (0) | 0.84 | j52 1.0 |
| Zelda | dash_attack | [[6, 8], [9, 13]] | j62 | 0-32 (0) | 0.64 | j63 1.0 |
| Zelda | ftilt_hi | [[12, 14]] | j94 | 0-38 (0) | 0.9 | j94 0.9 |
| Zelda | ftilt_hi | [[12, 14]] | j51 | 3-32 (17) | 0.72 | j52 1.03 |
| Zelda | ftilt_hi | [[12, 14]] | j63 | 3-32 (6) | 0.76 | j64 1.03 |
| Zelda | ftilt_hi | [[12, 14]] | j62 | 16-33 (27) | 0.77 | j63 1.03 |
| Zelda | ftilt_hi | [[12, 14]] | j50 | 19-33 (27) | 0.77 | j51 1.03 |
| Zelda | ftilt_hi | [[12, 14]] | j45 | 0-38 (15) | 0.55 | j46 1.01 |
| Zelda | ftilt_hi | [[12, 14]] | j57 | 0-38 (12) | 0.81 | j58 1.01 |
| Zelda | ftilt_hi | [[12, 14]] | L1stNb | 3-32 (6) | 0.76 | L2ndNa 1.01 |
| Zelda | ftilt_hi | [[12, 14]] | WaistB | 4-33 (28) | 0.81 | BustN 1.01 |
| Zelda | ftilt_hi | [[12, 14]] | L4thNb | 4-33 (16) | 0.66 | LHandNb 1.01 |
| Zelda | ftilt_hi | [[12, 14]] | j56 | 16-33 (27) | 0.77 | j57 1.01 |
| Zelda | ftilt_hi | [[12, 14]] | L4thNa | 19-33 (27) | 0.62 | L4thNb 1.01 |
| Zelda | ftilt_hi | [[12, 14]] | j44 | 19-33 (27) | 0.77 | j45 1.01 |
| Zelda | ftilt_hi | [[12, 14]] | LShoulderJA | 0-38 (27) | 0.89 | LShoulderJ 1.0 |
| Zelda | ftilt | [[12, 14]] | j94 | 0-38 (0) | 0.9 | j94 0.9 |
| Zelda | ftilt | [[12, 14]] | j51 | 3-33 (17) | 0.7 | j52 1.03 |
| Zelda | ftilt | [[12, 14]] | j63 | 3-32 (6) | 0.76 | j64 1.03 |
| Zelda | ftilt | [[12, 14]] | j62 | 16-33 (27) | 0.77 | j63 1.03 |
| Zelda | ftilt | [[12, 14]] | j50 | 19-33 (27) | 0.77 | j51 1.03 |
| Zelda | ftilt | [[12, 14]] | L4thNb | 4-32 (16) | 0.64 | LHandNb 1.02 |
| Zelda | ftilt | [[12, 14]] | L4thNa | 19-33 (27) | 0.62 | L4thNb 1.02 |
| Zelda | ftilt | [[12, 14]] | j45 | 0-38 (15) | 0.52 | j46 1.01 |
| Zelda | ftilt | [[12, 14]] | j57 | 0-38 (12) | 0.81 | j58 1.01 |
| Zelda | ftilt | [[12, 14]] | L1stNb | 3-32 (6) | 0.76 | L2ndNa 1.01 |
| Zelda | ftilt | [[12, 14]] | WaistB | 4-33 (28) | 0.81 | BustN 1.01 |
| Zelda | ftilt | [[12, 14]] | j56 | 16-33 (27) | 0.77 | j57 1.01 |
| Zelda | ftilt | [[12, 14]] | j44 | 19-33 (27) | 0.77 | j45 1.01 |
| Zelda | ftilt | [[12, 14]] | LShoulderJA | 0-38 (27) | 0.89 | LShoulderJ 1.0 |
| Zelda | ftilt_lw | [[12, 14]] | j94 | 0-38 (0) | 0.9 | j94 0.9 |
| Zelda | ftilt_lw | [[12, 14]] | j51 | 3-33 (17) | 0.69 | j52 1.03 |
| Zelda | ftilt_lw | [[12, 14]] | j63 | 3-32 (6) | 0.76 | j64 1.03 |
| Zelda | ftilt_lw | [[12, 14]] | j62 | 16-33 (27) | 0.77 | j63 1.03 |
| Zelda | ftilt_lw | [[12, 14]] | j50 | 19-33 (27) | 0.77 | j51 1.03 |
| Zelda | ftilt_lw | [[12, 14]] | L4thNb | 4-32 (16) | 0.63 | LHandNb 1.02 |
| Zelda | ftilt_lw | [[12, 14]] | L4thNa | 19-33 (27) | 0.62 | L4thNb 1.02 |
| Zelda | ftilt_lw | [[12, 14]] | j45 | 0-38 (15) | 0.53 | j46 1.01 |
| Zelda | ftilt_lw | [[12, 14]] | j57 | 0-38 (12) | 0.81 | j58 1.01 |
| Zelda | ftilt_lw | [[12, 14]] | L1stNb | 3-32 (6) | 0.76 | L2ndNa 1.01 |
| Zelda | ftilt_lw | [[12, 14]] | WaistB | 4-33 (28) | 0.81 | BustN 1.01 |
| Zelda | ftilt_lw | [[12, 14]] | j56 | 16-33 (27) | 0.77 | j57 1.01 |
| Zelda | ftilt_lw | [[12, 14]] | j44 | 19-33 (27) | 0.77 | j45 1.01 |
| Zelda | ftilt_lw | [[12, 14]] | LShoulderJA | 0-38 (27) | 0.89 | LShoulderJ 1.0 |
| Zelda | utilt | [[10, 24]] | j94 | 0-44 (0) | 0.9 | j94 0.9 |
| Zelda | utilt | [[10, 24]] | LShoulderJA | 0-44 (14) | 0.68 | LShoulderJ 0.95 |
| Zelda | utilt | [[10, 24]] | j45 | 0-44 (37) | 0.81 | j46 0.95 |
| Zelda | utilt | [[10, 24]] | j57 | 0-44 (37) | 0.69 | j58 0.95 |
| Zelda | utilt | [[10, 24]] | j63 | 2-35 (5) | 0.81 | j64 1.01 |
| Zelda | utilt | [[10, 24]] | j51 | 1-41 (6) | 0.72 | j52 1.0 |
| Zelda | utilt | [[10, 24]] | WaistB | 2-42 (29) | 0.74 | BustN 1.0 |
| Zelda | utilt | [[10, 24]] | L1stNb | 2-41 (5) | 0.77 | L2ndNa 1.0 |
| Zelda | utilt | [[10, 24]] | L4thNb | 2-41 (6) | 0.75 | LHandNb 1.0 |
| Zelda | dtilt | [[5, 7]] | L4thNb | 0-32 (0) | 0.51 | LHandNb 0.51 |
| Zelda | dtilt | [[5, 7]] | j51 | 0-32 (0) | 0.68 | j52 0.68 |
| Zelda | dtilt | [[5, 7]] | j45 | 0-32 (0) | 0.77 | j46 0.77 |
| Zelda | dtilt | [[5, 7]] | j94 | 0-32 (0) | 0.9 | j94 0.9 |
| Zelda | dtilt | [[5, 7]] | j63 | 0-32 (8) | 0.69 | j64 0.92 |
| Zelda | dtilt | [[5, 7]] | L1stNb | 1-22 (8) | 0.32 | L2ndNa 1.02 |
| Zelda | dtilt | [[5, 7]] | j58 | 1-22 (7) | 0.47 | NeckN 1.01 |
| Zelda | fsmash | [[16, 16], [18, 18], [20, 20], [22, 22], [24, 24]] | WaistB | 3-39 (37) | 1.16 | BustN 1.16 |
| Zelda | fsmash | [[16, 16], [18, 18], [20, 20], [22, 22], [24, 24]] | L1stNb | 3-39 (37) | 1.16 | L2ndNa 1.16 |
| Zelda | fsmash | [[16, 16], [18, 18], [20, 20], [22, 22], [24, 24]] | L4thNb | 3-38 (25) | 0.61 | LHandNb 1.12 |
| Zelda | fsmash | [[16, 16], [18, 18], [20, 20], [22, 22], [24, 24]] | LShoulderJA | 1-38 (25) | 0.68 | LShoulderJ 1.1 |
| Zelda | fsmash | [[16, 16], [18, 18], [20, 20], [22, 22], [24, 24]] | j51 | 2-38 (30) | 0.69 | j52 1.1 |
| Zelda | fsmash | [[16, 16], [18, 18], [20, 20], [22, 22], [24, 24]] | j63 | 2-38 (10) | 0.73 | j64 1.1 |
| Zelda | fsmash | [[16, 16], [18, 18], [20, 20], [22, 22], [24, 24]] | j94 | 0-40 (0) | 0.9 | j94 0.9 |
| Zelda | fsmash | [[16, 16], [18, 18], [20, 20], [22, 22], [24, 24]] | j45 | 1-38 (25) | 0.58 | j46 1.06 |
| Zelda | fsmash | [[16, 16], [18, 18], [20, 20], [22, 22], [24, 24]] | j57 | 1-38 (25) | 0.58 | j58 1.06 |
| Zelda | usmash | [[5, 5], [7, 7], [9, 9], [11, 11], [13, 13], [15, 15], [24, 24], [26, 26], [28, 28], [30, 30], [32, 32], [34, 34]] | j94 | 0-57 (0) | 0.9 | j94 0.9 |
| Zelda | usmash | [[5, 5], [7, 7], [9, 9], [11, 11], [13, 13], [15, 15], [24, 24], [26, 26], [28, 28], [30, 30], [32, 32], [34, 34]] | LShoulderJA | 0-57 (31) | 0.79 | LShoulderJ 0.95 |
| Zelda | usmash | [[5, 5], [7, 7], [9, 9], [11, 11], [13, 13], [15, 15], [24, 24], [26, 26], [28, 28], [30, 30], [32, 32], [34, 34]] | j45 | 0-57 (9) | 0.57 | j46 0.95 |
| Zelda | usmash | [[5, 5], [7, 7], [9, 9], [11, 11], [13, 13], [15, 15], [24, 24], [26, 26], [28, 28], [30, 30], [32, 32], [34, 34]] | j57 | 0-57 (22) | 0.71 | j58 0.95 |
| Zelda | usmash | [[5, 5], [7, 7], [9, 9], [11, 11], [13, 13], [15, 15], [24, 24], [26, 26], [28, 28], [30, 30], [32, 32], [34, 34]] | L4thNb | 1-54 (8) | 0.63 | LHandNb 1.0 |
| Zelda | usmash | [[5, 5], [7, 7], [9, 9], [11, 11], [13, 13], [15, 15], [24, 24], [26, 26], [28, 28], [30, 30], [32, 32], [34, 34]] | j51 | 2-48 (11) | 0.83 | j52 1.0 |
| Zelda | usmash | [[5, 5], [7, 7], [9, 9], [11, 11], [13, 13], [15, 15], [24, 24], [26, 26], [28, 28], [30, 30], [32, 32], [34, 34]] | j63 | 2-47 (12) | 0.87 | j64 1.0 |
| Zelda | usmash | [[5, 5], [7, 7], [9, 9], [11, 11], [13, 13], [15, 15], [24, 24], [26, 26], [28, 28], [30, 30], [32, 32], [34, 34]] | L1stNb | 3-50 (26) | 0.87 | L2ndNa 1.0 |
| Zelda | dsmash | [[4, 7], [13, 16]] | j94 | 0-40 (0) | 0.9 | j94 0.9 |
| Zelda | dsmash | [[4, 7], [13, 16]] | LShoulderJA | 0-40 (2) | 0.81 | LShoulderJ 0.95 |
| Zelda | dsmash | [[4, 7], [13, 16]] | j57 | 0-40 (20) | 0.68 | j58 0.95 |
| Zelda | dsmash | [[4, 7], [13, 16]] | L4thNb | 2-30 (20) | 0.67 | LHandNb 1.03 |
| Zelda | dsmash | [[4, 7], [13, 16]] | WaistB | 1-3 (2) | 0.83 | BustN 1.02 |
| Zelda | dsmash | [[4, 7], [13, 16]] | j45 | 0-40 (23) | 0.51 | j46 1.01 |
| Zelda | dsmash | [[4, 7], [13, 16]] | L1stNb | 1-30 (17) | 0.83 | L2ndNa 1.0 |
| Zelda | dsmash | [[4, 7], [13, 16]] | j63 | 1-34 (3) | 0.73 | j64 1.0 |
| Zelda | dsmash | [[4, 7], [13, 16]] | j51 | 2-33 (4) | 0.63 | j52 1.0 |
| Zelda | nair | [[6, 7], [10, 11], [14, 15], [18, 19], [22, 23], [26, 27]] | j94 | 0-50 (0) | 0.9 | j94 0.9 |
| Zelda | nair | [[6, 7], [10, 11], [14, 15], [18, 19], [22, 23], [26, 27]] | j45 | 0-50 (0) | 0.8 | j46 1.04 |
| Zelda | nair | [[6, 7], [10, 11], [14, 15], [18, 19], [22, 23], [26, 27]] | j20 | 1-43 (6) | 0.7 | WaistB 1.0 |
| Zelda | nair | [[6, 7], [10, 11], [14, 15], [18, 19], [22, 23], [26, 27]] | L1stNa | 1-44 (6) | 0.59 | L1stNb 1.0 |
| Zelda | nair | [[6, 7], [10, 11], [14, 15], [18, 19], [22, 23], [26, 27]] | j62 | 1-45 (6) | 0.54 | j63 1.0 |
| Zelda | fair | [[8, 11]] | j94 | 0-40 (0) | 0.9 | j94 0.9 |
| Zelda | fair | [[8, 11]] | j45 | 0-40 (0) | 0.8 | j46 0.95 |
| Zelda | fair | [[8, 11]] | j44 | 7-36 (9) | 0.75 | j45 0.95 |
| Zelda | fair | [[8, 11]] | j57 | 1-35 (6) | 0.66 | j58 1.04 |
| Zelda | fair | [[8, 11]] | j56 | 2-36 (19) | 1.31 | j57 1.04 |
| Zelda | fair | [[8, 11]] | L1stNa | 1-18 (5) | 0.7 | L1stNb 1.02 |
| Zelda | fair | [[8, 11]] | j62 | 7-38 (28) | 0.67 | j63 1.01 |
| Zelda | fair | [[8, 11]] | j63 | 7-14 (7) | 0.64 | j64 1.01 |
| Zelda | fair | [[8, 11]] | j20 | 1-36 (5) | 0.5 | WaistB 1.0 |
| Zelda | fair | [[8, 11]] | j26 | 1-6 (5) | 0.67 | LShoulderJA 1.0 |
| Zelda | fair | [[8, 11]] | LShoulderJA | 1-35 (7) | 0.65 | LShoulderJ 1.0 |
| Zelda | fair | [[8, 11]] | WaistB | 4-37 (25) | 0.7 | BustN 1.0 |
| Zelda | bair | [[5, 8]] | j94 | 0-36 (0) | 0.9 | j94 0.9 |
| Zelda | bair | [[5, 8]] | L1stNa | 1-28 (12) | 0.7 | L1stNb 1.02 |
| Zelda | bair | [[5, 8]] | j45 | 0-36 (0) | 0.8 | j46 1.01 |
| Zelda | bair | [[5, 8]] | WaistB | 1-4 (3) | 0.77 | BustN 1.01 |
| Zelda | bair | [[5, 8]] | j20 | 2-27 (11) | 0.82 | WaistB 1.01 |
| Zelda | bair | [[5, 8]] | j56 | 1-33 (14) | 0.7 | j57 1.0 |
| Zelda | bair | [[5, 8]] | j63 | 1-4 (3) | 0.44 | j64 1.0 |
| Zelda | bair | [[5, 8]] | j26 | 2-32 (11) | 0.76 | LShoulderJA 1.0 |
| Zelda | bair | [[5, 8]] | j50 | 2-31 (10) | 0.79 | j51 1.0 |
| Zelda | bair | [[5, 8]] | j62 | 2-32 (14) | 0.76 | j63 1.0 |
| Zelda | uair | [[14, 16]] | j45 | 0-55 (0) | 0.8 | j46 0.8 |
| Zelda | uair | [[14, 16]] | j94 | 0-55 (0) | 0.9 | j94 0.9 |
| Zelda | uair | [[14, 16]] | j56 | 38-54 (49) | 0.57 | j57 1.05 |
| Zelda | dair | [[14, 17]] | j94 | 0-44 (0) | 0.9 | j94 0.9 |
| Zelda | dair | [[14, 17]] | j45 | 0-44 (7) | 0.78 | j46 1.03 |
| Zelda | grab | [[11, 12]] | j94 | 0-30 (0) | 0.9 | j94 0.9 |
| Zelda | grab | [[11, 12]] | LShoulderJA | 0-30 (11) | 0.68 | LShoulderJ 0.95 |
| Zelda | grab | [[11, 12]] | j45 | 0-30 (15) | 0.67 | j46 0.95 |
| Zelda | grab | [[11, 12]] | j57 | 0-30 (15) | 0.69 | j58 0.95 |
| Zelda | grab | [[11, 12]] | L4thNb | 2-28 (15) | 0.61 | LHandNb 1.0 |
| Zelda | grab | [[11, 12]] | j63 | 2-26 (11) | 0.75 | j64 1.0 |
| Zelda | grab | [[11, 12]] | WaistB | 3-26 (11) | 0.78 | BustN 1.0 |
| Zelda | grab | [[11, 12]] | L1stNb | 3-26 (11) | 0.78 | L2ndNa 1.0 |
| Zelda | grab | [[11, 12]] | j51 | 3-27 (14) | 0.66 | j52 1.0 |
| Zelda | dash_grab | [[11, 12]] | j94 | 0-40 (0) | 0.9 | j94 0.9 |
| Zelda | dash_grab | [[11, 12]] | j26 | 0-4 (0) | 0.68 | LShoulderJA 0.95 |
| Zelda | dash_grab | [[11, 12]] | LShoulderJA | 0-40 (17) | 0.63 | LShoulderJ 0.95 |
| Zelda | dash_grab | [[11, 12]] | j45 | 0-40 (6) | 0.63 | j46 0.95 |
| Zelda | dash_grab | [[11, 12]] | j56 | 0-3 (0) | 0.86 | j57 0.95 |
| Zelda | dash_grab | [[11, 12]] | j57 | 0-40 (8) | 0.64 | j58 0.95 |
| Zelda | dash_grab | [[11, 12]] | j20 | 0-4 (0) | 0.65 | WaistB 1.0 |
| Zelda | dash_grab | [[11, 12]] | L1stNa | 0-3 (0) | 0.85 | L1stNb 1.0 |
| Zelda | dash_grab | [[11, 12]] | L4thNb | 0-37 (19) | 0.59 | LHandNb 1.0 |
| Zelda | dash_grab | [[11, 12]] | j51 | 0-37 (19) | 0.64 | j52 1.0 |
| Zelda | dash_grab | [[11, 12]] | j62 | 0-4 (0) | 0.64 | j63 1.0 |
| Zelda | dash_grab | [[11, 12]] | WaistB | 3-38 (25) | 0.81 | BustN 1.0 |
| Zelda | dash_grab | [[11, 12]] | L1stNb | 3-26 (6) | 0.9 | L2ndNa 1.0 |
| Zelda | dash_grab | [[11, 12]] | j63 | 3-36 (20) | 0.72 | j64 1.0 |
| Zelda | pummel | [[6, 8]] | LShoulderJA | 0-25 (0) | 0.74 | LShoulderJ 0.74 |
| Zelda | pummel | [[6, 8]] | j57 | 0-25 (0) | 0.77 | j58 0.77 |
| Zelda | pummel | [[6, 8]] | j63 | 0-25 (0) | 0.77 | j64 0.77 |
| Zelda | pummel | [[6, 8]] | j94 | 0-25 (0) | 0.9 | j94 0.9 |
| Zelda | pummel | [[6, 8]] | WaistB | 0-25 (0) | 0.92 | BustN 0.92 |
| Zelda | ledge_quick | [[27, 30]] | j94 | 0-54 (0) | 0.9 | j94 0.9 |
| Zelda | ledge_quick | [[27, 30]] | j63 | 6-48 (36) | 0.44 | j64 1.02 |
| Zelda | ledge_quick | [[27, 30]] | WaistB | 7-48 (33) | 0.53 | BustN 1.01 |
| Zelda | ledge_quick | [[27, 30]] | L1stNb | 7-48 (33) | 0.53 | L2ndNa 1.01 |
| Zelda | ledge_quick | [[27, 30]] | L4thNb | 7-38 (34) | 0.77 | LHandNb 1.01 |
| Zelda | ledge_quick | [[27, 30]] | j51 | 7-47 (36) | 0.66 | j52 1.01 |
| Zelda | ledge_quick | [[27, 30]] | j57 | 6-54 (33) | 0.53 | j58 1.0 |
| Zelda | ledge_quick | [[27, 30]] | LShoulderJA | 7-54 (33) | 0.53 | LShoulderJ 1.0 |
| Zelda | ledge_quick | [[27, 30]] | j45 | 7-54 (36) | 0.66 | j46 1.0 |
| Zelda | ledge_slow | [[34, 39]] | j94 | 0-70 (0) | 0.9 | j94 0.9 |
| Zelda | ledge_slow | [[34, 39]] | LShoulderJA | 32-70 (45) | 0.95 | LShoulderJ 1.0 |
| Zelda | ledge_slow | [[34, 39]] | j45 | 32-70 (45) | 0.95 | j46 1.0 |
| Zelda | ledge_slow | [[34, 39]] | j57 | 32-70 (45) | 0.95 | j58 1.0 |
| Zelda | getup_u | [[17, 19], [25, 27]] | j94 | 0-50 (0) | 0.9 | j94 0.9 |
| Zelda | getup_u | [[17, 19], [25, 27]] | L4thNa | 2-46 (12) | 0.52 | L4thNb 1.0 |
| Zelda | getup_u | [[17, 19], [25, 27]] | j44 | 2-46 (12) | 0.47 | j45 1.0 |
| Zelda | getup_u | [[17, 19], [25, 27]] | L1stNa | 3-41 (12) | 0.8 | L1stNb 1.0 |
| Zelda | getup_u | [[17, 19], [25, 27]] | j51 | 5-41 (12) | 0.81 | j52 1.0 |
| Zelda | getup_u | [[17, 19], [25, 27]] | WaistB | 7-47 (30) | 0.59 | BustN 1.0 |
| Zelda | getup_u | [[17, 19], [25, 27]] | L1stNb | 7-47 (30) | 0.59 | L2ndNa 1.0 |
| Zelda | getup_u | [[17, 19], [25, 27]] | j63 | 7-47 (30) | 0.58 | j64 1.0 |
| Zelda | getup_u | [[17, 19], [25, 27]] | LShoulderJA | 8-50 (30) | 0.66 | LShoulderJ 1.0 |
| Zelda | getup_u | [[17, 19], [25, 27]] | L4thNb | 8-47 (30) | 0.69 | LHandNb 1.0 |
| Zelda | getup_u | [[17, 19], [25, 27]] | j45 | 50-50 (50) | 0.95 | j46 1.0 |
| Zelda | getup_u | [[17, 19], [25, 27]] | j57 | 50-50 (50) | 0.95 | j58 1.0 |
| Zelda | getup_d | [[17, 18], [25, 26]] | j94 | 0-50 (0) | 0.9 | j94 0.9 |
| Zelda | getup_d | [[17, 18], [25, 26]] | LShoulderJA | 0-50 (0) | 0.95 | LShoulderJ 0.95 |
| Zelda | getup_d | [[17, 18], [25, 26]] | j45 | 0-50 (0) | 0.95 | j46 0.95 |
| Zelda | getup_d | [[17, 18], [25, 26]] | j57 | 0-50 (0) | 0.95 | j58 0.95 |
| Falco | jab1 | [[2, 3]] | j26 | 1-9 (5) | 1.34 | j27 1.95 |
| Falco | jab1 | [[2, 3]] | j23 | 3-4 (3) | 1.5 | j26 1.95 |
| Falco | jab2 | [[2, 3]] | j49 | 2-3 (2) | 1.5 | j52 2.4 |
| Falco | jab2 | [[2, 3]] | j52 | 2-9 (2) | 1.6 | RShoulderN 2.4 |
| Falco | dash_attack | [[4, 7], [8, 17]] | LLegJ | 4-5 (4) | 1.3 | LKneeJ 1.3 |
| Falco | dash_attack | [[4, 7], [8, 17]] | j52 | 27-40 (40) | 0.94 | RShoulderN 1.0 |
| Falco | ftilt_hi | [[5, 9]] | RLegJ | 5-16 (6) | 1.21 | RKneeJ 1.21 |
| Falco | ftilt | [[5, 9]] | RLegJ | 5-16 (6) | 1.21 | RKneeJ 1.21 |
| Falco | ftilt_lw | [[5, 9]] | RLegJ | 5-16 (6) | 1.21 | RKneeJ 1.21 |
| Falco | utilt | [[5, 11]] | RLegJ | 5-10 (7) | 1.35 | RKneeJ 1.35 |
| Falco | dtilt | [[7, 9]] | WaistB | 2-12 (8) | 2.3 | WaistB 2.3 |
| Falco | dsmash | [[6, 10]] | LLegJ | 4-9 (6) | 1.3 | LKneeJ 1.3 |
| Falco | dsmash | [[6, 10]] | RLegJ | 4-9 (6) | 1.3 | RKneeJ 1.3 |
| Falco | nair | [[4, 7], [8, 31]] | LFootJ | 4-31 (17) | 1.25 | j10 1.25 |
| Falco | ledge_slow | [[57, 59]] | RLegJ | 56-60 (58) | 1.6 | RKneeJ 1.6 |
| Falco | getup_u | [[17, 19], [24, 26]] | LLegJ | 21-39 (25) | 1.5 | LKneeJ 1.5 |
| Falco | getup_u | [[17, 19], [24, 26]] | j49 | 16-23 (18) | 1.45 | j50 1.45 |
| Falco | getup_d | [[19, 20], [25, 26]] | RLegJ | 20-27 (20) | 1.5 | RKneeJ 1.5 |
| Y.Link | jab1 | [[6, 8]] | j50 | 0-24 (0) | 0.89 | j50 0.89 |
| Y.Link | jab2 | [[6, 7]] | j50 | 0-22 (9) | 0.88 | j50 0.89 |
| Y.Link | jab3 | [[6, 10]] | j50 | 0-50 (0) | 0.89 | j50 0.89 |
| Y.Link | dash_attack | [[7, 12]] | j50 | 0-54 (0) | 0.89 | j50 0.89 |
| Y.Link | ftilt | [[11, 13]] | j50 | 0-34 (0) | 0.89 | j50 0.89 |
| Y.Link | utilt | [[9, 15]] | j50 | 0-30 (0) | 0.89 | j50 0.89 |
| Y.Link | dtilt | [[14, 16]] | j50 | 0-40 (0) | 0.89 | j50 0.89 |
| Y.Link | fsmash | [[15, 17]] | j50 | 0-50 (16) | 0.55 | j50 0.89 |
| Y.Link | fsmash | [[15, 17]] | j28 | 13-16 (15) | 1.1 | j28 1.1 |
| Y.Link | usmash | [[11, 14], [26, 28], [40, 42], [43, 44]] | j50 | 0-61 (43) | 0.77 | j50 0.89 |
| Y.Link | dsmash | [[9, 11], [21, 23]] | j50 | 0-50 (0) | 0.89 | j50 0.89 |
| Y.Link | nair | [[4, 5], [6, 27]] | j50 | 0-40 (0) | 0.89 | j50 0.89 |
| Y.Link | fair | [[14, 16], [17, 33]] | j50 | 0-56 (0) | 0.89 | j50 0.89 |
| Y.Link | bair | [[6, 9], [18, 23]] | j50 | 0-40 (0) | 0.89 | j50 0.89 |
| Y.Link | uair | [[5, 49]] | j50 | 0-70 (0) | 0.89 | j50 0.89 |
| Y.Link | dair | [[13, 64]] | j50 | 0-90 (0) | 0.89 | j50 0.89 |
| Y.Link | grab | [[10, 12], [13, 17]] | j50 | 0-85 (0) | 0.89 | j50 0.89 |
| Y.Link | dash_grab | [[13, 14], [15, 20]] | j50 | 0-95 (0) | 0.89 | j50 0.89 |
| Y.Link | pummel | [[9, 9]] | j50 | 0-25 (0) | 0.89 | j50 0.89 |
| Y.Link | ledge_quick | [[27, 29]] | j50 | 0-56 (0) | 0.89 | j50 0.89 |
| Y.Link | ledge_slow | [[50, 55]] | j50 | 0-70 (0) | 0.89 | j50 0.89 |
| Y.Link | getup_u | [[19, 20], [28, 29]] | j50 | 0-50 (0) | 0.83 | j50 0.89 |
| Y.Link | getup_d | [[15, 16], [24, 26]] | j50 | 0-50 (0) | 0.89 | j50 0.89 |
| Doc | jab1 | [[2, 3]] | LFootJA | 2-12 (2) | 1.4 | j10 2.24 |
| Doc | jab1 | [[2, 3]] | j10 | 2-4 (2) | 1.6 | RLegJA 2.24 |
| Doc | jab2 | [[2, 3]] | L3rdNa | 2-7 (2) | 1.4 | L4thNa 1.96 |
| Doc | jab2 | [[2, 3]] | L4thNa | 2-3 (2) | 1.4 | L4thNb 1.96 |
| Doc | jab2 | [[2, 3]] | LFootJA | 0-2 (0) | 1.06 | LFootJ 1.06 |
| Doc | jab3 | [[4, 8]] | j70 | 3-7 (4) | 1.5 | j72 2.18 |
| Doc | jab3 | [[4, 8]] | j69 | 5-8 (5) | 1.48 | j72 2.18 |
| Doc | jab3 | [[4, 8]] | j72 | 5-8 (5) | 1.23 | j73 2.18 |
| Doc | ftilt_hi | [[4, 8]] | j70 | 3-6 (3) | 1.1 | j71 1.51 |
| Doc | ftilt_hi | [[4, 8]] | j69 | 5-18 (5) | 1.4 | j70 1.51 |
| Doc | ftilt | [[4, 8]] | j70 | 3-6 (3) | 1.1 | j71 1.51 |
| Doc | ftilt | [[4, 8]] | j69 | 5-18 (5) | 1.4 | j70 1.51 |
| Doc | ftilt_lw | [[4, 8]] | j70 | 3-6 (3) | 1.1 | j71 1.51 |
| Doc | ftilt_lw | [[4, 8]] | j69 | 5-18 (5) | 1.4 | j70 1.51 |
| Doc | utilt | [[4, 4], [5, 13]] | L2ndNa | 3-17 (6) | 1.3 | L4thNa 3.01 |
| Doc | utilt | [[4, 4], [5, 13]] | L4thNa | 3-28 (12) | 1.62 | L4thNb 3.01 |
| Doc | utilt | [[4, 4], [5, 13]] | L3rdNb | 4-23 (6) | 1.26 | L4thNa 3.01 |
| Doc | utilt | [[4, 4], [5, 13]] | L3rdNa | 5-18 (6) | 1.14 | L4thNa 3.01 |
| Doc | dtilt | [[5, 8]] | j69 | 5-8 (5) | 2 | j70 2.0 |
| Doc | fsmash_hi | [[12, 16]] | YRotN | 12-13 (12) | 1.15 | j10 1.64 |
| Doc | fsmash_hi | [[12, 16]] | LFootJA | 12-13 (12) | 1.3 | j10 1.64 |
| Doc | fsmash_hi | [[12, 16]] | j10 | 12-12 (12) | 1.1 | RLegJA 1.64 |
| Doc | fsmash_hi | [[12, 16]] | LShoulderN | 12-36 (12) | 0.73 | LShoulderN 1.09 |
| Doc | fsmash_hi | [[12, 16]] | RLegJ | 12-26 (14) | 0.55 | RLegJ 1.05 |
| Doc | fsmash_hi | [[12, 16]] | RFootJA | 12-26 (12) | 0.53 | RFootJA 1.0 |
| Doc | fsmash_hi | [[12, 16]] | j16 | 12-26 (12) | 0.44 | j16 1.0 |
| Doc | fsmash_hi | [[12, 16]] | WaistB | 12-26 (12) | 0.48 | WaistB 1.0 |
| Doc | fsmash | [[12, 16]] | YRotN | 12-13 (12) | 1.15 | j10 1.64 |
| Doc | fsmash | [[12, 16]] | LFootJA | 12-17 (12) | 1.3 | j10 1.64 |
| Doc | fsmash | [[12, 16]] | j10 | 12-12 (12) | 1.1 | RLegJA 1.64 |
| Doc | fsmash | [[12, 16]] | LShoulderN | 3-36 (12) | 0.73 | LShoulderN 1.09 |
| Doc | fsmash | [[12, 16]] | RLegJ | 12-26 (14) | 0.55 | RLegJ 1.05 |
| Doc | fsmash | [[12, 16]] | RFootJA | 12-26 (12) | 0.53 | RFootJA 1.0 |
| Doc | fsmash | [[12, 16]] | j16 | 12-26 (12) | 0.44 | j16 1.0 |
| Doc | fsmash | [[12, 16]] | WaistB | 12-26 (12) | 0.48 | WaistB 1.0 |
| Doc | fsmash_lw | [[12, 16]] | YRotN | 12-13 (12) | 1.1 | j10 1.57 |
| Doc | fsmash_lw | [[12, 16]] | LFootJA | 12-13 (12) | 1.3 | j10 1.57 |
| Doc | fsmash_lw | [[12, 16]] | j10 | 12-12 (12) | 1.1 | RLegJA 1.57 |
| Doc | fsmash_lw | [[12, 16]] | LShoulderN | 12-38 (12) | 0.73 | LShoulderN 1.04 |
| Doc | fsmash_lw | [[12, 16]] | RLegJ | 12-26 (14) | 0.55 | RLegJ 1.01 |
| Doc | fsmash_lw | [[12, 16]] | RFootJA | 12-26 (12) | 0.53 | RFootJA 1.0 |
| Doc | fsmash_lw | [[12, 16]] | j16 | 12-26 (12) | 0.44 | j16 1.0 |
| Doc | fsmash_lw | [[12, 16]] | WaistB | 12-26 (12) | 0.48 | WaistB 1.0 |
| Doc | usmash | [[9, 10], [11, 11]] | LShoulderJA | 11-12 (11) | 1.1 | LShoulderJ 1.1 |
| Doc | dsmash | [[5, 6], [14, 15]] | R1stNa | 5-16 (7) | 0.89 | R1stNb 1.39 |
| Doc | dsmash | [[5, 6], [14, 15]] | R1stNb | 5-17 (5) | 1.3 | R2ndNa 1.39 |
| Doc | dsmash | [[5, 6], [14, 15]] | j69 | 5-16 (7) | 0.89 | j70 1.39 |
| Doc | dsmash | [[5, 6], [14, 15]] | j70 | 5-17 (5) | 1.3 | j71 1.39 |
| Doc | fair | [[18, 22]] | L4thNa | 6-37 (17) | 1.5 | L4thNb 2.4 |
| Doc | fair | [[18, 22]] | L3rdNa | 13-36 (17) | 1.6 | L4thNa 2.4 |
| Doc | fair | [[18, 22]] | j42 | 13-39 (17) | 0.45 | j42 1.15 |
| Doc | bair | [[6, 8], [9, 16]] | R1stNa | 3-15 (7) | 2 | R1stNb 2.0 |
| Doc | bair | [[6, 8], [9, 16]] | j69 | 6-15 (7) | 2 | j74 2.0 |
| Doc | uair | [[4, 9]] | j69 | 3-13 (4) | 1.75 | j70 1.75 |
| Doc | grab | [[6, 7]] | LFootJA | 2-13 (5) | 1.2 | LFootJ 1.2 |
| Doc | grab | [[6, 7]] | L3rdNa | 2-13 (5) | 1.2 | L3rdNb 1.2 |
| Doc | dash_grab | [[10, 11]] | LFootJA | 4-18 (10) | 1.2 | LFootJ 1.2 |
| Doc | dash_grab | [[10, 11]] | L3rdNa | 4-18 (10) | 1.2 | L3rdNb 1.2 |
| Doc | pummel | [[16, 16]] | LFootJA | 0-24 (0) | 1.2 | LFootJ 1.2 |
| Doc | pummel | [[16, 16]] | L3rdNa | 0-24 (0) | 1.2 | L3rdNb 1.2 |
| Doc | ledge_quick | [[24, 36]] | R1stNa | 24-32 (26) | 1.56 | R1stNb 1.82 |
| Doc | ledge_quick | [[24, 36]] | R1stNb | 24-31 (26) | 1.17 | R2ndNa 1.82 |
| Doc | ledge_quick | [[24, 36]] | j69 | 24-32 (26) | 1.56 | j70 1.82 |
| Doc | ledge_quick | [[24, 36]] | j70 | 24-31 (26) | 1.17 | j71 1.82 |
| Doc | ledge_slow | [[40, 44]] | j69 | 39-46 (40) | 1.4 | j70 1.88 |
| Doc | ledge_slow | [[40, 44]] | j70 | 39-46 (41) | 1.36 | j71 1.88 |
| Doc | getup_u | [[20, 21], [24, 25]] | j69 | 9-28 (20) | 1.5 | j70 1.5 |
| Doc | getup_u | [[20, 21], [24, 25]] | R1stNa | 19-28 (20) | 1.5 | R1stNb 1.5 |
| Doc | getup_d | [[19, 20], [25, 26]] | L4thNa | 17-43 (33) | 1.56 | L4thNb 1.56 |
| Pichu | dash_attack | [[5, 16]] | XRotN | 9-28 (17) | 0.6 | YRotN 1.3 |
| Pichu | dash_attack | [[5, 16]] | RLegJA | 5-28 (17) | 0.05 | RLegJA 1.19 |
| Pichu | ftilt_hi | [[5, 14]] | RHandNb | 2-8 (5) | 1.8 | LLegJA 2.7 |
| Pichu | ftilt_hi | [[5, 14]] | LLegJA | 2-8 (5) | 1.5 | LLegJ 2.7 |
| Pichu | ftilt_hi | [[5, 14]] | LFootJA | 2-8 (5) | 1.8 | j41 2.7 |
| Pichu | ftilt_hi | [[5, 14]] | j41 | 2-8 (5) | 1.5 | j42 2.7 |
| Pichu | ftilt | [[5, 14]] | RHandNb | 2-8 (5) | 1.6 | LLegJA 2.4 |
| Pichu | ftilt | [[5, 14]] | LLegJA | 2-8 (5) | 1.5 | LLegJ 2.4 |
| Pichu | ftilt | [[5, 14]] | LFootJA | 2-8 (5) | 1.6 | j41 2.4 |
| Pichu | ftilt | [[5, 14]] | j41 | 2-8 (5) | 1.5 | j42 2.4 |
| Pichu | ftilt_lw | [[5, 14]] | RHandNb | 2-8 (5) | 1.6 | LLegJA 2.4 |
| Pichu | ftilt_lw | [[5, 14]] | LLegJA | 2-8 (5) | 1.5 | LLegJ 2.4 |
| Pichu | ftilt_lw | [[5, 14]] | LFootJA | 2-8 (5) | 1.6 | j41 2.4 |
| Pichu | ftilt_lw | [[5, 14]] | j41 | 2-8 (5) | 1.5 | j42 2.4 |
| Pichu | utilt | [[7, 14]] | RLegJA | 1-17 (10) | 3.5 | RLegJA 3.5 |
| Pichu | dtilt | [[7, 9]] | RLegJA | 3-19 (7) | 3 | RLegJA 2.85 |
| Pichu | dtilt | [[7, 9]] | XRotN | 7-15 (7) | 0.95 | RLegJA 2.85 |
| Pichu | usmash | [[9, 11]] | XRotN | 10-26 (17) | 0.8 | L2ndNa 1.21 |
| Pichu | usmash | [[9, 11]] | L2ndNa | 10-11 (10) | 1.1 | L2ndNb 1.21 |
| Pichu | dsmash | [[7, 13]] | TransN | 6-34 (7) | 0.9 | LFootJA 1.01 |
| Pichu | dsmash | [[7, 13]] | LFootJA | 6-37 (7) | 0.8 | LFootJ 1.01 |
| Pichu | dsmash | [[7, 13]] | j41 | 6-36 (7) | 1.2 | j42 1.0 |
| Pichu | fair | [[10, 12], [14, 16], [18, 20], [22, 24]] | XRotN | 7-12 (10) | 0.8 | YRotN 1.0 |
| Pichu | fair | [[10, 12], [14, 16], [18, 20], [22, 24]] | RLegJA | 32-39 (34) | 0.55 | RLegJA 1.0 |
| Pichu | bair | [[4, 7], [8, 37]] | XRotN | 2-33 (5) | 0.9 | YRotN 1.0 |
| Pichu | uair | [[4, 5], [6, 7], [8, 9]] | RLegJA | 2-18 (6) | 2.07 | RLegJA 2.07 |
| Pichu | dair | [[14, 26]] | XRotN | 6-17 (14) | 1.4 | YRotN 1.4 |
| Pichu | dair | [[14, 26]] | RLegJA | 7-49 (13) | 0.8 | RLegJA 1.19 |
| Pichu | pummel | [[2, 2]] | RLegJA | 3-21 (12) | 1.59 | RLegJA 1.59 |
| Pichu | ledge_quick | [[22, 24]] | j41 | 22-28 (23) | 2.18 | j42 2.18 |
| Pichu | ledge_slow | [[54, 59]] | RLegJA | 53-60 (55) | 3.2 | RLegJA 3.2 |
| Pichu | getup_u | [[13, 14], [18, 19]] | LLegJA | 4-19 (13) | 2 | LLegJ 2.2 |
| Pichu | getup_u | [[13, 14], [18, 19]] | j41 | 4-41 (13) | 2 | j42 2.2 |
| Pichu | getup_u | [[13, 14], [18, 19]] | RHandNb | 13-19 (13) | 1.1 | LLegJA 2.2 |
| Pichu | getup_u | [[13, 14], [18, 19]] | LFootJA | 13-19 (13) | 1.1 | j41 2.2 |
| Ganon | bair | [[10, 15]] | LShoulderJA | 10-12 (10) | 1.28 | LHandN 1.53 |
| Ganon | bair | [[10, 15]] | LHandN | 10-12 (10) | 1.2 | L1stNa 1.53 |
| Ganon | dair | [[16, 20]] | LLegJ | 3-18 (17) | 1.25 | LKneeJ 1.25 |
| Ganon | dair | [[16, 20]] | RLegJ | 3-18 (17) | 1.25 | RKneeJ 1.25 |
| Ganon | ledge_quick | [[24, 29]] | RKneeJ | 25-29 (25) | 1.2 | RFootJA 1.2 |

376 of 666 moves scale a body part.
