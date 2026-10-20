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

public static class DesktopChecks
{
    static void Check(bool condition, string name) { if (!condition) throw new Exception(name); Console.WriteLine("PASS " + name); }
    static Task<List<string>> Fixture(string seed, CancellationToken token)
    {
        return Task.FromResult(Enumerable.Range(0, 5).Select(i => seed + " 실제추천" + i).ToList());
    }
    [STAThread]
    public static int Main(string[] args)
    {
        try
        {
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
            string folder = args[0];
            Directory.CreateDirectory(folder);
            var parsed = TopicService.Parse("[\"게임\",[\"게임 공략\",\"게임 공략\",\"게임 리뷰\"]]", "게임");
            Check(parsed.Count == 2, "upstream duplicates removed");
            bool rejected = false;
            try { TopicService.Parse("[\"other\",[\"게임\"]]", "게임"); } catch (InvalidDataException) { rejected = true; }
            Check(rejected, "mismatched upstream rejected");
            var first = TopicService.Discover("", new string[0], 0, CancellationToken.None, Fixture).GetAwaiter().GetResult();
            var second = TopicService.Discover("", first.Topics.Select(t => t.Term), first.NextCursor, CancellationToken.None, Fixture).GetAwaiter().GetResult();
            Check(first.Topics.Count == 12 && first.Topics.Select(t => t.Source).Distinct().Count() == 4, "four sources interleaved");
            Check(!first.Topics.Select(t => t.Term).Intersect(second.Topics.Select(t => t.Term)).Any(), "consecutive discoveries do not repeat");
            var wrapped = TopicService.Discover("", first.Topics.Select(t => t.Term), 5, CancellationToken.None, Fixture).GetAwaiter().GetResult();
            Check(!first.Topics.Select(t => t.Term).Intersect(wrapped.Topics.Select(t => t.Term)).Any(), "history survives category rotation");
            var exhausted = TopicService.Seeds.Take(4).SelectMany(seed=>Enumerable.Range(0,5).Select(i=>seed+" 실제추천"+i)).ToList();
            int calls = 0;
            var fallback=TopicService.Discover("",exhausted,5,CancellationToken.None,(seed,token)=>{
                Interlocked.Increment(ref calls); return Fixture(seed,token);
            }).GetAwaiter().GetResult();
            Check(calls==8 && fallback.Topics.Count>0 && fallback.NextCursor==7,"spent group advances automatically to next four sources");
            Check(!fallback.Topics.Select(t=>t.Term).Intersect(exhausted).Any(),"automatic fallback never reuses excluded terms");
            calls=0;
            var allSpent=TopicService.Seeds.SelectMany(seed=>Enumerable.Range(0,5).Select(i=>seed+" 실제추천"+i));
            var none=TopicService.Discover("",allSpent,5,CancellationToken.None,(seed,token)=>{
                Interlocked.Increment(ref calls); return Fixture(seed,token);
            }).GetAwaiter().GetResult();
            Check(none.Topics.Count==0 && calls==20 && none.NextCursor==10,"fully spent sources finish after one bounded rotation");
            var cancelled=new CancellationTokenSource();cancelled.Cancel();bool stopped=false;
            try{TopicService.Discover("",exhausted,5,cancelled.Token,Fixture).GetAwaiter().GetResult();}catch(OperationCanceledException){stopped=true;}
            Check(stopped,"cancellation stops fallback discovery");
            string liveHistory=Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"..","..","data","replier","desktop-history.json"));
            var actual=new HistoryStore(liveHistory).Load();
            var live=TopicService.Discover(actual.Query,actual.Seen,actual.Cursor,CancellationToken.None).GetAwaiter().GetResult();
            Check(live.Topics.Count>0 && live.Topics.All(t=>!actual.Seen.Select(TopicService.Key).Contains(TopicService.Key(t.Term))),"actual current local history recovers fresh YouTube suggestions without changing history");
            Console.WriteLine("LIVE TOPICS "+string.Join(" / ",live.Topics.Take(5).Select(t=>t.Term)));
            var store = new HistoryStore(Path.Combine(folder, "history.json"));
            store.Save(new History { Cursor = 2, Query = "", Seen = first.Topics.Select(t => t.Term).ToList(), Selected = "게임 리뷰" });
            var loaded = store.Load();
            Check(loaded.Cursor == 2 && loaded.Seen.Count == 12 && loaded.Selected == "게임 리뷰", "history persists across reload");
            store.Save(loaded);
            Check(store.Load().Seen.Count == 12, "atomic history replacement");

            Console.WriteLine("NOTE native batch UI is verified by BatchChecks");
            return 0;
        }
        catch (Exception ex) { Console.Error.WriteLine(ex.GetType().Name + ": " + ex.Message); return 1; }
    }
}
