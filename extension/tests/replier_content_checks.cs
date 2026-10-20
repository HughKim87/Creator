using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Net;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using ReplierDesktop;

public static class ContentChecks
{
    static void Check(bool condition, string name) { if (!condition) throw new Exception(name); Console.WriteLine("PASS " + name); }
    static object Player(string id, object[] tracks, string status = "OK")
    {
        var json = new JavaScriptSerializer().Serialize(new {
            videoDetails = new { videoId = id }, playabilityStatus = new { status = status },
            captions = new { playerCaptionsTracklistRenderer = new { captionTracks = tracks } }
        });
        return new JavaScriptSerializer().DeserializeObject(json);
    }
    static object Track(string language, string kind)
    {
        return new { languageCode = language, kind = kind, baseUrl = "https://www.youtube.com/api/timedtext?v=HPUpsEzL1ps&fmt=srv3" };
    }

    [STAThread]
    public static int Main(string[] args)
    {
        try
        {
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
            string folder = Path.Combine(args[0], "run-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(folder);
            const string id = "HPUpsEzL1ps";
            var cues = CaptionService.ParseCues("{\"events\":[{\"tStartMs\":520,\"dDurationMs\":3000,\"segs\":[{\"utf8\":\"첫 대사\\n입니다\"}]},{\"tStartMs\":520,\"segs\":[{\"utf8\":\"첫 대사 입니다\"}]},{\"tStartMs\":9519,\"segs\":[{\"utf8\":\"첫 대사 입니다\"}]}]}");
            Check(cues.Count == 2 && cues[0].Text == "첫 대사 입니다" && cues[1].StartMs == 9519, "deduplicate exact cues while retaining later repeated speech");
            Check(CaptionService.Timestamp(9519) == "00:00:09.519", "millisecond timestamp retained");
            bool rejected = false;
            try { CaptionService.ParseCues("{\"events\":[]}"); } catch (ContentUnavailable) { rejected = true; }
            Check(rejected, "empty transcript cannot be completed");
            rejected = false;
            try { CaptionService.ParseCues("{\"events\":[{\"tStartMs\":-1,\"segs\":[{\"utf8\":\"bad\"}]}]}"); } catch (InvalidDataException) { rejected = true; }
            Check(rejected, "invalid cue timing rejected");
            var player = Player(id, new[] { Track("en", ""), Track("ko", "asr"), Track("ko", "") });
            Check((string)CaptionService.Get(CaptionService.SelectTrack(player, id), "kind") == "", "prefer Korean creator captions over automatic captions");
            rejected = false;
            try { CaptionService.SelectTrack(player, "ABCDEFGHIJ1"); } catch (ContentUnavailable) { rejected = true; }
            Check(rejected, "different video ID rejected");
            rejected = false;
            try { CaptionService.SelectTrack(Player(id, new object[0]), id); } catch (ContentUnavailable) { rejected = true; }
            Check(rejected, "no-caption status distinct from success");
            rejected = false;
            try { CaptionService.SelectTrack(Player(id, new object[0], "LOGIN_REQUIRED"), id); } catch (ContentUnavailable) { rejected = true; }
            Check(rejected, "restricted video cannot be completed");
            Check(CaptionService.CaptionUrl("https://www.youtube.com/api/timedtext?v=" + id + "&fmt=srv3").Query.Contains("fmt=json3"), "replace existing format without duplicate parameter");
            rejected = false;
            try { CaptionService.CaptionUrl("https://example.com/api/timedtext"); } catch (ContentUnavailable) { rejected = true; }
            Check(rejected, "external caption URL rejected");
            rejected = false;
            try { CaptionService.CaptionUrl("https://www.youtube.com/api/timedtext?v=ABCDEFGHIJ1", id); } catch (ContentUnavailable) { rejected = true; }
            Check(rejected, "caption address bound to the found video ID");

            var video = new Video { Id = id, Title = "스팀평가 매우긍정적 이상! 꿀잼 인디게임 추천 14종", Channel = "겜생각" };
            var live = CaptionService.Fetch(video, CancellationToken.None).GetAwaiter().GetResult();
            Check(live.VideoId == id && live.Language == "ko" && live.Cues.Count > 0 && live.Cues[0].StartMs >= 0, "real Korean captions and timecodes acquired");
            var store = new ContentStore(Path.Combine(folder, "content"));
            store.Save(live);
            var loaded = new ContentStore(Path.Combine(folder, "content")).Load(id);
            Check(loaded.Cues.Count == live.Cues.Count && loaded.Cues[0].Text == live.Cues[0].Text && loaded.Source == "YouTube 공개 자막", "content source and speech survive reload");
            rejected = false;
            try { ContentStore.Validate(live, "ABCDEFGHIJ1"); } catch (InvalidDataException) { rejected = true; }
            Check(rejected, "saved captions cannot bind to another video");
            rejected = false;
            try { store.Load("../invalid"); } catch (ArgumentException) { rejected = true; }
            Check(rejected, "invalid cache path rejected");

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Exception error = null;
            using (var form = new ContentForm(video, store, false))
            {
                form.Opacity = 0;
                form.ShowInTaskbar = false;
                form.Shown += async (sender, e) => {
                    try
                    {
                        await form.LoadContent(false);
                        var grid = (DataGridView)form.Controls.Find("CaptionCues", true)[0];
                        Check(grid.Rows.Count == live.Cues.Count, "native viewer displays stored real speech");
                        Check(((Label)form.Controls.Find("ContentStatus", true)[0]).Text.Contains("저장된 자막"), "cached source explicitly labeled");
                        await form.LoadContent(true);
                        Check(grid.Rows.Count > 0 && ((Label)form.Controls.Find("ContentStatus", true)[0]).Text.Contains("실제 자막 확보 완료"), "native viewer refreshes actual captions");
                        Check(grid.SelectedRows.Count == 0 && !((Button)form.Controls.Find("OpenCue", true)[0]).Enabled, "no automatic video playback");
                        Check(((Button)form.Controls.Find("RefreshContent", true)[0]).Enabled, "controls restored after caption acquisition");
                        using (var image = new Bitmap(form.Width, form.Height))
                        {
                            form.DrawToBitmap(image, new Rectangle(0, 0, image.Width, image.Height));
                            image.Save(Path.Combine(args[0], "content-stage3-preview.png"), ImageFormat.Png);
                        }
                    }
                    catch (Exception ex) { error = ex; }
                    finally { form.Close(); }
                };
                Application.Run(form);
            }
            if (error != null) throw error;
            return 0;
        }
        catch (Exception ex) { Console.Error.WriteLine(ex.GetType().Name + ": " + ex.Message); return 1; }
    }
}
