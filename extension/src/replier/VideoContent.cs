using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using System.Diagnostics;

namespace ReplierDesktop
{
    public sealed class CaptionCue
    {
        public long StartMs { get; set; }
        public long DurationMs { get; set; }
        public string Text { get; set; }
    }
    public sealed class VideoContent
    {
        public int Version { get; set; }
        public string VideoId { get; set; }
        public string Language { get; set; }
        public string OriginalLanguage { get; set; }
        public bool IsAuto { get; set; }
        public string Source { get; set; }
        public string AcquiredAt { get; set; }
        public List<CaptionCue> Cues { get; set; }
    }
    public sealed class ContentUnavailable : IOException
    {
        public ContentUnavailable(string message) : base(message) { }
    }

    public static class CaptionService
    {
        // Public client contract checked against yt-dlp's youtube/_base.py.
        const string ClientVersion = "21.26.364";
        const string Agent = "com.google.android.youtube/21.26.364 (Linux; U; Android 11) gzip";
        public static object Get(object obj, string key)
        {
            var map = obj as Dictionary<string, object>;
            return map != null && map.ContainsKey(key) ? map[key] : null;
        }
        static IEnumerable<object> Items(object value) { return value as object[] ?? new object[0]; }
        static long Milliseconds(object value)
        {
            long number;
            if (value == null || !long.TryParse(Convert.ToString(value, CultureInfo.InvariantCulture), out number) ||
                number < 0 || number > 604800000)
                throw new InvalidDataException("자막 타임코드를 읽지 못했습니다.");
            return number;
        }
        public static List<CaptionCue> ParseCues(string json)
        {
            object root;
            try { root = new JavaScriptSerializer { MaxJsonLength = 4 * 1024 * 1024 }.DeserializeObject(json); }
            catch (ArgumentException) { throw new ContentUnavailable("자막 본문을 읽지 못했습니다. 내용 확보는 완료되지 않았습니다."); }
            if (!(Get(root, "events") is object[])) throw new ContentUnavailable("유효한 자막 본문이 없습니다.");
            var cues = new List<CaptionCue>();
            var seen = new HashSet<string>();
            foreach (var item in Items(Get(root, "events")))
            {
                if (!(Get(item, "segs") is object[])) continue;
                string text = string.Concat(Items(Get(item, "segs")).Select(seg => Get(seg, "utf8") as string ?? ""));
                text = Regex.Replace(text, @"\s+", " ").Trim();
                if (text.Length == 0) continue;
                long start = Milliseconds(Get(item, "tStartMs"));
                long duration = Get(item, "dDurationMs") == null ? 0 : Milliseconds(Get(item, "dDurationMs"));
                if (!seen.Add(start + ":" + text)) continue;
                cues.Add(new CaptionCue { StartMs = start, DurationMs = duration, Text = text });
            }
            if (cues.Count == 0) throw new ContentUnavailable("자막 본문이 비어 있습니다. 영상 내용을 확보하지 못했습니다.");
            return cues.OrderBy(c => c.StartMs).ToList();
        }

        public static object SelectTrack(object player, string expectedId)
        {
            if ((Get(Get(player, "videoDetails"), "videoId") as string) != expectedId)
                throw new ContentUnavailable("응답의 영상 ID가 달라 내용 확보를 중단했습니다.");
            if ((Get(Get(player, "playabilityStatus"), "status") as string) != "OK")
                throw new ContentUnavailable("영상 접근이 제한되어 자막을 가져오지 못했습니다.");
            var tracks = Items(Get(Get(Get(player, "captions"), "playerCaptionsTracklistRenderer"), "captionTracks"))
                .Where(t => Get(t, "baseUrl") is string && Get(t, "languageCode") is string).ToList();
            if (tracks.Count == 0) throw new ContentUnavailable("이 영상에서 제공되는 공개 자막을 찾지 못했습니다. 내용 확보는 완료되지 않았습니다.");
            return tracks.OrderBy(t => {
                string lang = (string)Get(t, "languageCode");
                int priority = lang == "ko" ? 0 : lang.StartsWith("ko-") ? 1 : lang == "en" ? 2 : 3;
                return priority * 2 + (((Get(t, "kind") as string) == "asr") ? 1 : 0);
            }).First();
        }

        public static string OriginalLanguage(object player)
        {
            var declared=Get(Get(player,"videoDetails"),"defaultAudioLanguage") as string;
            if(!string.IsNullOrEmpty(declared)) return declared;
            var languages=Items(Get(Get(Get(player,"captions"),"playerCaptionsTracklistRenderer"),"captionTracks"))
                .Where(t=>(Get(t,"kind") as string)=="asr").Select(t=>Get(t,"languageCode") as string)
                .Where(l=>!string.IsNullOrEmpty(l)).Distinct().ToArray();
            return languages.Length==1 ? languages[0] : null;
        }

        public static Uri CaptionUrl(string url, string expectedId = null)
        {
            Uri uri;
            if (!Uri.TryCreate(url, UriKind.Absolute, out uri) || uri.Scheme != "https" || !uri.IsDefaultPort ||
                (uri.Host != "www.youtube.com" && uri.Host != "youtube.com") || uri.AbsolutePath != "/api/timedtext")
                throw new ContentUnavailable("자막 제공 주소를 확인할 수 없습니다.");
            var builder = new UriBuilder(uri);
            var query = System.Web.HttpUtility.ParseQueryString(uri.Query);
            if (expectedId != null && query["v"] != expectedId) throw new ContentUnavailable("자막 주소의 영상 ID가 달라 내용 확보를 중단했습니다.");
            query["fmt"] = "json3";
            builder.Query = query.ToString();
            return builder.Uri;
        }

        static async Task<string> Read(HttpResponseMessage response, int limit, CancellationToken token)
        {
            response.EnsureSuccessStatusCode();
            await response.Content.LoadIntoBufferAsync(limit).ConfigureAwait(false);
            token.ThrowIfCancellationRequested();
            var bytes = await response.Content.ReadAsByteArrayAsync().ConfigureAwait(false);
            if (bytes.Length == 0) throw new ContentUnavailable("자막 서비스가 빈 응답을 반환했습니다. 영상 내용을 확보하지 못했습니다.");
            return Encoding.UTF8.GetString(bytes);
        }

        public static async Task<VideoContent> Fetch(Video video, CancellationToken token)
        {
            if (video == null || !VideoSearch.ValidId(video.Id)) throw new ArgumentException("먼저 영상을 찾아주세요.");
            using (var handler = new HttpClientHandler { UseCookies = false, AllowAutoRedirect = false })
            using (var client = new HttpClient(handler))
            {
                client.Timeout = TimeSpan.FromSeconds(20);
                client.DefaultRequestHeaders.UserAgent.ParseAdd(Agent);
                var body = new {
                    context = new { client = new { clientName = "ANDROID", clientVersion = ClientVersion,
                        androidSdkVersion = 30, hl = "ko", gl = "KR" } },
                    videoId = video.Id
                };
                string json;
                using (var request = new StringContent(new JavaScriptSerializer().Serialize(body), Encoding.UTF8, "application/json"))
                using (var response = await client.PostAsync("https://www.youtube.com/youtubei/v1/player", request, token).ConfigureAwait(false))
                    json = await Read(response, 8 * 1024 * 1024, token).ConfigureAwait(false);
                object player;
                try { player = new JavaScriptSerializer { MaxJsonLength = 8 * 1024 * 1024, RecursionLimit = 150 }.DeserializeObject(json); }
                catch (ArgumentException) { throw new ContentUnavailable("영상 자막 목록 응답을 읽지 못했습니다."); }
                var track = SelectTrack(player, video.Id);
                var url = CaptionUrl((string)Get(track, "baseUrl"), video.Id);
                string captionJson;
                using (var response = await client.GetAsync(url, token).ConfigureAwait(false))
                    captionJson = await Read(response, 4 * 1024 * 1024, token).ConfigureAwait(false);
                return new VideoContent {
                    Version = 1, VideoId = video.Id, Language = (string)Get(track, "languageCode"),
                    IsAuto = (Get(track, "kind") as string) == "asr",
                    OriginalLanguage = OriginalLanguage(player),
                    Source = "YouTube 공개 자막", AcquiredAt = DateTime.UtcNow.ToString("o"),
                    Cues = ParseCues(captionJson)
                };
            }
        }

        public static string Timestamp(long ms)
        {
            var value = TimeSpan.FromMilliseconds(ms);
            return ((int)value.TotalHours).ToString("00") + ":" + value.Minutes.ToString("00") + ":" + value.Seconds.ToString("00") + "." + value.Milliseconds.ToString("000");
        }
    }

    public sealed class ContentStore
    {
        readonly string folder;
        public ContentStore(string directory) { folder = directory; }
        string PathFor(string id)
        {
            if (!VideoSearch.ValidId(id)) throw new ArgumentException("유효하지 않은 영상 ID입니다.");
            return Path.Combine(folder, id + ".json");
        }
        public static void Validate(VideoContent content, string id)
        {
            DateTime parsed;
            if (content == null || content.Version != 1 || content.VideoId != id || !VideoSearch.ValidId(id) ||
                content.Source != "YouTube 공개 자막" || string.IsNullOrWhiteSpace(content.Language) ||
                !DateTime.TryParse(content.AcquiredAt, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind, out parsed) ||
                content.Cues == null || content.Cues.Count == 0 ||
                content.Cues.Any(c => c == null || c.StartMs < 0 || c.DurationMs < 0 || string.IsNullOrWhiteSpace(c.Text)))
                throw new InvalidDataException("저장된 내용의 영상 ID·출처·대사를 확인할 수 없습니다.");
        }
        public VideoContent Load(string id)
        {
            string path = PathFor(id);
            if (!File.Exists(path)) return null;
            if (new FileInfo(path).Length > 8 * 1024 * 1024) throw new InvalidDataException("저장된 자막 파일이 너무 큽니다.");
            var result = new JavaScriptSerializer { MaxJsonLength = 8 * 1024 * 1024 }.Deserialize<VideoContent>(File.ReadAllText(path, Encoding.UTF8));
            Validate(result, id);
            return result;
        }
        public void Save(VideoContent content)
        {
            Validate(content, content.VideoId);
            Directory.CreateDirectory(folder);
            string path = PathFor(content.VideoId);
            string temp = path + "." + Guid.NewGuid().ToString("N") + ".new";
            File.WriteAllText(temp, new JavaScriptSerializer { MaxJsonLength = 8 * 1024 * 1024 }.Serialize(content), new UTF8Encoding(false));
            if (File.Exists(path)) File.Replace(temp, path, null);
            else File.Move(temp, path);
        }
    }

    public sealed class ContentForm : Form
    {
        readonly Video video;
        readonly ContentStore store;
        readonly CancellationTokenSource cancel = new CancellationTokenSource();
        readonly DataGridView grid = new DataGridView();
        readonly Label status = new Label();
        readonly Button refresh = new Button();
        readonly Button open = new Button();
        VideoContent content;
        bool busy;

        public ContentForm(Video found, ContentStore storage, bool autoLoad = true)
        {
            video = found; store = storage;
            Text = "영상 내용 확인 · 24HReplier";
            Name = "VideoContent";
            Font = new Font("맑은 고딕", 10);
            BackColor = Color.FromArgb(244, 246, 242);
            ClientSize = new Size(1000, 750);
            MinimumSize = new Size(800, 600);
            StartPosition = FormStartPosition.CenterParent;
            var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 5, Padding = new Padding(24) };
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 68));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 54));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 42));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 50));
            Controls.Add(layout);
            layout.Controls.Add(new Label { Text = video.Title + "\n" + video.Channel + " · " + video.Url,
                Dock = DockStyle.Fill, Font = new Font("맑은 고딕", 12, FontStyle.Bold), AutoEllipsis = true }, 0, 0);
            status.Name = "ContentStatus";
            status.Text = "아직 영상 내용을 확보하지 않았습니다.";
            status.Dock = DockStyle.Fill;
            status.ForeColor = Color.FromArgb(19, 110, 88);
            layout.Controls.Add(status, 0, 1);
            var buttons = new FlowLayoutPanel { Dock = DockStyle.Fill };
            refresh.Name = "RefreshContent";
            refresh.Text = "자막 다시 가져오기";
            refresh.AutoSize = true;
            refresh.Click += async (sender, e) => await LoadContent(true);
            open.Name = "OpenCue";
            open.Text = "선택 대사 시점 열기";
            open.AutoSize = true;
            open.Enabled = false;
            open.Click += (sender, e) => {
                if (content == null || grid.SelectedRows.Count == 0) return;
                var cue = content.Cues[grid.SelectedRows[0].Index];
                try { Process.Start(new ProcessStartInfo(video.Url + "&t=" + (cue.StartMs / 1000).ToString(CultureInfo.InvariantCulture)) { UseShellExecute = true }); }
                catch (Exception) { status.Text = "기본 브라우저에서 영상을 열지 못했습니다."; }
            };
            buttons.Controls.Add(refresh);
            buttons.Controls.Add(open);
            layout.Controls.Add(buttons, 0, 2);
            grid.Name = "CaptionCues";
            grid.Dock = DockStyle.Fill;
            grid.ReadOnly = true;
            grid.AllowUserToAddRows = false;
            grid.AllowUserToDeleteRows = false;
            grid.RowHeadersVisible = false;
            grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
            grid.MultiSelect = false;
            grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
            grid.BackgroundColor = Color.White;
            grid.BorderStyle = BorderStyle.None;
            grid.DefaultCellStyle.WrapMode = DataGridViewTriState.True;
            grid.AutoSizeRowsMode = DataGridViewAutoSizeRowsMode.AllCells;
            grid.Columns.Add("time", "시작 시각");
            grid.Columns.Add("text", "실제 자막 대사");
            grid.Columns[0].FillWeight = 18;
            grid.Columns[1].FillWeight = 82;
            grid.SelectionChanged += (sender, e) => open.Enabled = !busy && content != null && grid.SelectedRows.Count > 0;
            layout.Controls.Add(grid, 0, 3);
            layout.Controls.Add(new Label { Text = "자막은 음성 내용의 근거입니다. 화면만으로 전달되는 상황은 확인하지 않았습니다.\n자동 생성 자막에는 인식 오류가 있을 수 있습니다. AI 요약과 댓글 생성은 아직 하지 않습니다.",
                Dock = DockStyle.Fill, Font = new Font("맑은 고딕", 9), ForeColor = Color.FromArgb(95, 112, 101), Padding = new Padding(0, 10, 0, 0) }, 0, 4);
            if (autoLoad) Shown += async (sender, e) => await LoadContent(false);
            FormClosing += (sender, e) => cancel.Cancel();
        }

        public async Task LoadContent(bool force)
        {
            if (busy) return;
            busy = true;
            refresh.Enabled = false;
            open.Enabled = false;
            content = null;
            grid.Rows.Clear();
            status.Text = "공개 자막의 실제 대사와 타임코드를 확인하고 있어요…";
            try
            {
                VideoContent loaded = force ? null : await Task.Run(() => store.Load(video.Id), cancel.Token);
                bool cached = loaded != null;
                if (loaded == null)
                {
                    loaded = await CaptionService.Fetch(video, cancel.Token);
                    await Task.Run(() => store.Save(loaded), cancel.Token);
                }
                if (IsDisposed || cancel.IsCancellationRequested) return;
                content = loaded;
                foreach (var cue in content.Cues) grid.Rows.Add(CaptionService.Timestamp(cue.StartMs), cue.Text);
                grid.ClearSelection();
                var when = TimeZoneInfo.ConvertTimeFromUtc(DateTime.Parse(content.AcquiredAt, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind).ToUniversalTime(), TimeZoneInfo.FindSystemTimeZoneById("Korea Standard Time"));
                status.Text = (cached ? "저장된 자막 확인" : "실제 자막 확보 완료") + " · " + content.Language + " · " +
                    (content.IsAuto ? "자동 생성 자막" : "제작자 제공 자막") + " · 대사 " + content.Cues.Count + "개\n" +
                    "출처: " + content.Source + " · 확보 시각 " + when.ToString("yyyy-MM-dd HH:mm:ss") + " KST";
            }
            catch (OperationCanceledException)
            {
                if (!IsDisposed && !cancel.IsCancellationRequested) status.Text = "자막 조회 시간이 초과됐습니다. 내용 확보는 완료되지 않았습니다.";
            }
            catch (Exception ex)
            {
                if (IsDisposed || cancel.IsCancellationRequested) return;
                status.Text = ex is ContentUnavailable || ex is InvalidDataException ? ex.Message :
                    ex is IOException ? "자막 저장·읽기에 실패했습니다. 내용 확보를 완료 처리하지 않았습니다." :
                    "자막을 가져오지 못했습니다. 접근 제한이나 네트워크 문제일 수 있습니다. 내용 확보는 완료되지 않았습니다.";
            }
            finally
            {
                busy = false;
                if (!IsDisposed && !cancel.IsCancellationRequested) refresh.Enabled = true;
            }
        }
    }
}
