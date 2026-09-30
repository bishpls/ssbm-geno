/* director.c: the runtime half of the machinima director (see director.h). C89, prototypes required (-requireprotos). */
#include "director.h"

#include <dolphin/os.h>
#include <melee/cm/camera.h>
#include <melee/ft/fighter.h>
#include <melee/ft/ft_0892.h>
#include <melee/ft/ftcommon.h>
#include <melee/ft/ftwaitanim.h>
#include <melee/ft/ftcolanim.h>
#include <melee/ft/ftdevice.h>
#include <melee/ft/ftlib.h>
#include <melee/ft/ftparts.h>
#include <melee/ft/inlines.h>
#include <melee/ft/types.h>
#include <melee/ft/kinds/ftCommon/types.h>
#include <melee/gm/forward.h>
#include <melee/gm/gm_1A3F.h>
#include <melee/gm/gmmain_lib.h>
#include <melee/gm/gmscene.h>
#include <melee/gr/forward.h>
#include <melee/gr/ground.h>
#include <melee/gr/stage.h>
#include <melee/gr/types.h>
#include <melee/mp/mplib.h>
#include <melee/mp/types.h>
#include <melee/if/ifall.h>
#include <melee/it/it_26B1.h>
#include <melee/it/item.h>
#include <melee/it/kinds/itfoxlaser.h>
#include <melee/it/types.h>
#include <melee/lb/lbaudio_ax.h>
#include <melee/mn/mncharsel.h>
#include <melee/mn/mnstagesel.h>
#include <melee/pl/forward.h>
#include <melee/pl/player.h>
#include <melee/pl/plstale.h>
#include <melee/sfx/crowdsfx.h>
#include <sysdolphin/baselib/cobj.h>
#include <sysdolphin/baselib/controller.h>
#include <sysdolphin/baselib/gobj.h>
#include <sysdolphin/baselib/jobj.h>
#include <math.h>
#include <string.h>
#include <sysdolphin/baselib/random.h>

static void director_match_start(void);
static void director_update(void);
static void put_pad(int port, const DirPad* p);
static void put_camera(int s);
static void cam_abs(const DirCam* k, Vec3* eye, Vec3* at);
static void run_cue(const DirCue* c);
static void slate(int on);
static f32 ease(int kind, f32 u);
static Fighter* fighter(int port);
static void track_update(int snap);
static void menu_goto(void);
static void show_coll(void);

static int F;                 /* game frames since match start */
static s32 crowd_last[3] = { -1, -1, -1 }; /* the crowd state last logged (CROWD lines) */
static int s_end;             /* the script's last frame + 1 (a DIR_END cue can shorten it) */
static int done;
static int pad_i[4];          /* next dir_pads index per port is found by scanning; this is the last applied entry */
static const DirPad* pad_cur[4];
static u32 last_buttons[4];
static int cue_i;
static s32 last_msid[4];
static s32 last_held[4];      /* whether each port held an item last frame (HOLD / LETGO lines) */
static s32 last_vis[4];       /* each port's visibility-group options last frame, packed 4 bits a group (VIS lines) */
static Vec3 trk[4];           /* smoothed tracking points: [DIR_MID], [DIR_P0], [DIR_P1] */
static int cam_key;           /* the camera key in effect last frame */
static int ap_until[4];       /* approach: active while s < ap_until */
static f32 ap_range[4];
static s8 ap_stick[4];
static u8 auto_flags[4];      /* DIR_AUTO_* per port */
static u8 ff_done[4], lc_done[4];
static s8 ff_hold[4], lc_hold[4];
static u8 ll_done[4], ll_ff[4];
static int air_frames[4];
static int trace_until[4];
static void auto_tech(int s);

static int boot_F;             /* loop frames since boot */
static int menu_i[4];
static u8 last_mode = 0xFF, last_scene = 0xFF;

/* the developer display of hitboxes and hurtboxes, on every fighter in a match (the flags Melee's develop mode toggles:
 * x21FC b6 draws the collision capsules, b7 the model) */
static void show_coll(void)
{
    int port;
    u8 mode = gm_GetCurrentGameMode();
    if (dir_show_coll == 0 || !(mode == GM_DEBUG_VS || (mode == GM_VS && gm_GetCurrentSceneIndex() == 2))) {
        return;
    }
    for (port = 0; port < 4; port++) {
        HSD_GObj* g = Player_GetEntity(port);
        if (g != NULL) {
            Fighter* fp = GET_FIGHTER(g);
            fp->x21FC_flag.b6 = 1;
            fp->x21FC_flag.b7 = dir_show_coll != 2;
        }
    }
}

/* steer each active goto's token toward its target: the hand moves ~0.015 units a frame per unit of stick, so half the
 * error per frame converges without overshoot; menus ignore small sticks, so a move is at least 24 */
static void menu_goto(void)
{
    int i, k;
    f32 hand[2], tok[2];
    if ((gm_GetCurrentGameMode() != GM_VS && gm_GetCurrentGameMode() != GM_TRAINING) || gm_GetCurrentSceneIndex() != 0) {
        return; /* the character select of VS or Training */
    }
    for (i = 0; i < dir_nmenu_gotos; i++) {
        const DirMenuGoto* g = &dir_menu_gotos[i];
        HSD_PadStatus* ps = &HSD_PadMasterStatus[g->port];
        f32 e[2];
        s8 st[2];
        if (boot_F < g->frame || boot_F >= g->until || !mnCharSel_DebugPositions(g->port, hand, tok)) {
            continue;
        }
        e[0] = g->x - tok[0];
        e[1] = g->y - tok[1];
        for (k = 0; k < 2; k++) {
            f32 v = e[k] / 0.015f * 0.5f;
            if (v > 80.0f) {
                v = 80.0f;
            } else if (v < -80.0f) {
                v = -80.0f;
            }
            if (e[k] > 0.25f && v < 24.0f) {
                v = 24.0f;
            } else if (e[k] < -0.25f && v > -24.0f) {
                v = -24.0f;
            } else if (e[k] <= 0.25f && e[k] >= -0.25f) {
                v = 0.0f;
            }
            st[k] = (s8) v;
        }
        ps->err = 0;
        ps->stickX = st[0];
        ps->stickY = st[1];
        ps->nml_stickX = st[0] / 80.0f;
        ps->nml_stickY = st[1] / 80.0f;
        if ((boot_F - g->frame) % 4 == 0 || boot_F == g->until - 1) {
            OSReport("CSSPOS %d port %d hand %.2f %.2f token %.2f %.2f stick %d %d\n", boot_F, g->port, hand[0], hand[1],
                     tok[0], tok[1], st[0], st[1]);
        }
    }
}

int director_boot(void)
{
    if (dir_boot_mode != GM_DEBUG_VS) {
        *gmMainLib_GetUnlockedCharactersBitmaskPtr() = 0x7FF; /* all 11 unlockable characters */
        *gmMainLib_8015EDA4() = 0x7FF;                         /* all 11 unlockable stages (save data x186A) */
        gmMainLib_GetGamePrefs()->stage_mask = 0xFFFFFFFF;     /* and every stage on in random stage select */
    }
    OSReport("DIRECTOR BOOT mode %d\n", dir_boot_mode);
    return dir_boot_mode;
}

void director_boot_frame(void)
{
    int port, i;
    u8 mode = gm_GetCurrentGameMode(), scene = gm_GetCurrentSceneIndex();
    if (mode != last_mode || scene != last_scene) {
        OSReport("SCENE %d mode %d scene %d stkind %d\n", boot_F, mode, scene, (int) Stage_80225194());
        last_mode = mode;
        last_scene = scene;
        if (dir_results_music && F > 0) {
            /* leaving a match that has run (F: its frames): the match muted the music (director_match_start) and the
             * results screen's fanfare needs it back. The stage music stays off regardless (rules.x1_4) */
            lbAudioAx_80025064(1, 1);
            OSReport("DIRECTOR MUSIC ON %d\n", boot_F);
        }
    }
    if (boot_F == 0) {
        for (port = 0; port < 4; port++) {
            menu_i[port] = -1;
        }
    }
    for (port = 0; port < 4; port++) {
        HSD_PadStatus* ps = &HSD_PadMasterStatus[port];
        const DirMenuPad* p = NULL;
        for (i = menu_i[port] + 1; i < dir_nmenu_pads && dir_menu_pads[i].frame <= boot_F; i++) {
            if (dir_menu_pads[i].port == port) {
                menu_i[port] = i;
            }
        }
        if (menu_i[port] < 0) {
            continue;
        }
        p = &dir_menu_pads[menu_i[port]];
        ps->err = 0;
        ps->button = p->buttons;
        ps->stickX = p->sx;
        ps->stickY = p->sy;
        ps->subStickX = p->cx;
        ps->subStickY = p->cy;
        ps->analogL = ps->analogR = p->trig;
        ps->nml_stickX = p->sx / 80.0f;
        ps->nml_stickY = p->sy / 80.0f;
        ps->nml_subStickX = p->cx / 80.0f;
        ps->nml_subStickY = p->cy / 80.0f;
        ps->nml_analogL = ps->nml_analogR = p->trig / 140.0f;
    }
    if (dir_boot_mode != GM_DEBUG_VS && boot_F == dir_len) {
        OSReport("DIRECTOR MENU END %d\n", boot_F); /* a menu test's length: dolphin.py --until stops here */
    }
    menu_goto();
    {
        /* the stage select (menu tests): the hovered entry and the cursor, every 4 frames and on each change */
        static int last_hover = -2;
        f32 xy[2];
        int count, hover = mnStageSel_DebugState(xy, &count);
        if (hover >= 0 && (hover != last_hover || boot_F % 4 == 0)) {
            OSReport("SSS %d hover %d cursor %.2f %.2f stages %d\n", boot_F, hover, xy[0], xy[1], count);
        }
        last_hover = hover;
    }
    show_coll();
    boot_F++;
}

void director_setup_match(StartMeleeData* start)
{
    int i;
    if (dir_boot_mode != GM_DEBUG_VS) {
        return; /* a menu test: the menus chose this match */
    }
    *HSD_RandSeedPtr = dir_setup.seed; /* before stage setup draws from it */
    start->rules.stkind = dir_setup.stage;
    start->rules.match_kind = dir_setup.stocks ? MatchKind_Stock : MatchKind_Time;
    start->rules.timer_enabled = 0;
    start->rules.item_freq = -1;
    start->rules.x1_2 = 1; /* no READY splash */
    start->rules.x1_3 = 1; /* no GO splash; input live at once */
    start->rules.x1_4 = 1; /* never start the stage music */
    start->rules.disable_pausing = 1;
    start->rules.on_match_start = director_match_start;
    start->rules.on_frame_start = director_update;
    for (i = 0; i < 4; i++) {
        if (i < dir_setup.nplayers) {
            start->players[i].ckind = dir_setup.ckind[i];
            start->players[i].color = dir_setup.color[i];
            start->players[i].slot_type = dir_setup.cpu[i] ? Gm_PKind_Cpu : Gm_PKind_Human;
            start->players[i].cpu_level = dir_setup.cpu[i];
            start->players[i].cpu_kind = 4; /* VS mode's CPU (gmvsmode.c) */
            start->players[i].xC_b1 = dir_setup.entry;
            if (dir_setup.stocks) {
                start->players[i].stocks = dir_setup.stocks;
            }
        } else {
            start->players[i].slot_type = Gm_PKind_NA;
        }
        start->players[i].rumble_enabled = 0;
        start->players[i].nametag = 120;
    }
    OSReport("DIRECTOR SETUP stage %d players %d seed %u\n", dir_setup.stage, dir_setup.nplayers, dir_setup.seed);
}

static void director_match_start(void)
{
    int i;
    F = 0;
    done = 0;
    cue_i = 0;
    s_end = dir_len;
    cam_key = -1;
    for (i = 0; i < 4; i++) {
        pad_i[i] = -1;
        pad_cur[i] = NULL;
        last_buttons[i] = 0;
        last_msid[i] = -1;
        last_held[i] = 0;
        last_vis[i] = -1;
        ap_until[i] = -1;
        auto_flags[i] = ff_done[i] = lc_done[i] = 0;
        ff_hold[i] = lc_hold[i] = 0;
        ll_done[i] = ll_ff[i] = 0;
        trace_until[i] = -1;
    }
    if (!dir_setup.stocks) {
        ifAll_HideHUD(); /* films are clean plates; a stock match (a HUD test) keeps it */
    }
    Camera_SetQuakeScale(0.0f);
    if (dir_ncams > 0) {
        Camera_8003006C(); /* debug free camera: the director writes eye, interest and fov every frame */
    } /* else the game's own camera: the match framing players see (dsl Film.game_camera) */
    if (dir_setup.aspect > 0.0f) {
        HSD_CObjSetAspect(GET_COBJ(Camera_80030A50()), dir_setup.aspect);
    }
    lbAudioAx_80025064(0, 1); /* music off, sound effects on (belt and braces with rules.x1_4) */
    OSReport("DIRECTOR START len %d slate %d\n", dir_len, DIR_SLATE);
}

static Fighter* fighter(int port)
{
    HSD_GObj* g = Player_GetEntity(port);
    return g != NULL ? GET_FIGHTER(g) : NULL;
}

static void slate(int on)
{
    Camera_SetStageVisible(!on);
    if (on) {
        Camera_SetBackgroundColor(255, 0, 255);
        gm_SetDbPauseFlag(1);
        lbAudioAx_80024030(1); /* a click at each slate's first frame: the host syncs the game's audio dump to it */
    } else {
        Camera_SetBackgroundColor(0, 0, 0);
        gm_ClearDbPauseFlag(1);
    }
}

static void director_update(void)
{
    int s = F - DIR_SLATE, port, i;
    if (done) {
        return;
    }
    if (F == 0) {
        slate(1);
        if (!dir_setup.entry) {
            for (i = 0; i < dir_setup.nplayers; i++) {
                Fighter* fp = fighter(i);
                if (fp != NULL) {
                    Vec3 p;
                    p.x = dir_setup.x[i];
                    p.y = 0.0f;
                    p.z = 0.0f;
                    ftLib_SetPos(Player_GetEntity(i), &p);
                    fp->facing_dir = (f32) dir_setup.face[i];
                }
            }
        }
    }
    if (F == 1) { /* the fighters' own attributes, from the disc's fighter data: tools/machinima/melee/framedata.py */
        for (i = 0; i < dir_setup.nplayers; i++) {
            Fighter* fp = fighter(i);
            if (fp != NULL) {
                OSReport("ATTR %d %d walk %.4f dash0 %.4f dashmax %.4f jumpsquat %.1f hop %.4f jump %.4f jumph %.4f "
                         "grav %.4f term %.4f ff %.4f drift %.4f airfric %.4f fric %.4f\n",
                         i, fp->kind, fp->co_attrs.walk_max_vel, fp->co_attrs.dash_initial_velocity,
                         fp->co_attrs.dash_max_velocity, fp->co_attrs.jump_startup_time,
                         fp->co_attrs.hop_v_initial_velocity, fp->co_attrs.jump_v_initial_velocity,
                         fp->co_attrs.jump_h_initial_velocity, fp->co_attrs.gravity, fp->co_attrs.terminal_velocity,
                         fp->co_attrs.fast_fall_velocity, fp->co_attrs.air_drift_max, fp->co_attrs.aerial_friction,
                         fp->co_attrs.ground_friction);
                OSReport("LAG %d landing %.0f n %.0f f %.0f b %.0f hi %.0f lw %.0f weight %.0f\n", i,
                         fp->co_attrs.normal_landing_lag, fp->co_attrs.landingairn_lag, fp->co_attrs.landingairf_lag,
                         fp->co_attrs.landingairb_lag, fp->co_attrs.landingairhi_lag, fp->co_attrs.landingairlw_lag,
                         fp->co_attrs.weight);
            }
        }
    }
    if (s == 0) {
        slate(0);
        OSReport("S0 %d\n", F);
    }
    if (s >= 0 && s < s_end) {
        while (cue_i < dir_ncues && dir_cues[cue_i].frame <= s) {
            run_cue(&dir_cues[cue_i]);
            cue_i++;
        }
    }
    if (s == s_end) {
        slate(1);
    }
    /* pads: each port holds its latest entry at or before s (neutral before its first) */
    for (port = 0; port < 4; port++) {
        for (i = pad_i[port] + 1; i < dir_npads; i++) {
            if (dir_pads[i].frame > s) {
                break;
            }
            if (dir_pads[i].port == port) {
                pad_i[port] = i;
                pad_cur[port] = &dir_pads[i];
            }
        }
        if (port < dir_setup.nplayers) {
            put_pad(port, s >= 0 && s < s_end ? pad_cur[port] : NULL);
        }
    }
    /* approach: steer the stick toward the opponent until inside range (2-player films: the opponent is port ^ 1) */
    for (port = 0; port < dir_setup.nplayers && port < 2; port++) {
        if (s >= 0 && s < ap_until[port]) {
            Fighter* me = fighter(port);
            Fighter* op = fighter(port ^ 1);
            if (me != NULL && op != NULL) {
                f32 dx = op->cur_pos.x - me->cur_pos.x;
                s8 st = 0;
                if (dx > ap_range[port]) {
                    st = ap_stick[port];
                } else if (-dx > ap_range[port]) {
                    st = -ap_stick[port];
                }
                HSD_PadGameStatus[port].stickX = st;
                HSD_PadGameStatus[port].nml_stickX = st / 80.0f;
            }
        }
    }
    if (s >= 0 && s < s_end) {
        auto_tech(s);
        for (port = 0; port < dir_setup.nplayers; port++) {
            Fighter* fp = fighter(port);
            if (fp != NULL && s < trace_until[port]) {
                /* and the hip joint's world position: what the eye follows. A ledge action's cur_pos is the ledge plus
                 * TransN, but CliffWait keeps cur_pos at the corner and hangs the body by TransN in the skeleton, so
                 * only the joint shows whether the body jumps between actions */
                MtxPtr m = HSD_JObjGetMtxPtr(fp->parts[ftParts_GetBoneIndex(fp, FtPart_HipN)].joint);
                OSReport("POS %d %d %.2f %.2f %d %.2f %.2f\n", s, port, fp->cur_pos.x, fp->cur_pos.y, fp->motion_id,
                         m[0][3], m[1][3]);
            }
        }
    }
    /* the crowd (sfx/crowdsfx.c): who it chants for (spawn number), the chant's sound id, and its play count (0 while the
     * opening gasp plays, 1..max_gasp_count-1 each time the chant sample restarts, then the closing cheer) */
    if (s >= 0 && s < s_end && crowdsfx_ptr != NULL) {
        CrowdSFX_UnkStruct* c = crowdsfx_ptr;
        if ((s32) c->xC != crowd_last[0] || c->x14 != crowd_last[1] || c->x18 != crowd_last[2]) {
            crowd_last[0] = (s32) c->xC;
            crowd_last[1] = c->x14;
            crowd_last[2] = c->x18;
            OSReport("CROWD %d fighter %d chant %d count %d voice %d\n", s, (int) c->xC, (int) c->x14, (int) c->x18,
                     (int) c->x2C);
        }
    }
    put_camera(s < 0 ? 0 : (s < s_end ? s : s_end - 1));
    /* report motion-state changes: the action timeline the host checks against the script */
    if (s >= 0 && s < s_end) {
        for (port = 0; port < dir_setup.nplayers; port++) {
            Fighter* fp = fighter(port);
            if (fp != NULL && fp->motion_id != last_msid[port]) {
                last_msid[port] = fp->motion_id;
                OSReport("MS %d %d %d %.2f %.2f\n", s, port, fp->motion_id, fp->cur_pos.x, fp->cur_pos.y);
            }
            /* an item taken or let go (the hand's item slot), with the action and its animation frame: an item throw's
             * own release event, to line the throw's key pose up with */
            /* the model's visibility groups (script command 0x1F model mod; an action change reverts them): the option
             * each group shows, when any changes, with the action and its animation frame (-1: the group hidden) */
            if (fp != NULL) {
                s32 v = 0;
                int g, n = fp->x5AC.model_num < 7 ? fp->x5AC.model_num : 7;
                int o[7];
                for (g = 0; g < 7; g++) {
                    o[g] = g < n ? (int) fp->x5F4_arr[g].idx : 9;
                    v |= ((o[g] + 1) & 0xF) << (4 * g);
                }
                if (v != last_vis[port]) {
                    last_vis[port] = v;
                    OSReport("VIS %d %d state %d anim %.2f groups %d %d %d %d %d %d %d\n", s, port, fp->motion_id,
                             fp->cur_anim_frame, o[0], o[1], o[2], o[3], o[4], o[5], o[6]);
                }
            }
            if (fp != NULL && (fp->item_gobj != NULL) != last_held[port]) {
                last_held[port] = fp->item_gobj != NULL;
                OSReport("%s %d %d state %d anim %.2f\n", last_held[port] ? "HOLD" : "LETGO", s, port, fp->motion_id,
                         fp->cur_anim_frame);
            }
        }
    }
    if (s == s_end + DIR_SLATE) {
        OSReport("DIRECTOR END %d\n", F);
        done = 1;
        gm_801A4B60();
    }
    F++;
}

/* aerial attacks are the common motion states AttackAirN..AttackAirLw */
#define IS_AERIAL(fp) ((fp)->motion_id >= 65 && (fp)->motion_id <= 69)

static void auto_tech(int s)
{
    int port;
    (void) s;
    for (port = 0; port < dir_setup.nplayers; port++) {
        Fighter* fp = fighter(port);
        HSD_PadStatus* ps = &HSD_PadGameStatus[port];
        if (fp == NULL || auto_flags[port] == 0) {
            continue;
        }
        if (fp->ground_or_air != GA_Air) {
            ff_done[port] = lc_done[port] = 0;
            ll_done[port] = ll_ff[port] = 0;
            air_frames[port] = 0;
        } else {
            air_frames[port]++;
        }
        /* low laser: B on the 8th airborne frame of a hop. The laser leaves the gun 12 frames later, at about 15 units: the
         * laser lab measured that anything fired before air frame 7 flies over a standing fighter */
        if ((auto_flags[port] & DIR_AUTO_LOWLASER) && fp->ground_or_air == GA_Air && !ll_done[port] &&
            air_frames[port] == 8)
        {
            ll_done[port] = 1;
            ps->button |= 0x200;
            ps->trigger |= 0x200 & ~ps->last_button;
        }
        /* fast fall: a sharp stick-down on the first descending frame of an aerial (the game sees a smash input) */
        if ((auto_flags[port] & DIR_AUTO_FASTFALL) && !ff_done[port] && fp->ground_or_air == GA_Air && IS_AERIAL(fp) &&
            fp->self_vel.y < 0.0f)
        {
            ff_done[port] = 1;
            ff_hold[port] = 2;
        }
        if (ff_hold[port] > 0) {
            ff_hold[port]--;
            ps->stickY = -80;
            ps->nml_stickY = -1.0f;
        }
        /* L-cancel: press a shoulder once the fighter is falling within 6 units of the floor (y = 0): two to four frames
         * before touching down at any fall speed, inside the game's 7-frame window */
        if ((auto_flags[port] & DIR_AUTO_LCANCEL) && !lc_done[port] && fp->ground_or_air == GA_Air && IS_AERIAL(fp) &&
            fp->self_vel.y < 0.0f && fp->cur_pos.y < 6.0f)
        {
            lc_done[port] = 1;
            lc_hold[port] = 2;
        }
        if (lc_hold[port] > 0) {
            lc_hold[port]--;
            ps->button |= 0x20 | 0x80000000; /* R, and the either-shoulder bit */
            ps->trigger |= (0x20 | 0x80000000) & ~ps->last_button;
            ps->analogR = 140;
            ps->nml_analogR = 1.0f;
        }
    }
}

static void put_pad(int port, const DirPad* p)
{
    HSD_PadStatus* ps = &HSD_PadGameStatus[port];
    u32 b = p != NULL ? (p->buttons | (p->trig ? 0x80000000 : 0)) : 0;
    u32 last = last_buttons[port];
    s8 sx = p != NULL ? p->sx : 0, sy = p != NULL ? p->sy : 0;
    s8 cx = p != NULL ? p->cx : 0, cy = p != NULL ? p->cy : 0;
    u8 tr = p != NULL ? p->trig : 0;
    ps->last_button = last;
    ps->button = b;
    ps->trigger = b & ~last;
    ps->release = last & ~b;
    ps->repeat = ps->trigger;
    ps->stickX = sx;
    ps->stickY = sy;
    ps->subStickX = cx;
    ps->subStickY = cy;
    ps->analogL = tr;
    ps->analogR = 0;
    ps->nml_stickX = sx / 80.0f;
    ps->nml_stickY = sy / 80.0f;
    ps->nml_subStickX = cx / 80.0f;
    ps->nml_subStickY = cy / 80.0f;
    ps->nml_analogL = tr / 140.0f;
    ps->nml_analogR = 0.0f;
    ps->err = 0;
    last_buttons[port] = b;
}

static f32 ease(int kind, f32 u)
{
    switch (kind) {
    case DIR_CUT:
        return 0.0f;
    case DIR_IN:
        return u * u * u;
    case DIR_OUT:
        u = 1.0f - u;
        return 1.0f - u * u * u;
    case DIR_INOUT:
        if (u < 0.5f) {
            return 4.0f * u * u * u;
        }
        u = -2.0f * u + 2.0f;
        return 1.0f - u * u * u * 0.5f;
    default:
        return u;
    }
}

static void track_update(int snap)
{
    Vec3 raw[4];
    int i, n = 0;
    raw[DIR_MID].x = raw[DIR_MID].y = raw[DIR_MID].z = 0.0f;
    for (i = 0; i < 2 && i < dir_setup.nplayers; i++) {
        Fighter* fp = fighter(i);
        if (fp != NULL) {
            raw[DIR_P0 + i] = fp->cur_pos;
            raw[DIR_MID].x += fp->cur_pos.x;
            raw[DIR_MID].y += fp->cur_pos.y;
            n++;
        } else {
            raw[DIR_P0 + i] = trk[DIR_P0 + i];
        }
    }
    if (n > 0) {
        raw[DIR_MID].x /= n;
        raw[DIR_MID].y /= n;
    }
    for (i = DIR_MID; i <= DIR_P1; i++) {
        if (snap) {
            trk[i] = raw[i];
        } else { /* critically damped enough for knockback, never jittery */
            trk[i].x += (raw[i].x - trk[i].x) * 0.12f;
            trk[i].y += (raw[i].y - trk[i].y) * 0.08f;
        }
        trk[i].z = 0.0f;
    }
}

static void cam_abs(const DirCam* k, Vec3* eye, Vec3* at)
{
    Vec3 o;
    o.x = o.y = o.z = 0.0f;
    if (k->track != DIR_WORLD) {
        o = trk[k->track];
    }
    eye->x = o.x + k->eye[0];
    eye->y = o.y + k->eye[1];
    eye->z = o.z + k->eye[2];
    at->x = o.x + k->at[0];
    at->y = o.y + k->at[1];
    at->z = o.z + k->at[2];
}

static void put_camera(int s)
{
    int k = 0;
    const DirCam* a;
    const DirCam* b;
    Vec3 ea, aa, eb, ab;
    f32 u = 0.0f;
    if (dir_ncams == 0) {
        /* the game's own camera: log where it is (eye, interest, fov) so a board can place world points on the image */
        HSD_CObj* cobj = GET_COBJ(Camera_80030A50());
        HSD_CObjGetEyePosition(cobj, &ea);
        HSD_CObjGetInterest(cobj, &aa);
        OSReport("CAM %d %.3f %.3f %.3f %.3f %.3f %.3f %.3f\n", s, ea.x, ea.y, ea.z, aa.x, aa.y, aa.z, HSD_CObjGetFov(cobj));
        return;
    }
    while (k + 1 < dir_ncams && dir_cams[k + 1].frame <= s) {
        k++;
    }
    /* snap the trackers on the first frame and whenever a key is entered by a cut */
    track_update(cam_key < 0 || (k != cam_key && dir_cams[k - (k > 0)].ease == DIR_CUT));
    cam_key = k;
    a = &dir_cams[k];
    b = k + 1 < dir_ncams ? &dir_cams[k + 1] : a;
    if (b != a && b->frame > a->frame) {
        u = ease(a->ease, (f32) (s - a->frame) / (f32) (b->frame - a->frame));
    }
    cam_abs(a, &ea, &aa);
    cam_abs(b, &eb, &ab);
    cm_80453004.free_eye_pos.x = ea.x + (eb.x - ea.x) * u;
    cm_80453004.free_eye_pos.y = ea.y + (eb.y - ea.y) * u;
    cm_80453004.free_eye_pos.z = ea.z + (eb.z - ea.z) * u;
    cm_80453004.free_int_pos.x = aa.x + (ab.x - aa.x) * u;
    cm_80453004.free_int_pos.y = aa.y + (ab.y - aa.y) * u;
    cm_80453004.free_int_pos.z = aa.z + (ab.z - aa.z) * u;
    cm_80453004.free_fov = a->fov + (b->fov - a->fov) * u;
    HSD_CObjSetRoll(GET_COBJ(Camera_80030A50()), (a->roll + (b->roll - a->roll) * u) * 0.017453292f);
}

static void run_cue(const DirCue* c)
{
    Fighter* fp = fighter(c->port);
    Vec3 p;
    SpawnItem spawn;
    switch (c->kind) {
    case DIR_FREEZE:
        if (c->a != 0.0f) {
            gm_SetDbPauseFlag(1);
        } else {
            gm_ClearDbPauseFlag(1);
        }
        break;
    case DIR_STAGE:
        Camera_SetStageVisible(c->a != 0.0f);
        break;
    case DIR_BGCOLOR:
        Camera_SetBackgroundColor((u8) c->a, (u8) c->b, (u8) c->c);
        break;
    case DIR_SETPOS:
        p.x = c->a;
        p.y = c->b;
        p.z = 0.0f;
        ftLib_SetPos(Player_GetEntity(c->port), &p);
        if (fp != NULL) {
            /* a teleport: collision sweeps from the previous positions, so a jump across the stage's edge pushed the
             * fighter back onto it; start every sweep here, with no momentum */
            fp->prev_pos = p;
            fp->coll_data.cur_pos = p;
            fp->coll_data.prev_pos = p;
            fp->coll_data.last_pos = p;
            fp->self_vel.x = fp->self_vel.y = 0.0f;
        }
        break;
    case DIR_FACE:
        if (fp != NULL) {
            fp->facing_dir = c->a;
        }
        break;
    case DIR_MOTION:
        Fighter_ChangeMotionState(Player_GetEntity(c->port), (FtMotionId) c->a, 0, c->b, 1.0f, 0.0f, NULL);
        break;
    case DIR_PERCENT:
        ftLib_SetPercent(Player_GetEntity(c->port), (s32) c->a);
        break;
    case DIR_MARK:
        OSReport("MARK %d %d\n", c->frame, (int) c->a);
        break;
    case DIR_END:
        s_end = c->frame;
        break;
    case DIR_APPROACH:
        ap_range[c->port] = c->a;
        ap_until[c->port] = (int) c->b;
        ap_stick[c->port] = (s8) c->c;
        break;
    case DIR_AUTO:
        auto_flags[c->port] = (u8) c->a;
        break;
    case DIR_TRACE:
        trace_until[c->port] = (int) c->a;
        break;
    case DIR_STATUS:
        if (fp != NULL) {
            OSReport("STATUS %d %d %.1f %.2f %.2f %d\n", F - DIR_SLATE, c->port, fp->dmg.x1830_percent, fp->cur_pos.x,
                     fp->cur_pos.y, fp->motion_id);
        }
        break;
    case DIR_SHIELD:
        if (fp != NULL) {
            /* the guard's collision shield is a unit sphere on ThrowN (the lookup table's byte 0x11), so its world radius is
             * the joint matrix's scale; hurtbox radii are world units times the fighter's scale */
            MtxPtr m = HSD_JObjGetMtxPtr(fp->parts[fp->ft_data->x8->x11].joint);
            float sc = sqrtf(m[0][0] * m[0][0] + m[1][0] * m[1][0] + m[2][0] * m[2][0]);
            int k;
            OSReport("SHIELD %d %d motion %d health %.1f centre %.2f %.2f %.2f radius %.2f scale %.3f pos %.2f %.2f\n",
                     F - DIR_SLATE, c->port, fp->motion_id, fp->shield_health, m[0][3], m[1][3], m[2][3], sc,
                     fp->x34_scale.y, fp->cur_pos.x, fp->cur_pos.y);
            for (k = 0; k < fp->hurt_capsules_len; k++) {
                HurtCapsule* h = &fp->hurt_capsules[k].capsule;
                OSReport("HURT %d %d %d %.2f %.2f %.2f %.2f %.2f %.2f %.2f\n", F - DIR_SLATE, c->port, k, h->a_pos.x,
                         h->a_pos.y, h->a_pos.z, h->b_pos.x, h->b_pos.y, h->b_pos.z, h->scale);
            }
        }
        break;
    case DIR_FEET:
        if (fp != NULL) {
            int side;
            for (side = 0; side < 2; side++) {
                int j = side == 0 ? fp->ft_data->x8->x13 : fp->ft_data->x8->x14;
                MtxPtr m = HSD_JObjGetMtxPtr(fp->parts[j].joint);
                OSReport("FEET %d %d %d %.3f %.3f %.3f %.4f %.4f %.4f %.4f %.4f %.4f %d %.3f\n", F - DIR_SLATE, c->port, side,
                         m[0][3], m[1][3], m[2][3], m[0][0], m[1][0], m[2][0], m[0][1], m[1][1], m[2][1], fp->motion_id,
                         fp->cur_anim_frame);
            }
        }
        break;
    case DIR_SHIELDHP:
        if (fp != NULL) {
            fp->shield_health = c->a;
        }
    case DIR_ITEM:
        /* the game's own drop (itdrop.c): an item at rest where it lands, facing the stage's centre */
        memset(&spawn, 0, sizeof(spawn));
        spawn.kind = (ItemKind) c->a;
        spawn.prev_pos.x = c->b;
        spawn.prev_pos.y = c->c;
        spawn.prev_pos.z = 0.0f;
        spawn.pos = spawn.prev_pos;
        spawn.facing_dir = it_8026B684(&spawn.prev_pos);
        spawn.x44_flag.b0 = 1;
        OSReport("ITEM %d kind %d at %.1f %.1f %s\n", F - DIR_SLATE, (int) c->a, c->b, c->c,
                 Item_80268B18(&spawn) != NULL ? "ok" : "failed");
        break;
    case DIR_ANIM:
        if (fp != NULL) {
            ftCo_8008A6D8(Player_GetEntity(c->port), (s32) c->a);
            OSReport("ANIM %d %d entry %d state %d\n", F - DIR_SLATE, c->port, (int) c->a, fp->motion_id);
        }
        break;
    case DIR_SFX:
        OSReport("SFX %d id %d voice %d\n", F - DIR_SLATE, (int) c->a,
                 lbAudioAx_800237A8((int) c->a, c->b > 0.0f ? (int) c->b : 0x7F, 0x40));
        break;
    case DIR_SHOOT:
        if (fp != NULL) {
            int packed = (int) c->a;
            int kind = (packed & 4095) >> 4, state = packed & 15;
            f32 speed = (f32) (packed >> 12) / 10.0f;
            p = fp->cur_pos;
            p.x += fp->facing_dir * c->b;
            p.y += c->c;
            p.z = 0.0f;
            it_8029C504(Player_GetEntity(c->port), &p, state, kind, fp->facing_dir < 0.0f ? 3.14159265f : 0.0f, speed);
            OSReport("SHOOT %d %d kind %d state %d %.2f %.2f %.1f\n", F - DIR_SLATE, c->port, kind, state, p.x, p.y, speed);
        }
        break;
    case DIR_ITEMS: {
        HSD_GObj* ig;
        for (ig = HSD_GObjPLinkHead[HSD_GOBJ_PLINK_ITEM]; ig != NULL; ig = ig->next) {
            Item* ip = (Item*) ig->user_data;
            OSReport("ITEMS %d kind %d %.2f %.2f\n", F - DIR_SLATE, (int) ip->kind, ip->pos.x, ip->pos.y);
        }
        break;
    }
    case DIR_GRDUMP: {
        MapCollData* cd = mpLib_8004D164();
        CollLine* ln = mpGetGroundCollLine();
        CollVtx* vx = mpGetGroundCollVtx();
        int k;
        OSReport("STAGE %d grkind %d stkind %d blast %.3f %.3f %.3f %.3f cam %.3f %.3f %.3f %.3f offset %.3f %.3f\n",
                 F - DIR_SLATE, (int) stage_info.grkind, (int) Stage_80225194(), Stage_GetBlastZoneLeftOffset(),
                 Stage_GetBlastZoneRightOffset(), Stage_GetBlastZoneTopOffset(), Stage_GetBlastZoneBottomOffset(),
                 Stage_GetCamBoundsLeftOffset(), Stage_GetCamBoundsRightOffset(), Stage_GetCamBoundsTopOffset(),
                 Stage_GetCamBoundsBottomOffset(), stage_info.cam_info.cam_x_offset, stage_info.cam_info.cam_y_offset);
        if (cd != NULL && ln != NULL && vx != NULL) {
            for (k = 0; k < cd->line_count; k++) {
                MapLine* m = ln[k].x0;
                if (m == NULL || (c->a == 0 && (ln[k].flags & LINE_FLAG_KIND) != 1)) {
                    continue;
                }
                OSReport("LINE %d %d %X %X %.3f %.3f %.3f %.3f\n", F - DIR_SLATE, k, (unsigned) ln[k].flags,
                         (unsigned) m->lo_flags, vx[m->v0_idx].pos.x, vx[m->v0_idx].pos.y, vx[m->v1_idx].pos.x,
                         vx[m->v1_idx].pos.y);
            }
        }
        for (k = 0; k < dir_setup.nplayers; k++) {
            Fighter* fk = fighter(k);
            if (fk != NULL) {
                /* the ledge line held, in the cliff states (CliffCatch 252 .. CliffJumpQuick2 263) */
                int ledge = (fk->motion_id >= 252 && fk->motion_id <= 263) ? (int) fk->mv.co.cliff.ledge_id : -1;
                OSReport("GROUND %d %d %.3f %.3f %d %d %d %d\n", F - DIR_SLATE, k, fk->cur_pos.x, fk->cur_pos.y,
                         (int) fk->ground_or_air, (int) fk->coll_data.floor.index, fk->motion_id, ledge);
            }
        }
        break;
    }
    case DIR_RESET:
        if (fp != NULL && fp->motion_id <= 13) {
            /* dead (0-11) or on the respawn platform (Rebirth, RebirthWait): forcing them onto the ground asserts
             * ("fighter ground no under Id") and freezes the game, so skip and say so */
            OSReport("RESET SKIPPED %d %d state %d\n", F - DIR_SLATE, c->port, fp->motion_id);
        } else if (fp != NULL) {
            HSD_GObj* g = Player_GetEntity(c->port);
            p.x = c->a;
            p.y = 0.0f;
            p.z = 0.0f;
            ftLib_SetPos(g, &p);
            fp->prev_pos = p;
            /* as for setpos: collision sweeps from the previous positions, so a reset from under a ledge (hanging on it)
             * swept into the stage and dropped the fighter back below it */
            fp->coll_data.cur_pos = p;
            fp->coll_data.prev_pos = p;
            fp->coll_data.last_pos = p;
            fp->self_vel.x = fp->self_vel.y = fp->self_vel.z = 0.0f;
            fp->x8c_kb_vel.x = fp->x8c_kb_vel.y = fp->x8c_kb_vel.z = 0.0f;
            fp->gr_vel = 0.0f;
            fp->xF0_ground_kb_vel = 0.0f;
            fp->facing_dir = c->b;
            plStale_ResetStaleMoveTableForPlayer(c->port); /* fresh moves: a lab repeats one, and staling weakens it */
            if (fp->x1990 != 0 || fp->x1994 != 0) { /* respawn invincibility (and its flashing) would carry into the test */
                fp->x1990 = fp->x1994 = 0;
                fp->x198C = 0;
                if (ftCo_800C0694(fp) == 9) {
                    ftCo_800C0200(fp, 9);
                }
            }
            if (fp->ground_or_air == GA_Air) {
                ftCommon_8007D7FC(fp);
            }
            ft_8008A2BC(g);
        }
        break;
    }
}

void director_on_hit(Fighter_GObj* attacker, Fighter_GObj* victim, float dmg)
{
    Fighter* a = GET_FIGHTER(attacker);
    Fighter* v = GET_FIGHTER(victim);
    OSReport("HIT %d %d %d %.1f %d\n", F - DIR_SLATE, a->player_idx, v->player_idx, dmg, a->x2070.x2073);
}

void director_on_item_hit(HSD_GObj* item, Fighter_GObj* victim, float dmg)
{
    Fighter* v = GET_FIGHTER(victim);
    (void) item;
    OSReport("IHIT %d %d %.1f\n", F - DIR_SLATE, v->player_idx, dmg);
}

void director_on_laser(HSD_GObj* parent, Vec3* pos, int kind, float angle, float speed)
{
    Fighter* fp = GET_FIGHTER(parent);
    (void) kind;
    OSReport("LASER %d %d %.2f %.2f %.3f %.2f\n", F - DIR_SLATE, fp->player_idx, pos->x, pos->y, angle, speed);
}
