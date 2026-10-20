using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

namespace ReplierDesktop
{
    public sealed class Video
    {
        public string Id { get; set; }
        public string Title { get; set; }
        public string Channel { get; set; }
        public string Query { get; set; }
        public string FoundAt { get; set; }
        public string DurationText { get; set; }
        public string ViewCountText { get; set; }
        public string PublishedText { get; set; }
        public string CommentCountText { get; set; }
        internal string CommentContinuation;
        public string Url { get { return "https://www.youtube.com/watch?v=" + Id; } }
        public string Thumbnail { get { return "https://i.ytimg.com/vi/" + Id + "/hqdefault.jpg"; } }
    }

    public static class ViewCounts
    {
        // Unknown counts sort after known counts; preserve the original display text.
        public static long Parse(string text)
        {
            text=(text ?? "").Trim();
            if(text=="조회수 없음" || text.Equals("No views",StringComparison.OrdinalIgnoreCase)) return 0;
            var match=Regex.Match(text,@"^(?:조회수\s*)?([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(억|만|천|[KMB])?\s*(?:회|views?)?$",RegexOptions.IgnoreCase);
            decimal value;
            if(!match.Success || !decimal.TryParse(match.Groups[1].Value.Replace(",",""),NumberStyles.AllowDecimalPoint,CultureInfo.InvariantCulture,out value)) return -1;
            decimal factor=1;
            switch(match.Groups[2].Value.ToUpperInvariant())
            {
                case "억": factor=100000000;break;
                case "만": factor=10000;break;
                case "천": case "K": factor=1000;break;
                case "M": factor=1000000;break;
                case "B": factor=1000000000;break;
            }
            if(value>long.MaxValue/factor) return -1;
            return (long)(value*factor);
        }
    }

    public static class VideoSearch
    {
        public static bool ValidId(string id) { return id != null && Regex.IsMatch(id, @"\A[A-Za-z0-9_-]{11}\z"); }
        static Dictionary<string, object> Map(object value) { return value as Dictionary<string, object>; }
        static object Field(object value, string key)
        {
            var map = Map(value);
            return map != null && map.ContainsKey(key) ? map[key] : null;
        }
        static IEnumerable<object> Items(object value) { return value as object[] ?? new object[0]; }
        static string Text(object value)
        {
            var simple = Field(value, "simpleText") as string;
            return simple ?? string.Concat(Items(Field(value, "runs")).Select(run => Field(run, "text") as string ?? ""));
        }

        public static string ExtractData(string html)
        {
            var match = Regex.Match(html, @"(?:var\s+)?ytInitialData\s*=\s*");
            if (!match.Success) throw new InvalidDataException("YouTube 검색 데이터를 읽지 못했습니다. 응답 형식이나 접속 상태를 확인해 주세요.");
            int start = match.Index + match.Length;
            if (start >= html.Length || html[start] != '{') throw new InvalidDataException("검색 데이터 형식이 변경되었습니다.");
            int depth = 0;
            bool quoted = false, escaped = false;
            for (int i = start; i < html.Length; i++)
            {
                char c = html[i];
                if (quoted)
                {
                    if (escaped) escaped = false;
                    else if (c == '\\') escaped = true;
                    else if (c == '"') quoted = false;
                }
                else if (c == '"') quoted = true;
                else if (c == '{') depth++;
                else if (c == '}' && --depth == 0) return html.Substring(start, i - start + 1);
            }
            throw new InvalidDataException("검색 데이터가 불완전합니다.");
        }

        static bool SelectedFilter(object value,string label)
        {
            var map=Map(value);
            if(map != null)
            {
                object filter;
                if(map.TryGetValue("searchFilterRenderer",out filter) && Text(Field(filter,"label"))==label &&
                    (Field(filter,"status") as string)=="FILTER_STATUS_SELECTED") return true;
                return map.Values.Any(child=>SelectedFilter(child,label));
            }
            return Items(value).Any(child=>SelectedFilter(child,label));
        }

        public static List<Video> Parse(string html,string period="all")
        {
            var serializer = new JavaScriptSerializer { MaxJsonLength = 8 * 1024 * 1024, RecursionLimit = 150 };
            object data;
            try { data = serializer.DeserializeObject(ExtractData(html)); }
            catch (ArgumentException) { throw new InvalidDataException("YouTube 검색 데이터 형식이 변경되었습니다."); }
            string requiredFilter=UploadPeriods.YouTubeLabel(period);
            if(requiredFilter.Length>0 && !SelectedFilter(data,requiredFilter))
                throw new InvalidDataException("YouTube가 업로드 기간 필터 적용을 확인해 주지 않아 검색을 중단했습니다.");
            var primary = Field(Field(Field(data, "contents"), "twoColumnSearchResultsRenderer"), "primaryContents");
            var sections = Field(Field(primary, "sectionListRenderer"), "contents");
            if (sections == null) throw new InvalidDataException("검색 결과에 접근하지 못했습니다. YouTube 응답이 변경되었거나 접속이 제한됐을 수 있습니다.");
            var videos = new List<Video>();

            foreach (var section in Items(sections))
            {
                foreach (var item in Items(Field(Field(section, "itemSectionRenderer"), "contents")))
                {
                    var renderer = Field(item, "videoRenderer");
                    string id = Field(renderer, "videoId") as string;
                    if (!ValidId(id)) continue;
                    string title = Text(Field(renderer, "title"));
                    string channel = Text(Field(renderer, "ownerText"));
                    if (channel.Length == 0) channel = Text(Field(renderer, "longBylineText"));
                    // Only ordinary, directly searchable video cards; no ads, channel cards or Shorts shelves.
                    if (title.Length == 0 || channel.Length == 0) continue;
                    string duration = Text(Field(renderer, "lengthText"));
                    if (duration.Length == 0)
                        foreach (var overlay in Items(Field(renderer, "thumbnailOverlays"))) {
                            duration = Text(Field(Field(overlay, "thumbnailOverlayTimeStatusRenderer"), "text"));
                            if (duration.Length > 0) break;
                        }
                    string views = Text(Field(renderer, "viewCountText"));
                    if (views.Length == 0) views = Text(Field(renderer, "shortViewCountText"));
                    string published=Text(Field(renderer,"publishedTimeText"));
                    // YouTube can mix older recommendations into a filtered search response.
                    if(!UploadPeriods.IncludesDisplayAge(published,period)) continue;
                    videos.Add(new Video { Id = id, Title = title, Channel = channel,
                        DurationText = duration.Length > 0 ? duration : "미제공",
                        ViewCountText = views.Length > 0 ? views : "미제공",
                        PublishedText = string.IsNullOrWhiteSpace(published) ? "미제공" : published });
                }
            }
            return videos;
        }

        public static Task<List<Video>> Search(string query,CancellationToken token)
        {
            return Search(query,token,"all");
        }
        public static string SearchUrl(string query,string period)
        {
            if(string.IsNullOrWhiteSpace(query) || query.Length>200 || query.Any(char.IsControl))
                throw new ArgumentException("먼저 추천 검색어를 선택해 주세요.");
            string filter=UploadPeriods.Filter(period);
            return "https://www.youtube.com/results?search_query="+Uri.EscapeDataString(query)+"&hl=ko&gl=KR"+
                (filter.Length==0 ? "" : "&sp="+Uri.EscapeDataString(filter));
        }
        public static async Task<List<Video>> Search(string query, CancellationToken token,string period)
        {
            if (string.IsNullOrWhiteSpace(query) || query.Length > 200 || query.Any(char.IsControl))
                throw new ArgumentException("먼저 추천 검색어를 선택해 주세요.");
            using (var client = new HttpClient())
            {
                client.Timeout = TimeSpan.FromSeconds(22);
                client.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 24HReplier/0.3");
                var url = SearchUrl(query,period);
                using (var response = await client.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, token).ConfigureAwait(false))
                {
                    response.EnsureSuccessStatusCode();
                    await response.Content.LoadIntoBufferAsync(8 * 1024 * 1024).ConfigureAwait(false);
                    var bytes = await response.Content.ReadAsByteArrayAsync().ConfigureAwait(false);
                    token.ThrowIfCancellationRequested();
                    return Parse(Encoding.UTF8.GetString(bytes),period);
                }
            }
        }

        public static async Task<Image> Picture(Video video, CancellationToken token)
        {
            using (var client = new HttpClient())
            {
                client.Timeout = TimeSpan.FromSeconds(8);
                using (var response = await client.GetAsync(video.Thumbnail, HttpCompletionOption.ResponseHeadersRead, token).ConfigureAwait(false))
                {
                    response.EnsureSuccessStatusCode();
                    await response.Content.LoadIntoBufferAsync(2 * 1024 * 1024).ConfigureAwait(false);
                    var bytes = await response.Content.ReadAsByteArrayAsync().ConfigureAwait(false);
                    using (var stream = new MemoryStream(bytes))
                    using (var image = Image.FromStream(stream)) return new Bitmap(image);
                }
            }
        }
    }

    public sealed class VideoLedger
    {
        readonly string path;
        public VideoLedger(string file) { path = file; }


        public HashSet<string> ReadIds()
        {
            var ids = new HashSet<string>(StringComparer.Ordinal);
            if (!File.Exists(path)) return ids;
            using (var file = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.None))
            using (var reader = new StreamReader(file, new UTF8Encoding(false, true)))
            {
                var serializer = new JavaScriptSerializer();
                string line;
                while ((line = reader.ReadLine()) != null)
                {
                    Video record;
                    try { record = serializer.Deserialize<Video>(line); }
                    catch (Exception) { throw new InvalidDataException("영상 이력이 손상되어 검색을 중단했습니다."); }
                    if (record == null || !VideoSearch.ValidId(record.Id)) throw new InvalidDataException("영상 이력을 확인할 수 없습니다.");
                    ids.Add(record.Id);
                }
            }
            return ids;
        }

        public Video ClaimFirst(IEnumerable<Video> candidates, string query)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            // An exclusive file handle covers read + reservation across threads and app instances.
            using (var file = new FileStream(path, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
            {
                var serializer = new JavaScriptSerializer();
                var ids = new HashSet<string>(StringComparer.Ordinal);
                using (var reader = new StreamReader(file, new UTF8Encoding(false, true), true, 1024, true))
                {
                    string line;
                    while ((line = reader.ReadLine()) != null)
                    {
                        if (line.Length == 0) throw new InvalidDataException("영상 이력이 손상되어 검색을 중단했습니다. 이력 파일을 확인해야 합니다.");
                        Video record;
                        try { record = serializer.Deserialize<Video>(line); }
                        catch (Exception) { throw new InvalidDataException("영상 이력이 손상되어 검색을 중단했습니다. 이력 파일을 확인해야 합니다."); }
                        if (record == null || !VideoSearch.ValidId(record.Id)) throw new InvalidDataException("영상 이력을 확인할 수 없어 중복 방지를 위해 검색을 중단했습니다.");
                        ids.Add(record.Id);
                    }
                }
                var chosen = candidates.FirstOrDefault(video => VideoSearch.ValidId(video.Id) && !ids.Contains(video.Id));
                if (chosen == null) return null;
                var recordToSave = new Video { Id = chosen.Id, Title = chosen.Title, Channel = chosen.Channel,
                    Query = query, FoundAt = DateTime.UtcNow.ToString("o"), DurationText = chosen.DurationText, ViewCountText = chosen.ViewCountText, PublishedText = chosen.PublishedText, CommentCountText = chosen.CommentCountText };
                // Record durably before displaying; a restart after display must never repeat the ID.
                file.Position = file.Length;
                if (file.Length > 0)
                {
                    file.Position = file.Length - 1;
                    if (file.ReadByte() != '\n') throw new InvalidDataException("영상 이력의 마지막 기록이 불완전합니다. 중복 방지를 위해 중단했습니다.");
                    file.Position = file.Length;
                }
                var bytes = Encoding.UTF8.GetBytes(serializer.Serialize(recordToSave) + "\n");
                file.Write(bytes, 0, bytes.Length);
                file.Flush(true);
                return recordToSave;
            }
        }
    }
}
