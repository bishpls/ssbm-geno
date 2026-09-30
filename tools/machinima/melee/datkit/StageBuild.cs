// stage-build SPEC.json TEMPLATE_GrXx.dat OUT.dat : a stage file from a stage spec (projects/geno/stage/stage_spec.py).
// The template (Battlefield's GrNBa.dat) supplies what the spec doesn't: grGroundParam's camera fields and per-StKind row
// layout (item weights), the map lights (map_head, each gobj's light set), the fighters' lights (map_plit), the stage
// camera descs and ALDYakuAll / itemdata / quake_model_set. Everything the spec gives is written fresh:
//   - coll_data: vertices, lines (engine order, prev at +4 and next at +6, surface / property / material), one line group;
//   - the general points: a joint tree (root = 0, one child per point) and its (index, type) list, as map gobj 0;
//   - map gobjs from the spec's faces: one joint, one DObj per colour, flat-shaded lit material colours (RENDER_DIFFUSE,
//     ambient half the diffuse), rigid PObjs (position + normal), drawn both sides; a gobj may carry its own fog;
//   - grGroundParam: stage scale and one per-StKind row (the stage's music), cloned from the template's VS row.
// Dropped from the template: its models and textures, map_ptcl/map_texg (its particle bank) and yakumono_param.
// Verification is stage-dump on the output (the same numbers as the spec) and the director's grdump in game.
using System.Globalization;
using System.Numerics;
using System.Text.Json;
using HSDRaw;
using HSDRaw.Common;
using HSDRaw.GX;
using HSDRaw.Melee.Gr;
using HSDRaw.Tools;

static class StageBuild
{
    static float F(JsonElement e) => (float)e.GetDouble();

    public static int Run(string[] a)
    {
        if (a.Length < 4) { Console.Error.WriteLine("usage: stage-build SPEC.json TEMPLATE.dat OUT.dat"); return 2; }
        var spec = JsonDocument.Parse(File.ReadAllText(a[1])).RootElement;
        var f = new HSDRawFile(a[2]);
        HSDAccessor Root(string n) => f.Roots.FirstOrDefault(r => r.Name == n)?.Data;
        var gp = Root("grGroundParam") as SBM_GroundParam;
        var head = Root("map_head") as SBM_Map_Head;
        float scale = F(spec.GetProperty("scale"));
        var log = new List<string>();

        // ---- collision
        var cs = spec.GetProperty("collision");
        var verts = cs.GetProperty("vertices").EnumerateArray().Select(v => new SBM_CollVertex { X = F(v[0]) / scale, Y = F(v[1]) / scale }).ToArray();
        var lines = new List<SBM_CollLine>();
        foreach (var l in cs.GetProperty("lines").EnumerateArray())
        {
            var v = l.GetProperty("v");
            var cl = new SBM_CollLine
            {
                VertexIndex1 = (short)v[0].GetInt32(), VertexIndex2 = (short)v[1].GetInt32(),
                NextLine = (short)l.GetProperty("prev").GetInt32(),          // +4: the engine's prev_id0 (HSDRaw's name is swapped)
                PreviousLine = (short)l.GetProperty("next").GetInt32(),      // +6: next_id0
                NextLineAltGroup = -1, PreviousLineAltGroup = -1,
                CollisionFlag = (CollPhysics)l.GetProperty("surface").GetInt32(),
                Flag = (l.GetProperty("drop").GetBoolean() ? CollProperty.DropThrough : 0) | (l.GetProperty("ledge").GetBoolean() ? CollProperty.LedgeGrab : 0),
                Material = (CollMaterial)l.GetProperty("material").GetInt32(),
            };
            lines.Add(cl);
        }
        var g = cs.GetProperty("group"); var rg = g.GetProperty("ranges"); var bd = g.GetProperty("bounds");
        short S(JsonElement e, int i) => (short)e[i].GetInt32();
        var grp = new SBM_CollLineGroup
        {
            TopLineIndex = S(rg.GetProperty("floor"), 0), TopLineCount = S(rg.GetProperty("floor"), 1),
            BottomLineIndex = S(rg.GetProperty("ceiling"), 0), BottomLineCount = S(rg.GetProperty("ceiling"), 1),
            RightLineIndex = S(rg.GetProperty("right_wall"), 0), RightLineCount = S(rg.GetProperty("right_wall"), 1),
            LeftLineIndex = S(rg.GetProperty("left_wall"), 0), LeftLineCount = S(rg.GetProperty("left_wall"), 1),
            DynamicLineIndex = 0, DynamicLineCount = 0,
            XMin = F(bd[0]) / scale, YMin = F(bd[1]) / scale, XMax = F(bd[2]) / scale, YMax = F(bd[3]) / scale,
            VertexStart = S(g.GetProperty("vertices"), 0), VertexCount = S(g.GetProperty("vertices"), 1),
        };
        var coll = new SBM_Coll_Data();
        coll.Vertices = verts; coll.Links = lines.ToArray(); coll.LineGroups = new[] { grp };
        coll._s.SetInt32(0x04, verts.Length); coll._s.SetInt32(0x0C, lines.Count); coll._s.SetInt32(0x28, 1);
        coll.TopLinksOffset = grp.TopLineIndex; coll.TopLinksCount = grp.TopLineCount;
        coll.BottomLinksOffset = grp.BottomLineIndex; coll.BottomLinksCount = grp.BottomLineCount;
        coll.RightLinksOffset = grp.RightLineIndex; coll.RightLinksCount = grp.RightLineCount;
        coll.LeftLinksOffset = grp.LeftLineIndex; coll.LeftLinksCount = grp.LeftLineCount;
        coll.DynamicLinksOffset = 0; coll.DynamicLinksCount = 0;
        log.Add($"collision: {verts.Length} vertices, {lines.Count} lines (floor {grp.TopLineCount}, ceiling {grp.BottomLineCount}, right {grp.RightLineCount}, left {grp.LeftLineCount})");

        // ---- map gobjs
        var tplGobjs = head.ModelGroups.Array;
        var tplStage = tplGobjs[tplGobjs.Length - 1];               // Battlefield's play plane: its lights and camera
        var gobjs = new List<SBM_Map_GOBJ>();
        HSD_JOBJ pointsRoot = null;
        SBM_GeneralPointInfo[] pointInfo = null;
        foreach (var go in spec.GetProperty("gobjs").EnumerateArray())
        {
            var kind = go.GetProperty("kind").GetString();
            var mg = new SBM_Map_GOBJ { Camera = tplStage.Camera, Lights = tplStage.Lights };
            if (kind == "points")
            {
                pointsRoot = new HSD_JOBJ { Flags = JOBJ_FLAG.CLASSICAL_SCALING, SX = 1, SY = 1, SZ = 1 };
                var infos = new List<SBM_GeneralPointInfo>(); HSD_JOBJ prev = null; short idx = 1;
                foreach (var p in spec.GetProperty("points").EnumerateArray())
                {
                    var j = new HSD_JOBJ { Flags = JOBJ_FLAG.CLASSICAL_SCALING, SX = 1, SY = 1, SZ = 1, TX = F(p.GetProperty("x")) / scale, TY = F(p.GetProperty("y")) / scale };
                    if (prev == null) pointsRoot.Child = j; else prev.Next = j;
                    prev = j;
                    infos.Add(new SBM_GeneralPointInfo { JOBJIndex = idx++, Type = (PointType)p.GetProperty("type").GetInt32() });
                }
                pointInfo = infos.ToArray();
                mg.RootNode = pointsRoot;
                log.Add($"gobj {gobjs.Count}: {infos.Count} general points");
            }
            else
            {
                var root = new HSD_JOBJ { Flags = JOBJ_FLAG.CLASSICAL_SCALING, SX = 1, SY = 1, SZ = 1 };
                var mesh = new HSD_JOBJ { Flags = JOBJ_FLAG.CLASSICAL_SCALING | JOBJ_FLAG.LIGHTING | JOBJ_FLAG.OPA, SX = 1, SY = 1, SZ = 1 };
                root.Child = mesh;
                // one DObj per colour
                var byCol = new Dictionary<string, List<GX_Vertex>>();
                int tris = 0;
                foreach (var face in go.GetProperty("faces").EnumerateArray())
                {
                    var c = face.GetProperty("color"); var key = $"{c[0].GetInt32()},{c[1].GetInt32()},{c[2].GetInt32()}";
                    var n = face.GetProperty("normal");
                    var nv = new GXVector3(F(n[0]), F(n[1]), F(n[2]));
                    if (!byCol.TryGetValue(key, out var list)) byCol[key] = list = new();
                    foreach (var t in face.GetProperty("tris").EnumerateArray())
                    {
                        foreach (var p in t.EnumerateArray())
                            list.Add(new GX_Vertex { POS = new GXVector3(F(p[0]) / scale, F(p[1]) / scale, F(p[2]) / scale), NRM = nv });
                        tris++;
                    }
                }
                HSD_DOBJ prevD = null;
                foreach (var (key, list) in byCol)
                {
                    var rgb = key.Split(',').Select(byte.Parse).ToArray();
                    var mo = new HSD_MOBJ { RenderFlags = RENDER_MODE.DIFFUSE, Material = new HSD_Material() };
                    var mt = mo.Material;
                    mt.DIF_R = rgb[0]; mt.DIF_G = rgb[1]; mt.DIF_B = rgb[2]; mt.DIF_A = 255;
                    mt.AMB_R = (byte)(rgb[0] / 2); mt.AMB_G = (byte)(rgb[1] / 2); mt.AMB_B = (byte)(rgb[2] / 2); mt.AMB_A = 255;
                    mt.SPC_R = mt.SPC_G = mt.SPC_B = 0; mt.SPC_A = 255; mt.Alpha = 1; mt.Shininess = 50;
                    var gen = new POBJ_Generator { CullMode = GenCullMode.None };
                    var po = gen.CreatePOBJsFromTriangleList(list, new[] { GXAttribName.GX_VA_POS, GXAttribName.GX_VA_NRM }, null, null);
                    gen.SaveChanges();
                    var d = new HSD_DOBJ { Mobj = mo, Pobj = po };
                    if (prevD == null) mesh.Dobj = d; else prevD.Next = d;
                    prevD = d;
                }
                root.UpdateFlags();
                mg.RootNode = root;
                if (go.TryGetProperty("fog", out var fog))
                {
                    var fd = HSDAccessor.DeepClone<HSD_FogDesc>(tplGobjs.First(x => x.Fog != null).Fog);
                    fd.Start = F(fog.GetProperty("start")); fd.End = F(fog.GetProperty("end"));
                    var fc = fog.GetProperty("color");
                    fd.Color = System.Drawing.Color.FromArgb(255, fc[0].GetInt32(), fc[1].GetInt32(), fc[2].GetInt32());
                    mg.Fog = fd;
                }
                log.Add($"gobj {gobjs.Count} ({kind}): {byCol.Count} DObjs, {tris} triangles{(mg.Fog != null ? ", fog" : "")}");
            }
            gobjs.Add(mg);
        }
        head.ModelGroups = new HSDArrayAccessor<SBM_Map_GOBJ> { Array = gobjs.ToArray() };
        var gpts = new SBM_GeneralPoints { JOBJReference = pointsRoot };
        gpts.Points = pointInfo;
        head.GeneralPoints = new HSDArrayAccessor<SBM_GeneralPoints> { Array = new[] { gpts } };

        // ---- grGroundParam
        gp.StageScale = scale;
        var sp = spec.GetProperty("stage_param");
        var vsRow = gp.BGMData.First(b => b.GrKind < 0x21);          // the template's VS row: item weights and layout
        var row = HSDAccessor.DeepClone<SBM_GroundBGM>(vsRow);
        row.GrKind = sp.GetProperty("st_kind").GetInt32();           // HSDRaw's name; the engine's StageParam.stkind
        row.MainMusic = sp.GetProperty("bgm").GetInt32(); row.AltMusic = sp.GetProperty("bgm_alt").GetInt32();
        row.SuddenDeathMainMusic = sp.GetProperty("bgm_sd").GetInt32(); row.SuddenDeathAltMusic = sp.GetProperty("bgm_sd_alt").GetInt32();
        row.SongBehaviorFlag = (short)sp.GetProperty("behaviour").GetInt32(); row.ChanceToPlayAltSong = (short)sp.GetProperty("alt_chance").GetInt32();
        gp.BGMData = new[] { row };
        log.Add($"grGroundParam: scale {scale}, one stage row (StKind 0x{row.GrKind:X}, music {row.MainMusic})");

        // ---- roots
        var coll0 = f.Roots.First(r => r.Name == "coll_data"); coll0.Data = coll;
        var drop = new HashSet<string> { "map_ptcl", "map_texg", "yakumono_param" };
        f.Roots.RemoveAll(r => drop.Contains(r.Name) || r.Name.EndsWith("_image") || r.Name.EndsWith("_tlut") || r.Name.EndsWith("_tlut_desc"));
        f.Save(a[3]);
        foreach (var s in log) Console.WriteLine(s);
        Console.WriteLine($"wrote {a[3]} ({new FileInfo(a[3]).Length} bytes); roots {string.Join(", ", f.Roots.Select(r => r.Name))}");
        return 0;
    }
}
