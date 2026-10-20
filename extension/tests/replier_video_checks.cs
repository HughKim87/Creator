using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using ReplierDesktop;

public static class VideoChecks
{
    static void Check(bool ok, string name) { if (!ok) throw new Exception(name); Console.WriteLine("PASS " + name); }
    static object Card(string id)
    {
        return new { videoRenderer = new { videoId = id,
            title = new { runs = new[] { new { text = "게임 제목 } \"검사\"" } } },
            ownerText = new { runs = new[] { new { text = "테스트 채널" } } },
            lengthText = new { simpleText = "12:34" }, viewCountText = new { simpleText = "조회수 1.2만회" }, publishedTimeText = new { simpleText = "3개월 전" } } };
    }
    static Video Item(string id) { return new Video { Id = id, Title = "fixture", Channel = "test" }; }

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
            var payload = new { contents = new { twoColumnSearchResultsRenderer = new { primaryContents =
                new { sectionListRenderer = new { contents = new[] { new { itemSectionRenderer =
                    new { contents = new object[] { Card("ABCDEFGHIJ1"), Card("ABCDEFGHIJ1"), Card("KLMNOPQRST2") } } } } } } } } };
            string html = "<script>var ytInitialData = " + new JavaScriptSerializer().Serialize(payload) + ";</script>";
            var parsed = VideoSearch.Parse(html);
            Check(parsed.Count == 3 && parsed[0].Title.Contains("}"), "video search parser handles quoted braces and duplicate IDs");
            Check(parsed[0].Url == "https://www.youtube.com/watch?v=ABCDEFGHIJ1", "video URLs canonicalized by ID");
            Check(parsed[0].DurationText == "12:34" && parsed[0].ViewCountText == "조회수 1.2만회", "duration and view count use actual renderer display text");
            Check(parsed[0].PublishedText == "3개월 전", "published time preserves YouTube display text");
            Check(VideoSearch.Parse(html.Replace("publishedTimeText","missingTime"))[0].PublishedText == "미제공", "missing published time is explicit without inventing a date");
            bool formatRejected = false;
            try { VideoSearch.Parse("<html>consent required</html>"); } catch (InvalidDataException) { formatRejected = true; }
            Check(formatRejected, "blocked or changed search response is not an empty success");

            var live = VideoSearch.Search("인디 게임 추천", CancellationToken.None).GetAwaiter().GetResult();
            Check(live.Count >= 2 && live.All(v => VideoSearch.ValidId(v.Id) && v.Title.Length > 0 && v.Channel.Length > 0),
                "real YouTube search returns IDs titles and channels");
            Check(live.Any(v => v.DurationText != "미제공" && v.ViewCountText != "미제공"), "real search supplies duration and views");
            Check(live.Any(v => v.PublishedText != "미제공"), "real YouTube search supplies published time");
            Console.WriteLine("NOTE native batch UI is verified by BatchChecks");
            return 0;
        }
        catch (Exception ex) { Console.Error.WriteLine(ex.GetType().Name + ": " + ex.Message); return 1; }
    }
}
