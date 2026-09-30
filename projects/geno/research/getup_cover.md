# Get-up attacks: coverage (measured)

Get-up attack coverage across the cast: how high the hits reach on each side, whether they cover the space over the
fighter's own body, and how high an opponent must be to clear them (jump clearance), from `datkit movedata` geometry (every
active frame's spheres in the fighter's space: facing +z, feet at y = 0).
For each move, top(z) is the highest point any hitbox covers at horizontal offset z over all active frames. Reported:
  - side top: the highest point covered in front (z > 0) and behind (z < 0);
  - top at 8 / 14 units: the height covered where an opponent stands close in and at mid range, each side;
  - over body: the highest point covered within 3 units of his centre (0: nothing over him);
  - clear at d: the height an opponent's feet must be above, at centre distance d, to pass over untouched (the highest
    coverage within W of d; W = 3, an airborne body's half-width), at d = 0 (a hop straight over him), 8 and 14.

Units are world units; heights from his feet. `pct` is Geno's percentile in the cast (25 others).

## getup_u

| | front_top | back_top | front_8 | back_8 | front_14 | back_14 | over_body | clear_0 | clear_8 | clear_14 |
|---|---|---|---|---|---|---|---|---|---|---|
| cast min | 6.0 | 6.0 | 0.0 | 0.0 | 0.0 | 0.0 | 5.2 | 5.2 | 6.0 | 0.0 |
| cast median | 14.8 | 13.5 | 12.4 | 12.4 | 13.6 | 12.4 | 11.4 | 11.4 | 14.6 | 14.3 |
| cast max | 25.0 | 24.1 | 24.7 | 23.8 | 24.2 | 23.4 | 20.5 | 20.5 | 25.0 | 24.9 |
| Fox | 14.7 | 15.0 | 11.4 | 14.1 | 13.2 | 14.4 | 15.0 | 15.0 | 14.6 | 14.6 |
| Falco | 16.8 | 17.2 | 11.6 | 16.2 | 15.2 | 16.7 | 17.2 | 17.2 | 16.6 | 16.7 |
| Marth | 17.0 | 15.8 | 15.6 | 13.9 | 15.3 | 13.3 | 15.7 | 15.7 | 15.7 | 16.8 |
| Sheik | 14.9 | 17.6 | 13.0 | 17.2 | 14.9 | 17.2 | 14.9 | 14.9 | 17.6 | 17.6 |
| Falcon | 22.3 | 21.6 | 22.2 | 21.5 | 20.7 | 20.3 | 18.4 | 18.4 | 22.3 | 22.1 |
| Peach | 11.4 | 11.8 | 9.7 | 11.2 | 11.4 | 11.8 | 8.1 | 8.1 | 11.5 | 11.8 |
| Puff | 8.3 | 8.2 | 6.3 | 6.1 | 7.7 | 7.2 | 8.3 | 8.3 | 7.2 | 7.7 |
| Samus | 19.4 | 19.3 | 19.4 | 19.3 | 16.5 | 16.1 | 16.5 | 16.5 | 19.4 | 19.0 |
| Mario | 13.7 | 12.4 | 12.6 | 12.3 | 13.6 | 12.4 | 10.7 | 10.7 | 13.6 | 13.7 |
| **GENO now** | **14.4** | **14.4** | **12.9** | **12.9** | **14.4** | **14.4** | **10.8** | **10.8** | **14.0** | **14.4** |
| Geno pct | 48 | 56 | 60 | 60 | 60 | 71 | 48 | 48 | 48 | 52 |

## getup_d

| | front_top | back_top | front_8 | back_8 | front_14 | back_14 | over_body | clear_0 | clear_8 | clear_14 |
|---|---|---|---|---|---|---|---|---|---|---|
| cast min | 5.6 | 5.6 | 0.0 | 5.6 | 0.0 | 0.0 | 0.0 | 0.0 | 5.6 | 0.0 |
| cast median | 13.5 | 14.2 | 13.2 | 13.2 | 11.1 | 12.4 | 11.2 | 11.2 | 14.9 | 14.5 |
| cast max | 22.3 | 21.9 | 21.9 | 19.2 | 21.8 | 21.3 | 21.6 | 21.6 | 21.9 | 22.1 |
| Fox | 12.3 | 14.9 | 12.3 | 14.5 | 11.1 | 14.2 | 10.6 | 10.6 | 14.9 | 14.9 |
| Falco | 14.1 | 17.1 | 13.9 | 16.0 | 13.8 | 17.0 | 11.3 | 11.3 | 17.0 | 17.1 |
| Marth | 17.9 | 18.3 | 14.4 | 16.2 | 12.4 | 18.3 | 18.1 | 18.1 | 17.9 | 18.3 |
| Sheik | 21.9 | 19.9 | 21.7 | 17.6 | 16.4 | 17.1 | 21.6 | 21.6 | 21.9 | 19.9 |
| Falcon | 19.9 | 17.3 | 16.4 | 15.6 | 19.9 | 17.3 | 12.0 | 12.0 | 18.6 | 19.9 |
| Peach | 7.5 | 8.6 | 7.2 | 8.2 | 6.0 | 8.1 | 7.6 | 7.6 | 8.6 | 8.6 |
| Puff | 11.7 | 12.4 | 11.7 | 12.4 | 9.0 | 9.7 | 11.4 | 11.4 | 12.4 | 11.8 |
| Samus | 19.8 | 19.6 | 17.6 | 16.7 | 19.7 | 19.6 | 0.0 | 0.0 | 19.5 | 19.8 |
| Mario | 12.9 | 13.6 | 12.9 | 13.2 | 11.1 | 12.9 | 11.2 | 11.2 | 13.6 | 13.6 |
| **GENO now** | **14.4** | **14.4** | **12.9** | **12.9** | **14.4** | **14.4** | **10.7** | **10.7** | **14.0** | **14.4** |
| Geno pct | 56 | 52 | 44 | 48 | 75 | 63 | 48 | 48 | 48 | 52 |

