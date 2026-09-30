/* director: turns Super Smash Bros. Melee (the doldecomp/melee decompilation, non-matching build) into a deterministic
 * machinima renderer. The game boots straight into a VS match set up by the script, the HUD and music are off, and every game
 * frame the director writes the script's controller states, camera and one-shot cues. It reports back through OSReport, which
 * Dolphin logs: frame-stamped hits, action-state changes and the end marker. tools/machinima/melee/build.py compiles a film's
 * shot script (Python, tools/machinima/melee/dsl.py) into script.c, which defines the tables declared here.
 *
 * Timeline, in game frames F from match start:
 *   [0, SLATE)              slate: the stage hidden on a magenta clear colour, fighters frozen, a menu click on its first
 *                           frame. The host trims the plates up to its end and syncs the audio dump to the click.
 *   s = F - SLATE, [0, len) the script, on the film's clock (s / 60 = seconds from the plate's first frame)
 *   [len, len + SLATE)      end slate, so the host can check no frame was dropped or doubled
 *   then OSReport("DIRECTOR END") and the scene ends.
 */
#ifndef MELEE_DIRECTOR_H
#define MELEE_DIRECTOR_H

#include <Runtime/platform.h>
#include <melee/ft/forward.h>
#include <melee/mn/types.h>
#include <dolphin/mtx.h>

#define DIR_SLATE 8

/* a pad state, held from `frame` until the port's next entry; sticks are raw -80..80, trig is the analog L/R 0..140 */
typedef struct DirPad {
    s32 frame; /* s16 capped a script at 32767 frames (~9 minutes); labs run longer */
    u8 port;
    u8 trig;
    u32 buttons;
    s8 sx, sy, cx, cy;
} DirPad;

enum { DIR_CUT = 0, DIR_LINEAR, DIR_INOUT, DIR_IN, DIR_OUT };
enum { DIR_AUTO_FASTFALL = 1, DIR_AUTO_LCANCEL = 2, DIR_AUTO_LOWLASER = 4 };

enum { DIR_WORLD = 0, DIR_MID, DIR_P0, DIR_P1 };

/* camera keys: eye, interest (at), vertical fov in degrees and roll in degrees; `ease` shapes the move to the next key.
 * With `track` set, eye and at are offsets from a smoothed tracking point: the fighters' midpoint, or one fighter. The point
 * snaps to the fighters on a cut, so each shot starts framed. */
typedef struct DirCam {
    s32 frame; /* s16 capped a script at 32767 frames (~9 minutes); labs run longer */
    u8 ease;
    u8 track;
    f32 eye[3];
    f32 at[3];
    f32 fov;
    f32 roll;
} DirCam;

enum {
    DIR_FREEZE = 1, /* a: 1 freezes fighters, items and effects (the camera keeps running), 0 releases them */
    DIR_STAGE,      /* a: stage visible 0/1 */
    DIR_BGCOLOR,    /* a, b, c: clear colour 0..255 */
    DIR_SETPOS,     /* port; a, b: x, y */
    DIR_FACE,       /* port; a: facing -1 or 1 */
    DIR_MOTION,     /* port; a: motion state id; b: animation start frame */
    DIR_PERCENT,    /* port; a: damage percent */
    DIR_MARK,       /* a: id, logged as MARK */
    DIR_END,        /* end the script here */
    DIR_RESET,      /* port; a: x, b: facing. Stand the fighter on the floor at x, in Wait, with no momentum (between shots) */
    DIR_APPROACH,   /* port; a: range, b: until frame, c: stick. Closed loop: walk toward the opponent while farther than
                     * range, then stand, so a scripted move finds its mark whatever the last knockback did */
    DIR_AUTO,       /* port; a: flags. Closed-loop tech on every aerial: 1 fast fall on the first descending frame,
                     * 2 L-cancel (a shoulder press ~3 frames before touching the floor), 4 low laser (B on the 8th
                     * airborne frame of any hop: the laser spawns 12 frames later at standing-fighter height) */
    DIR_TRACE,      /* port; a: until frame. Log POS s port x y motion hipx hipy every frame (for planning combos; the hip
                     * joint shows the body where cur_pos does not, e.g. hanging on a ledge) */
    DIR_STATUS,     /* port. Log STATUS s port percent x y motion (for labs: throw damage, launch results) */
    DIR_SHIELD,     /* port. Log the shield sphere (ThrowN's world centre and scale) and every hurtbox capsule in world space */
    DIR_FEET,       /* port. Log FEET s port side x y z fx fy fz dx dy dz motion frame: each foot bone's world position and
                     * its local X and Y axes (ftData's LeftFootBone/RightFootBone), the motion state and animation frame */
    DIR_SHIELDHP,   /* port; a: shield health (60 is full): a lab's shield break without minutes of shielding */
    DIR_ITEM,       /* a: ::ItemKind, b, c: x, y. Spawn a common item there (a bat, a crate, a Super Scope...), as the
                     * game's own item drop does, whatever the match's item switch; for labs of the item actions */
    DIR_SFX,        /* a: sound id, b: volume 0-127 (0 = 127). Play a sound as a move script's SoundEffect does
                     * (lbAudioAx_800237A8, centred) and log SFX s id voice: for labs that check a bank's sounds in game */
    DIR_ANIM,       /* port; a: action-table entry. Play that entry's animation and script in the current state, through
                     * the engine's own idle-variant player (ftCo_8008A6D8, Wait's): for animations no state plays
                     * (ItemBlind) */
    DIR_GRDUMP,     /* a: 0 floors only, 1 every line. The stage as the engine holds it this frame: STAGE s grkind stkind
                     * blast l r t b cam l r t b offset x y; LINE s id flags lo x0 y0 x1 y1 for each live collision line
                     * (after joint binding, so moving platforms read where they are); GROUND s port x y air line motion
                     * ledge for every fighter (the floor line it stands on; the ledge line it holds, in the cliff states).
                     * For stage labs and stage-build checks */
    DIR_ITEMS,      /* Log ITEMS s kind x y per live item this frame (a lab's projectile paths: Link's boomerang, Geno's Whirl) */
    DIR_SHOOT       /* port: the owner; a: kind*16 + state + 4096*(speed*10); b, c: the spawn's offset from the owner (b along
                     * his facing, c up). A laser-type projectile (it_8029C504: Fox's, Falco's, Geno's Finger Shot and Beam
                     * states) fired straight ahead, as its owner's: a lab fires any state of those articles where a move
                     * can't aim it (Geno's throw shots at a PSI Magnet). Logs SHOOT s port kind state x y speed */
};

typedef struct DirCue {
    s32 frame; /* s16 capped a script at 32767 frames (~9 minutes); labs run longer */
    u8 kind;
    u8 port;
    f32 a, b, c;
} DirCue;

typedef struct DirSetup {
    u16 stage;     /* ::StageKind (St_Kind_Last = Final Destination) */
    u8 nplayers;
    u8 entry;      /* 1: fighters play their entry animation */
    s8 ckind[4];   /* ::CharacterKind */
    u8 color[4];   /* costume */
    f32 x[4];      /* start position (placed at F = 0) */
    s8 face[4];    /* start facing */
    u32 seed;      /* RNG seed, fixed before stage setup */
    f32 aspect;    /* 0 keeps the game's 4:3 */
    u8 cpu[4];     /* 0: the director's pads drive the port; 1-9: the game's CPU at that level */
    u8 stocks;     /* 0: a time match with no timer (films); N: a stock match with N stocks each (the HUD shows stocks) */
} DirSetup;

/* menu tests: boot into one of the game's own modes (dir_boot_mode, a ::GameModeKind; films use GM_DEBUG_VS) and drive its
 * menus with pads written into the master pad status, so menus and matches read them like a real controller. Each entry is
 * held from `frame` (loop frames since boot) until the port's next entry. Films have no entries. */
typedef struct DirMenuPad {
    s32 frame;
    u8 port;
    u8 trig;
    u16 buttons;
    s8 sx, sy, cx, cy;
} DirMenuPad;

/* closed-loop cursor moves on the character select screen: from `frame` until `until`, the port's stick steers its token
 * (the chip it drops on an icon, which is what the screen hit-tests) to (x, y) in icon-bound units, then holds still */
typedef struct DirMenuGoto {
    s32 frame, until;
    u8 port;
    f32 x, y;
} DirMenuGoto;

extern const int dir_boot_mode;
extern const int dir_show_coll;   /* developer display: 0 off, 1 the model with hitboxes and hurtboxes, 2 the capsules only */
extern const int dir_results_music; /* 1: music back on for the scenes after a match (the victory fanfare); films 0 */
extern const DirMenuGoto dir_menu_gotos[];
extern const int dir_nmenu_gotos;
extern const DirMenuPad dir_menu_pads[];
extern const int dir_nmenu_pads;

extern const DirSetup dir_setup;
extern const DirPad dir_pads[];
extern const int dir_npads;
extern const DirCam dir_cams[];
extern const int dir_ncams;
extern const DirCue dir_cues[];
extern const int dir_ncues;
extern const int dir_len;

void director_setup_match(StartMeleeData* start);
int director_boot(void);        /* at boot: returns the ::GameModeKind to start in (menu tests also unlock every character) */
void director_boot_frame(void); /* every loop frame, after the master pad status is read */
void director_on_hit(Fighter_GObj* attacker, Fighter_GObj* victim, float dmg);
void director_on_item_hit(HSD_GObj* item, Fighter_GObj* victim, float dmg);
void director_on_laser(HSD_GObj* parent, Vec3* pos, int kind, float angle, float speed);

#endif
