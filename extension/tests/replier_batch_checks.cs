using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using ReplierDesktop;

public static class BatchChecks
{
    static void Check(bool ok, string name) { if (!ok) throw new Exception(name); Console.WriteLine("PASS " + name); }
    static Video V(int n) { return new Video { Id = "V" + n.ToString("D10"), Title = "fixture " + n, Channel = "test" }; }
    static VideoContent C(Video v) { return new VideoContent {
        Version = 1, VideoId = v.Id, Language = "ko", IsAuto = true, Source = "YouTube 공개 자막", AcquiredAt = DateTime.UtcNow.ToString("o"),
        Cues = new List<CaptionCue> { new CaptionCue { StartMs = 1000, DurationMs = 1000, Text = "합성 검사 대사" } } }; }
    static Task<VideoContent> Good(Video v, CancellationToken token) { return Task.FromResult(C(v)); }

    [STAThread]
    public static int Main(string[] args)
    {
        try
        {
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
            string output = args[0];
            Directory.CreateDirectory(output);
            string run = Path.Combine(output, "run-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(run);
            var options = new List<Topic> { new Topic { Term = "실제후보1" }, new Topic { Term = "실제후보2" } };
            Check(Enumerable.Range(0, 50).All(i => options.Contains(TopicPicker.Pick(options))), "random choice uses only supplied actual topic candidates");
            bool empty = false;
            try { TopicPicker.Pick(new List<Topic>()); } catch (InvalidDataException) { empty = true; }
            Check(empty, "no invented fallback topic");

            var ledger = new VideoLedger(Path.Combine(run, "videos.jsonl"));
            var store = new ContentStore(Path.Combine(run, "content"));
            var candidates = Enumerable.Range(0, 18).Select(V).ToList();
            candidates.Insert(1,V(0));
            ledger.ClaimFirst(new[] { V(0) }, "old");
            int seenDuplicateFetch = 0;
            Func<Video, CancellationToken, Task<VideoContent>> fetch = (v, token) => {
                if (v.Id == V(0).Id) Interlocked.Increment(ref seenDuplicateFetch);
                if (v.Id == V(1).Id || v.Id == V(2).Id) throw new ContentUnavailable("no captions");
                return Good(v, token);
            };
            var batch = VideoBatch.Collect("one keyword", ledger, store, CancellationToken.None, null,
                (q, t) => Task.FromResult(candidates), fetch).GetAwaiter().GetResult();
            Check(batch.Videos.Count == 10, "return exactly ten when enough captioned candidates exist");
            Check(batch.Videos.Count(v=>v.Id==V(0).Id)==2 && seenDuplicateFetch>0, "prior IDs and duplicate input rows remain eligible");
            Check(batch.NoCaptions == 2 && batch.Videos.All(v => v.Id != V(1).Id && v.Id != V(2).Id), "missing captions excluded from results");
            Check(batch.Videos.All(v => store.Load(v.Id).Cues.Count > 0), "every displayed candidate has persisted validated content");
            var selectedIds = ledger.ReadIds();
            Check(selectedIds.SetEquals(new[]{V(0).Id}), "selection history is not modified");
            var again = VideoBatch.Collect("different keyword", new VideoLedger(Path.Combine(run, "videos.jsonl")), store, CancellationToken.None, null,
                (q, t) => Task.FromResult(candidates), fetch).GetAwaiter().GetResult();
            Check(again.Videos.Select(v => v.Id).SequenceEqual(batch.Videos.Select(v => v.Id)), "changed query returns previously displayed videos again");
            Check(again.Videos.Count == 10, "repeat search can still return ten");
            var retry = VideoBatch.Collect("retry", ledger, store, CancellationToken.None, null,
                (q,t) => Task.FromResult(new List<Video> { V(1) }), Good).GetAwaiter().GetResult();
            Check(retry.Videos.Count == 1, "temporarily failed caption is not permanently excluded");

            var historyBefore = File.ReadAllText(Path.Combine(run, "videos.jsonl"));
            for (int repeat=0;repeat<2;repeat++)
            {
                var repeated = VideoBatch.Collect("trending", ledger, store, CancellationToken.None,
                    search:(q,t)=>Task.FromResult(new List<Video>{V(0),V(0),V(98)}), captions:Good).GetAwaiter().GetResult();
                Check(repeated.Videos.Count==3 && repeated.Videos.Any(v=>v.Id==V(0).Id),
                    "trending repeat "+repeat+" retains previously seen and repeated rows");
            }
            Check(File.ReadAllText(Path.Combine(run,"videos.jsonl"))==historyBefore,
                "trending leaves normal search history unchanged");
            var noLedger = VideoBatch.Collect("trending", null, store, CancellationToken.None,
                search:(q,t)=>Task.FromResult(new List<Video>{V(0)}), captions:Good).GetAwaiter().GetResult();
            Check(noLedger.Videos.Count==1,"trending does not access permanent ledger");
            string lockedHistory=Path.Combine(run,"unreadable-history.jsonl");File.WriteAllText(lockedHistory,"not valid history");
            using(var historyLock=new FileStream(lockedHistory,FileMode.Open,FileAccess.ReadWrite,FileShare.None))
            foreach(string mode in new[]{"direct","automatic","channel","trending"}){
                var unfiltered=VideoBatch.Collect(mode,new VideoLedger(lockedHistory),store,CancellationToken.None,
                    search:(q,t)=>Task.FromResult(new List<Video>{V(0),V(0),V(98)}),captions:Good).GetAwaiter().GetResult();
                Check(unfiltered.Error=="" && unfiltered.Videos.Count==3,mode+" ignores locked corrupt selection history and retains repeated IDs");
            }
            Check(File.ReadAllText(lockedHistory)=="not valid history","existing history bytes preserved without reading or rewriting");
            var parallel=VideoBatch.Collect("duplicates",null,new ContentStore(Path.Combine(run,"parallel-content")),CancellationToken.None,
                search:(q,t)=>Task.FromResult(new List<Video>{V(95),V(95),V(95)}),captions:async(v,t)=>{await Task.Delay(50,t);return C(v);}).GetAwaiter().GetResult();
            Check(parallel.Error=="" && parallel.Videos.Count==3,"concurrent duplicate rows share caption cache without losing results");
            string blocked = Path.Combine(run, "blocked");
            File.WriteAllText(blocked, "fixture");
            var bad = VideoBatch.Collect("disk", new VideoLedger(Path.Combine(run, "disk.jsonl")), new ContentStore(blocked), CancellationToken.None,
                null, (q,t) => Task.FromResult(new List<Video> { V(99) }), Good).GetAwaiter().GetResult();
            Check(bad.Videos.Count == 0 && bad.Error.Length > 0, "caption storage failure cannot yield a video");
            var cts = new CancellationTokenSource();
            var partial = VideoBatch.Collect("cancel", new VideoLedger(Path.Combine(run, "cancel.jsonl")), new ContentStore(Path.Combine(run, "cancel-content")), cts.Token,
                null, (q,t) => Task.FromResult(Enumerable.Range(50, 8).Select(V).ToList()), (v,t) => {
                    if (v.Id == V(53).Id) cts.Cancel();
                    t.ThrowIfCancellationRequested();
                    return Good(v,t);
                }).GetAwaiter().GetResult();
            Check(partial.Cancelled && partial.Videos.Count == 3, "cancellation retains already committed partial results");

            var liveLedger = new VideoLedger(Path.Combine(run, "live.jsonl"));
            var liveStore = new ContentStore(Path.Combine(run, "live-content"));
            var live = VideoBatch.Collect("인디 게임 추천", liveLedger, liveStore, CancellationToken.None).GetAwaiter().GetResult();
            Check(live.Videos.Count > 0 && live.Videos.Count <= 10 && live.Error.Length == 0, "actual YouTube batch returns up to ten captioned videos");
            Check(live.Videos.All(v => liveStore.Load(v.Id).Cues.Count > 0), "actual batch videos all have real subtitle bodies");

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Exception error = null;
            using (var form = new MainForm(Path.Combine(run, "ui", "history.json")))
            {
                form.Opacity = 0;
                form.ShowInTaskbar = false;
                form.Shown += async (sender,e) => {
                    try
                    {
                        ((TextBox)form.Controls.Find("Query",true)[0]).Text = "인디 게임";
                        ((ComboBox)form.Controls.Find("UploadPeriod",true)[0]).SelectedIndex = 3;
                        await form.RecommendVideos();
                        var grid = (DataGridView)form.Controls.Find("Videos",true)[0];
                        Check(grid.Rows.Count > 0 && grid.Rows.Count <= 10, "one native action completes random keyword search and caption filtering");
                        Check(((Label)form.Controls.Find("SelectedQuery",true)[0]).Text.Contains("검색어 · "), "chosen random search term visible");
                        Check(((Button)form.Controls.Find("Recommend",true)[0]).Enabled, "native recommendation button restored");
                        var files = new ContentStore(Path.Combine(run, "ui", "content"));
                        var ids = new VideoLedger(Path.Combine(run, "ui", "videos.jsonl")).ReadIds();
                        Check(ids.Count==0 && grid.Rows.Cast<DataGridViewRow>().All(r=>files.Load(((Video)r.Tag).Id)!=null), "native results retain captions without recording selection history");
                        using (var bitmap = new Bitmap(form.Width,form.Height))
                        {
                            form.DrawToBitmap(bitmap,new Rectangle(0,0,bitmap.Width,bitmap.Height));
                            bitmap.Save(Path.Combine(output,"batch-preview.png"),ImageFormat.Png);
                        }
                    }
                    catch(Exception ex) { error=ex; }
                    finally { form.Close(); }
                };
                Application.Run(form);
            }
            if(error!=null) throw error;
            return 0;
        }
        catch(Exception ex) { Console.Error.WriteLine(ex.GetType().Name+": "+ex.Message); return 1; }
    }
}
