using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;

namespace ReplierDesktop
{
    public sealed class Topic
    {
        public string Term { get; set; }
        public string Source { get; set; }
    }

    public sealed class History
    {
        public string Query { get; set; }
        public int Cursor { get; set; }
        public string CategoryId { get; set; }
        public List<string> Seen { get; set; }
        public string Selected { get; set; }
        public History() { Query = ""; CategoryId = "20"; Seen = new List<string>(); Selected = ""; }
    }

    public sealed class TopicBatch
    {
        public List<Topic> Topics = new List<Topic>();
        public int FailedSources;
        public int NextCursor;
        public DateTime CheckedAt;
    }

    public static class TopicService
    {
        public static readonly string[] Seeds = {
            "스팀 신작 게임", "게임 웃긴 장면", "공포 게임", "게임 보스 공략",
            "인디 게임 추천", "게임 챌린지", "생존 게임", "게임 업데이트",
            "오픈월드 게임", "게임 버그", "협동 게임", "게임 스토리",
            "게임 초보 공략", "추억의 게임", "게임 숨겨진 요소", "무료 게임 추천",
            "로그라이크 게임", "게임 명장면", "시뮬레이션 게임", "게임 리뷰"
        };
        static readonly string[] Suffixes = { "공략", "웃긴 장면", "초보", "보스", "업데이트",
            "챌린지", "스토리", "버그", "숨겨진 요소", "리뷰", "직업", "팁" };

        public static string Key(string text)
        {
            return Regex.Replace(text.Normalize(NormalizationForm.FormKC).Trim(), @"\s+", " ").ToUpperInvariant();
        }

        public static List<string> Parse(string json, string query)
        {
            var data = new JavaScriptSerializer().DeserializeObject(json) as object[];
            if (data == null || data.Length < 2 || !(data[0] is string) || (string)data[0] != query || !(data[1] is object[]))
                throw new InvalidDataException("YouTube 추천 응답 형식이 변경되었습니다.");
            var found = new List<string>();
            var seen = new HashSet<string>();
            foreach (var item in (object[])data[1])
            {
                if (!(item is string)) throw new InvalidDataException("추천 검색어를 읽지 못했습니다.");
                var term = ((string)item).Normalize(NormalizationForm.FormKC).Trim();
                if (term.Length == 0 || term.Length > 200 || term.Any(char.IsControl) || !seen.Add(Key(term))) continue;
                found.Add(term);
                if (found.Count == 10) break;
            }
            return found;
        }

        static async Task<List<string>> Fetch(string seed, CancellationToken token)
        {
            using (var client = new HttpClient())
            {
                client.Timeout = TimeSpan.FromSeconds(14);
                client.DefaultRequestHeaders.UserAgent.ParseAdd("24HReplier/0.2");
                var url = "https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=ko&gl=KR&q=" + Uri.EscapeDataString(seed);
                using (var response = await client.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, token).ConfigureAwait(false))
                {
                    response.EnsureSuccessStatusCode();
                    await response.Content.LoadIntoBufferAsync(256000).ConfigureAwait(false);
                    var bytes = await response.Content.ReadAsByteArrayAsync().ConfigureAwait(false);
                    token.ThrowIfCancellationRequested();
                    return Parse(Encoding.UTF8.GetString(bytes), seed);
                }
            }
        }

        public static async Task<TopicBatch> Discover(string query, IEnumerable<string> excluded, int cursor,
            CancellationToken token, Func<string, CancellationToken, Task<List<string>>> fetch = null,string category="20")
        {
            query = (query ?? "").Normalize(NormalizationForm.FormKC).Trim();
            if (query.Length > 80 || query.Any(char.IsControl)) throw new ArgumentException("관심 주제는 80자 이내로 입력해 주세요.");
            var suffixes = category=="20" ? Suffixes : new[]{"추천","리뷰","이야기","최근"};
            var seeds = query.Length == 0 || (category=="20" && query == "게임") ? VideoCategories.Seeds(category) : suffixes.Select(s => query + " " + s).ToArray();
            var getter = fetch ?? Fetch;
            var seen = new HashSet<string>(excluded.Select(Key));
            var batch = new TopicBatch { NextCursor = cursor, CheckedAt = DateTime.UtcNow };
            bool receivedResponse = false;
            // A spent group must not trap the picker on the same four seeds forever.
            // Search each group at most once; keep both keyword and video exclusions intact.
            int groups = (seeds.Length + 3) / 4;
            for(int round = 0; round < groups; round++)
            {
                token.ThrowIfCancellationRequested();
                int current = (cursor + round) % 1000001;
                var chosen = Enumerable.Range(0,4).Select(i => seeds[((current % seeds.Length)*4+i)%seeds.Length]).ToArray();
                var tasks = chosen.Select(async seed => {
                    try { return await getter(seed,token).ConfigureAwait(false); }
                    catch(OperationCanceledException) { if(token.IsCancellationRequested) throw; return null; }
                    catch(HttpRequestException) { return null; }
                    catch(InvalidDataException) { return null; }
                    catch(ArgumentException) { return null; }
                }).ToArray();
                var results = await Task.WhenAll(tasks).ConfigureAwait(false);
                token.ThrowIfCancellationRequested();
                receivedResponse |= results.Any(r=>r != null);
                batch.NextCursor = (current+1)%1000001;
                batch.FailedSources += results.Count(r=>r == null);
                for(int i=0;i<10 && batch.Topics.Count<12;i++)
                {
                    for(int j=0;j<results.Length && batch.Topics.Count<12;j++)
                    {
                        if(results[j] == null || i>=results[j].Count) continue;
                        var term=results[j][i];
                        if(seen.Add(Key(term))) batch.Topics.Add(new Topic { Term=term,Source=chosen[j] });
                    }
                }
                if(batch.Topics.Count>0) return batch;
            }
            if(!receivedResponse) throw new IOException("YouTube 추천에 연결하지 못했습니다. 인터넷 연결을 확인하고 다시 눌러주세요.");
            return batch;
        }
    }

    public sealed class HistoryStore
    {
        readonly string path;
        public HistoryStore(string file) { path = file; }
        public History Load()
        {
            if (!File.Exists(path)) return new History();
            var state = new JavaScriptSerializer().Deserialize<History>(File.ReadAllText(path, Encoding.UTF8));
            if (state == null || state.Seen == null || state.Query == null || state.Cursor < 0 || state.Cursor > 1000000 ||
                state.Seen.Any(t => t == null || t.Length > 200)) throw new InvalidDataException("추천 이력을 읽지 못했습니다.");
            state.Seen = state.Seen.Skip(Math.Max(0, state.Seen.Count - 300)).ToList();
            return state;
        }
        public void Save(History state)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            string temp = path + ".new";
            File.WriteAllText(temp, new JavaScriptSerializer().Serialize(state), new UTF8Encoding(false));
            if (File.Exists(path)) File.Replace(temp, path, null);
            else File.Move(temp, path);
        }
    }

    public sealed class MainForm : Form
    {
        readonly TextBox query = new TextBox();
        readonly ComboBox uploadPeriod = new ComboBox();
        readonly ComboBox category = new ComboBox();
        readonly SettingsStore settingsStore;
        ReplierSettings settings;
        bool restoringSettings;
        readonly Button recommend = new Button();
        readonly ComboBox searchMode = new ComboBox();
        readonly string[] modeInputs = new string[4];
        int priorMode=1;
        readonly LocalModel channelModel;
        [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern IntPtr SendMessage(IntPtr h,int message,IntPtr w,string l);
        readonly Button stop = new Button();
        readonly DataGridView grid = new DataGridView();
        readonly Label status = new Label();
        readonly Label selectedQuery = new Label();
        readonly DataGridView commentGrid = new DataGridView();
        readonly Button refreshComments = new Button();
        readonly Button postComment = new Button();
        readonly Button copyDebug = new Button();
        readonly Button openVideo = new Button();
        readonly Action<string> copyToClipboard;
        DualCommentResult debugResult;
        string debugError="";
        string debugEvidence="";
        readonly IYoutubePublisher publisher;
        readonly ToolStripLabel connectedYoutube=new ToolStripLabel();
        readonly ToolStripMenuItem connectYoutube=new ToolStripMenuItem("유튜브 연결…"){Name="YoutubeConnectionMenu"};
        bool restoringYoutube;
        string youtubeRestoreError="";
        public Task ConnectionTask {get;private set;}
        readonly Label commentStatus = new Label();
        readonly DualCommentService comments;
        CancellationTokenSource commentCancellation;
        public Task SelectionTask { get; private set; }
        readonly CancellationTokenSource closing = new CancellationTokenSource();
        CancellationTokenSource running;
        readonly HistoryStore historyStore;

        readonly ContentStore contentStore;
        History history;
        List<Video> videos = new List<Video>();
        Video currentVideo;
        Task warmupTask=Task.FromResult(0);
        bool busy;
        bool sortingVideos;
        bool incompleteComments;
        bool needsFitRetry;
        int pictureVersion;
        readonly Color green = Color.FromArgb(19, 110, 88);

        public MainForm(string historyPath,IYoutubePublisher youtube=null,Action<string> clipboardWriter=null)
        {
            copyToClipboard=clipboardWriter ?? (text=>Clipboard.SetText(text,TextDataFormat.UnicodeText));
            historyStore = new HistoryStore(historyPath);
            string directory = Path.GetDirectoryName(historyPath);
            settingsStore = new SettingsStore(Path.Combine(directory,"settings.json"));
            settings = new ReplierSettings();

            publisher=youtube ?? new YoutubePublisher(new EncryptedYoutubeCredentialStore(Path.Combine(directory,"youtube-private","connection.bin")));
            contentStore = new ContentStore(Path.Combine(directory, "content"));
            string extension = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", ".."));
            comments = new DualCommentService(Path.Combine(extension, ".runtime", "replier-llm"));
            channelModel = new LocalModel(Path.Combine(extension,".runtime","replier-llm"),LocalModel.Model,true);
            SelectionTask = Task.FromResult(0);
            ConnectionTask = Task.FromResult(0);
            history = new History();
            string warning = "";
            try { history = historyStore.Load(); }
            catch (Exception) { warning = "이전 검색어 이력을 읽지 못했습니다. 검색 기능은 계속 사용할 수 있습니다."; }
            try { settings = settingsStore.Load(); }
            catch(Exception) { warning = "업로드 필터 설정을 읽지 못해 기본값으로 시작합니다. 필터를 다시 선택해 주세요."; }
            Text = "24HReplier · 김실버의 댓글 연구실";
            Font = new Font("맑은 고딕", 10);
            BackColor = Color.FromArgb(244, 246, 242);
            ClientSize = new Size(1120, 800);
            MinimumSize = new Size(760, 520);
            StartPosition = FormStartPosition.CenterScreen;
            AutoScaleDimensions = new SizeF(96, 96);
            AutoScaleMode = AutoScaleMode.Dpi;
            Icon = SystemIcons.Application;
            var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 4, Padding = new Padding(16, 12, 16, 12) };
            layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            int[] heights = { 44, 28, 26, 0 };
            for(int i=0;i<heights.Length;i++)
                layout.RowStyles.Add(i==3 ? new RowStyle(SizeType.Percent,100) : new RowStyle(SizeType.Absolute,heights[i]));
            Controls.Add(layout);
            var menu=new MenuStrip{Name="AppMenu",Dock=DockStyle.Top,Font=Font};
            var menuRoot=new ToolStripMenuItem("메뉴"){Name="MainMenu"};
            connectYoutube.Click+=async(sender,e)=>{
                using(var dialog=new YoutubeConnectionDialog(publisher)){
                    dialog.ShowDialog(this);
                    await dialog.OperationTask;
                }
                youtubeRestoreError="";
                if(!IsDisposed && !closing.IsCancellationRequested)UpdateYoutubeConnection();
            };
            menuRoot.DropDownItems.Add(connectYoutube);menu.Items.Add(menuRoot);
            connectedYoutube.Name="ConnectedYoutubeChannel";connectedYoutube.Alignment=ToolStripItemAlignment.Right;
            connectedYoutube.AutoSize=false;connectedYoutube.Width=270;connectedYoutube.TextAlign=ContentAlignment.MiddleRight;
            menu.Items.Add(connectedYoutube);MainMenuStrip=menu;Controls.Add(menu);

            var controls = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 6, Margin = Padding.Empty };
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 155));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 120));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 125));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 90));
            controls.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 55));
            searchMode.Name="SearchMode";
            searchMode.AccessibleName="검색 방식";
            searchMode.DropDownStyle=ComboBoxStyle.DropDownList;
            searchMode.Dock=DockStyle.Fill;
            searchMode.Margin=new Padding(0,6,8,0);
            searchMode.Items.AddRange(new[]{"검색어 검색","자동 검색어 추천","채널 내용으로 추천","인급동 추천"});
            priorMode=settings.SearchMode;
            searchMode.SelectedIndex=priorMode;
            searchMode.DropDownWidth=190;
            searchMode.SelectedIndexChanged+=(sender,e)=>{
                modeInputs[priorMode]=query.Text;
                priorMode=searchMode.SelectedIndex;
                query.Text=modeInputs[priorMode] ?? "";
                UpdateSearchControls();
            };
            controls.Controls.Add(searchMode,0,0);            category.Name = "Category";
            category.AccessibleName = "영상 카테고리";
            category.DropDownStyle = ComboBoxStyle.DropDownList;
            category.DropDownWidth = 240;
            category.Dock = DockStyle.Fill;
            category.Margin = new Padding(0,6,8,0);
            category.Items.AddRange(VideoCategories.All.Select(c=>c.Label).ToArray());
            category.SelectedIndex = VideoCategories.Index(settings.CategoryId);
            category.SelectedIndexChanged += (sender,e)=>SaveUploadPeriod();
            controls.Controls.Add(category,1,0);
            uploadPeriod.Name = "UploadPeriod";
            uploadPeriod.AccessibleName = "업로드 기간";
            uploadPeriod.DropDownStyle = ComboBoxStyle.DropDownList;
            uploadPeriod.Dock = DockStyle.Fill;
            uploadPeriod.Margin = new Padding(0,6,8,0);
            uploadPeriod.Items.AddRange(UploadPeriods.Labels);
            uploadPeriod.SelectedIndex = UploadPeriods.Index(settings.UploadPeriod);
            uploadPeriod.SelectedIndexChanged += (sender,e)=>SaveUploadPeriod();
            controls.Controls.Add(uploadPeriod,2,0);
            query.Name = "Query";
            query.MaxLength = 300;
            query.HandleCreated+=(sender,e)=>UpdateSearchControls();
            query.Dock = DockStyle.Fill;
            query.Margin = new Padding(0, 6, 12, 0);
            controls.Controls.Add(query, 3, 0);
            recommend.Name = "Recommend";
            recommend.Text = "가져오기";
            recommend.Dock = DockStyle.Fill;
            recommend.BackColor = green;
            recommend.ForeColor = Color.White;
            recommend.FlatStyle = FlatStyle.Flat;
            recommend.FlatAppearance.BorderSize = 0;
            recommend.Click += async (sender, e) => await AcquireVideos();
            controls.Controls.Add(recommend, 4, 0);
            stop.Text = "중지";
            stop.Dock = DockStyle.Fill;
            stop.Enabled = false;
            stop.Click += (sender, e) => { if (running != null) running.Cancel(); if (commentCancellation != null) commentCancellation.Cancel(); };
            stop.Name="Stop";
            controls.Controls.Add(stop, 5, 0);
            layout.Controls.Add(controls, 0, 0);
            selectedQuery.Name = "SelectedQuery";
            selectedQuery.Text = "";
            selectedQuery.Dock = DockStyle.Fill;
            selectedQuery.ForeColor = green;
            selectedQuery.TextAlign = ContentAlignment.MiddleLeft;
            selectedQuery.AutoEllipsis = true;
            layout.Controls.Add(selectedQuery, 0, 1);
            status.Name = "BatchStatus";
            status.Text = warning;
            status.Dock = DockStyle.Fill;
            status.ForeColor = Color.FromArgb(95, 112, 101);
            layout.Controls.Add(status, 0, 2);
            grid.Name = "Videos";
            grid.Dock = DockStyle.Fill;
            grid.ReadOnly = true;
            grid.AllowUserToAddRows = false;
            grid.AllowUserToDeleteRows = false;
            grid.RowHeadersVisible = false;
            grid.MultiSelect = false;
            grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
            grid.BackgroundColor = Color.White;
            grid.BorderStyle = BorderStyle.None;
            grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
            grid.EnableHeadersVisualStyles = false;
            grid.ColumnHeadersDefaultCellStyle.BackColor = Color.FromArgb(229, 238, 229);
            grid.ColumnHeadersHeight = 34;
            grid.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            grid.RowTemplate.Height = 26;
            grid.DefaultCellStyle.SelectionBackColor = Color.FromArgb(219, 238, 224);
            grid.DefaultCellStyle.SelectionForeColor = Color.FromArgb(20, 65, 44);
            grid.Columns.Add("title", "추천 영상");
            grid.Columns.Add("channel", "채널");
            grid.Columns.Add("duration", "영상 길이");
            grid.Columns.Add("views", "조회수");
            grid.Columns.Add("published", "업로드");
            grid.Columns.Add("comments", "댓글 수");
            grid.Columns[0].FillWeight = 39;
            grid.Columns[1].FillWeight = 18;
            grid.Columns[2].FillWeight = 10;
            grid.Columns[3].FillWeight = 13;
            grid.Columns[4].FillWeight = 11;
            grid.Columns[5].FillWeight = 9;
            grid.Columns["comments"].SortMode = DataGridViewColumnSortMode.Programmatic;
            grid.Columns["views"].SortMode = DataGridViewColumnSortMode.Programmatic;
            grid.ColumnHeaderMouseClick += (sender,e)=>{
                string name=grid.Columns[e.ColumnIndex].Name;
                if(name!="comments" && name!="views")return;
                sortingVideos=true;
                try {GridSorting.Toggle(grid,name);}finally {sortingVideos=false;}
            };
            grid.SelectionChanged += (sender, e) => { if(!sortingVideos) SelectionTask = ShowSelectedVideo(); };
            grid.CellClick += (sender,e) => {
                var clicked=e.RowIndex>=0 ? grid.Rows[e.RowIndex].Tag as Video : null;
                if(clicked!=null && currentVideo!=null && clicked.Id==currentVideo.Id && SelectionTask.IsCompleted)
                    SelectionTask = ShowSelectedVideo();
            };
            var lists = new SplitContainer { Name = "ListSplit", Dock = DockStyle.Fill,
                Orientation = Orientation.Horizontal, Size = new Size(900, 500),
                SplitterWidth = 8, Panel1MinSize = 80, Panel2MinSize = 120,
                SplitterDistance = 210, Margin = Padding.Empty };
            lists.BackColor = Color.FromArgb(216, 224, 216);
            lists.Panel1.BackColor = BackColor;
            lists.Panel2.BackColor = BackColor;
            lists.Panel1.Controls.Add(grid);
            layout.Controls.Add(lists, 0, 3);
            var commentPanel = new TableLayoutPanel { Dock = DockStyle.Fill, RowCount = 2, ColumnCount = 1, Margin = Padding.Empty };
            commentPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            commentPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
            commentPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            commentStatus.Name = "CommentStatus";
            commentStatus.Text = "";
            commentStatus.Dock = DockStyle.Fill;
            commentStatus.ForeColor = green;
            commentStatus.AutoEllipsis = true;
            var commentHeader = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 5, Margin = Padding.Empty };
            commentHeader.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
            commentHeader.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,160));
            commentHeader.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,170));
            commentHeader.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,130));
            commentHeader.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,90));
            commentHeader.Controls.Add(commentStatus,0,0);
            openVideo.Name="OpenVideo";openVideo.Text="영상 열기";openVideo.Dock=DockStyle.Fill;openVideo.Enabled=false;
            openVideo.Click+=(sender,e)=>{if(currentVideo==null||!VideoSearch.ValidId(currentVideo.Id))return;try{System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo("https://www.youtube.com/watch?v="+currentVideo.Id){UseShellExecute=true});}catch(System.ComponentModel.Win32Exception){MessageBox.Show(this,"브라우저를 열지 못했습니다.","영상 열기");}};
            commentHeader.Controls.Add(openVideo,4,0);
            refreshComments.Name = "RefreshComments";
            refreshComments.Text = "댓글 다시 생성";
            refreshComments.Dock = DockStyle.Fill;
            refreshComments.Enabled = false;
            refreshComments.Click += async (sender,e) => { SelectionTask = RefreshComments(); await SelectionTask; };
            copyDebug.Name="CopyCommentDebug";copyDebug.Text="디버깅 정보 복사";copyDebug.Dock=DockStyle.Fill;copyDebug.Enabled=false;
            copyDebug.Click+=(sender,e)=>CopyCommentDebug();
            commentHeader.Controls.Add(copyDebug,1,0);
            commentHeader.Controls.Add(refreshComments,2,0);
            postComment.Name="PostComment";postComment.Text="댓글 게시…";postComment.Dock=DockStyle.Fill;postComment.Enabled=false;
            postComment.Click+=(sender,e)=>{
                if(currentVideo==null || commentGrid.Rows.Count!=1)return;
                var suggestion=commentGrid.Rows[0].Tag as CommentSuggestion;
                if(suggestion==null)return;
                using(var dialog=new YoutubePostDialog(currentVideo,suggestion.Text,publisher))dialog.ShowDialog(this);
                UpdateYoutubeConnection();
            };
            commentHeader.Controls.Add(postComment,3,0);
            commentGrid.RowsAdded+=(sender,e)=>postComment.Enabled=currentVideo!=null && commentGrid.Rows.Count==1;
            commentGrid.RowsRemoved+=(sender,e)=>postComment.Enabled=currentVideo!=null && commentGrid.Rows.Count==1;
            commentPanel.Controls.Add(commentHeader, 0, 0);
            commentGrid.Name = "Comments";
            commentGrid.Dock = DockStyle.Fill;
            commentGrid.ReadOnly = true;
            commentGrid.AllowUserToAddRows = false;
            commentGrid.AllowUserToDeleteRows = false;
            commentGrid.RowHeadersVisible = false;
            commentGrid.MultiSelect = false;
            commentGrid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
            commentGrid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
            commentGrid.AutoSizeRowsMode = DataGridViewAutoSizeRowsMode.None;
            commentGrid.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            commentGrid.ColumnHeadersDefaultCellStyle.WrapMode = DataGridViewTriState.False;
            commentGrid.RowTemplate.MinimumHeight = 26;
            commentGrid.RowTemplate.Height = 30;
            commentGrid.DefaultCellStyle.WrapMode = DataGridViewTriState.False;
            commentGrid.BackgroundColor = Color.White;
            commentGrid.BorderStyle = BorderStyle.None;
            commentGrid.Columns.Add("model", "모델");
            commentGrid.Columns.Add("text", "추천 댓글");
            commentGrid.Columns.Add("evidence", "참고 대사 · 시각");
            commentGrid.Columns.Add("fit", "적합도");
            commentGrid.Columns["fit"].SortMode = DataGridViewColumnSortMode.Programmatic;
            commentGrid.ColumnHeaderMouseClick += (sender,e)=>{
                if(commentGrid.Columns[e.ColumnIndex].Name=="fit")GridSorting.Toggle(commentGrid,"fit");
            };
            commentGrid.CellClick+=(sender,e)=>{if(e.RowIndex>=0 && e.ColumnIndex>=0 && commentGrid.Columns[e.ColumnIndex].Name=="fit")ShowFitDetails(commentGrid.Rows[e.RowIndex]);};
            commentGrid.CellMouseEnter+=(sender,e)=>{commentGrid.Cursor=e.RowIndex>=0 && e.ColumnIndex>=0 && commentGrid.Columns[e.ColumnIndex].Name=="fit" ? Cursors.Hand : Cursors.Default;};
            commentGrid.Columns["fit"].MinimumWidth = 76;
            commentGrid.Columns["model"].MinimumWidth = 65;
            commentGrid.Columns["fit"].HeaderCell.ToolTipText = "점수를 클릭하면 선정 이유와 항목별 평가를 볼 수 있습니다. Gemma 50점 + Qwen 50점의 합계. 제목·발췌 자막 기준 AI 평가입니다. 일반 감상은 각 모델 최대 35점이며 정확할 확률이나 유머 점수가 아닙니다.";
            commentGrid.Columns[0].FillWeight = 9;
            commentGrid.Columns[1].FillWeight = 58;
            commentGrid.Columns[2].FillWeight = 25;
            commentGrid.Columns[3].FillWeight = 8;
            commentPanel.Controls.Add(commentGrid, 0, 1);
            lists.Panel2.Controls.Add(commentPanel);
            grid.ScrollBars = ScrollBars.Both;
            commentGrid.ScrollBars = ScrollBars.Both;
            Shown += (sender,e) => {
                FitToWorkingArea(true);
                int target = grid.ColumnHeadersHeight + grid.RowTemplate.Height * 10 + 2;
                lists.SplitterDistance = Math.Max(lists.Panel1MinSize,
                    Math.Min(target, lists.Height-lists.SplitterWidth-lists.Panel2MinSize));
            };
            Shown+=(sender,e)=>{ConnectionTask=RestoreYoutubeConnection();warmupTask=PrepareModelsAtStartup();};
            ResizeEnd += (sender,e) => FitToWorkingArea(false);
            AcceptButton = recommend;
            FormClosing += (sender, e) => { closing.Cancel(); if (running != null) running.Cancel(); if (commentCancellation != null) commentCancellation.Cancel(); };
            UpdateYoutubeConnection();
            FormClosed += (sender, e) => { comments.Dispose(); channelModel.Dispose();var disposablePublisher=publisher as IDisposable;if(disposablePublisher!=null)disposablePublisher.Dispose(); };
        }

        void FitToWorkingArea(bool center)
        {
            if(WindowState != FormWindowState.Normal) return;
            var area = Screen.FromControl(this).WorkingArea;
            // Bounds are physical pixels here, after WinForms applies display scaling.
            var available = new Rectangle(area.X + 8, area.Y + 8,
                Math.Max(1, area.Width - 16), Math.Max(1, area.Height - 16));
            MinimumSize = new Size(Math.Min(MinimumSize.Width, available.Width),
                Math.Min(MinimumSize.Height, available.Height));
            int width = Math.Min(Width, available.Width), height = Math.Min(Height, available.Height);
            int x = center ? available.X + (available.Width - width) / 2 :
                Math.Max(available.Left, Math.Min(Left, available.Right - width));
            int y = center ? available.Y + (available.Height - height) / 2 :
                Math.Max(available.Top, Math.Min(Top, available.Bottom - height));
            Bounds = new Rectangle(x,y,width,height);
        }

        bool SaveSearchSelection(int mode)
        {
            var selected=new ReplierSettings{SearchMode=mode,UploadPeriod=UploadPeriods.Keys[uploadPeriod.SelectedIndex],CategoryId=VideoCategories.All[category.SelectedIndex].Id};
            try{settingsStore.Save(selected);settings=selected;return true;}
            catch(Exception){status.Text="검색 설정을 저장하지 못했습니다. 저장 경로를 확인한 뒤 다시 눌러 주세요.";return false;}
        }
        void SaveUploadPeriod()
        {
            if(restoringSettings || uploadPeriod.SelectedIndex<0 || category.SelectedIndex<0) return;
            string prior = settings.UploadPeriod;
            string priorCategory = settings.CategoryId;
            settings.UploadPeriod = UploadPeriods.Keys[uploadPeriod.SelectedIndex];
            settings.CategoryId = VideoCategories.All[category.SelectedIndex].Id;
            try { settingsStore.Save(settings); }
            catch(Exception)
            {
                settings.UploadPeriod = prior;
                settings.CategoryId = priorCategory;
                restoringSettings = true;
                uploadPeriod.SelectedIndex = UploadPeriods.Index(prior);
                category.SelectedIndex = VideoCategories.Index(priorCategory);
                restoringSettings = false;
                status.Text = "필터 설정을 저장하지 못해 이전 값으로 되돌렸습니다. 저장 경로를 확인해 주세요.";
            }
            UpdateSearchControls();
        }

        void ClearVideo()
        {
            pictureVersion++;
            currentVideo = null;openVideo.Enabled=false;
            debugResult=null;debugError="";debugEvidence="";copyDebug.Enabled=false;copyDebug.Text="디버깅 정보 복사";
            postComment.Enabled=false;
            incompleteComments=false;needsFitRetry=false;
            refreshComments.Text="댓글 다시 생성";
            refreshComments.Enabled = false;
            if (commentCancellation != null) commentCancellation.Cancel();
            commentGrid.Rows.Clear();
            commentStatus.Text = "";

        }

        public async Task ShowSelectedVideo()
        {
            if (busy || grid.SelectedRows.Count == 0) return;
            var video = grid.SelectedRows[0].Tag as Video;
            if(video==null) return;
            ClearVideo();forceNewCandidates=false;
            currentVideo = video;openVideo.Enabled=true;
            int version = pictureVersion;
            commentCancellation = CancellationTokenSource.CreateLinkedTokenSource(closing.Token);
            var selectionToken = commentCancellation.Token;
            commentStatus.Text = "댓글 생성 중…";
            stop.Enabled = true;
            refreshComments.Enabled = false;
            await LoadComments(video, version, selectionToken, false);
        }

        public async Task RefreshComments()
        {
            if(busy || currentVideo == null || !refreshComments.Enabled) return;
            refreshComments.Enabled = false;
            if(commentCancellation != null) commentCancellation.Cancel();
            commentCancellation = CancellationTokenSource.CreateLinkedTokenSource(closing.Token);
            int version = ++pictureVersion;
            bool regenerateAll=!incompleteComments || forceNewCandidates;
            commentStatus.Text = regenerateAll ? "댓글 다시 생성 중…" : "추천 댓글 재시도 중…";
            stop.Enabled = true;
            await LoadComments(currentVideo,version,commentCancellation.Token,regenerateAll,true);
        }

        void CopyCommentDebug()
        {
            if(currentVideo==null || !copyDebug.Enabled)return;
            var shown=commentGrid.Rows.Count==1 ? commentGrid.Rows[0].Tag as CommentSuggestion : null;
            try{copyToClipboard(CommentDebugReport.Format(currentVideo,debugResult,shown,commentStatus.Text,debugError,debugEvidence));copyDebug.Text="복사 완료";}
            catch(ExternalException){copyDebug.Text="복사 재시도";}
        }

        bool forceNewCandidates;
        static bool HasBestComment(DualCommentResult result)
        {
            return result.Complete && !result.Cancelled && string.IsNullOrEmpty(result.ScoreError)
                && result.Count>0 && result.Count<=10 && result.Batches.Count==2
                && result.Batches.All(b=>string.IsNullOrEmpty(b.Error) && b.Result!=null && (b.Result.Comments.Count==5 || (b.Result.QualityFiltered && b.Result.Comments.Count<5)))
                && result.Batches.SelectMany(b=>b.Result.Comments).Any(c=>c.FitEligible!=false)
                && result.Batches.SelectMany(b=>b.Result.Comments).Where(c=>c.FitEligible!=false).All(c=>c.FitScore.HasValue && c.FitScore>=0 && c.FitScore<=100);
        }
        void RenderComments(DualCommentResult result)
        {
            bool evaluated=HasBestComment(result);
            bool ungraded=result.Complete && !result.Cancelled && !string.IsNullOrEmpty(result.ScoreError) && result.Count>0;
            if(!evaluated && !ungraded){if(result.Complete && !result.Cancelled && string.IsNullOrEmpty(result.ScoreError) && result.Count>0 && result.Batches.Where(b=>b.Result!=null).SelectMany(b=>b.Result.Comments).All(c=>c.FitEligible==false && c.FitScore.HasValue)){commentGrid.Rows.Clear();commentGrid.Columns["fit"].HeaderCell.SortGlyphDirection=SortOrder.None;}return;}
            var selected=commentGrid.SelectedRows.Count>0 ? commentGrid.SelectedRows[0].Tag as CommentSuggestion : null;
            commentGrid.Rows.Clear();
            var ordered=result.Batches.Where(b=>b.Result!=null)
                .SelectMany(batch=>batch.Result.Comments.Where(item=>item.FitEligible!=false).Select(item=>new {Batch=batch,Item=item}))
                .ToList();
            if(evaluated)ordered=ordered.OrderByDescending(entry=>entry.Item.TiePreference).ThenByDescending(entry=>entry.Item.FitScore.Value).ToList();
            foreach(var entry in ordered.Take(1))
                {
                    var batch=entry.Batch;
                    var item=entry.Item;
                    int row=commentGrid.Rows.Add(batch.Label,item.Text,CaptionService.Timestamp(item.StartMs)+" · "+System.Text.RegularExpressions.Regex.Replace(item.GroundingQuote ?? item.Evidence,@"\s+"," "),
                        evaluated ? item.FitScore.Value+"점" : "미평가");
                    commentGrid.Rows[row].Tag=item;
                    commentGrid.Rows[row].Cells["model"].ToolTipText=batch.Model;
                    commentGrid.Rows[row].Cells["text"].ToolTipText=item.Text;
                    commentGrid.Rows[row].Cells["evidence"].ToolTipText=string.IsNullOrEmpty(item.GroundingQuote) ? item.Evidence : (currentVideo==null ? "" : "영상 제목: "+currentVideo.Title+"\n\n")+"선택한 자막 구절:\n"+item.GroundingQuote+"\n\n앞뒤 원문 자막:\n"+item.Evidence;
                    commentGrid.Rows[row].Cells["fit"].ToolTipText=evaluated ? SelectionReason(ordered.Select(e=>e.Item).ToList())+"\n\n"+item.FitReason : "평가 실패로 점수와 순위가 없는 임시 후보입니다. 생성 순서의 첫 댓글을 표시합니다.\n"+result.ScoreError;
                }
            commentGrid.Columns["fit"].HeaderCell.SortGlyphDirection = evaluated ? SortOrder.Descending : SortOrder.None;
            commentGrid.ClearSelection();
            if(selected!=null)foreach(DataGridViewRow row in commentGrid.Rows)if(object.ReferenceEquals(row.Tag,selected)){row.Selected=true;commentGrid.CurrentCell=row.Cells["text"];break;}
        }
        static string SelectionReason(IList<CommentSuggestion> ranked)
        {
            var best=ranked[0];int score=best.FitScore.Value;
            if(best.TiePreference>0 && (best.TieReason??"").Contains("구어체"))return "두 모델 근거·말투 검사 통과 "+ranked.Count+"개 중 짧고 자연스러운 반응으로 선택했습니다. 적합도 "+score+"점.\\n"+best.TieReason;
            int tied=ranked.Count(c=>c.FitScore==score);
            string summary=ranked.Count+"개 후보 중 합산 "+score+"점으로 최고점";
            if(tied>1)return summary+". 최고점 동점 "+tied+"개 중 "+(best.TiePreference>0 ? "모델의 직접 비교로 선택했습니다. "+best.TieReason : "먼저 생성된 댓글을 표시합니다.");
            if(ranked.Count>1)summary+=". 차점 "+ranked[1].FitScore.Value+"점보다 "+(score-ranked[1].FitScore.Value)+"점 높습니다.";
            if(ranked.Count>1){
                var next=ranked[1];
                if(best.FitTopicScore.HasValue && next.FitTopicScore.HasValue &&
                    best.FitTopicScore+best.FitToneScore+best.FitCareScore+best.FitLinkScore==best.FitScore &&
                    next.FitTopicScore+next.FitToneScore+next.FitCareScore+next.FitLinkScore==next.FitScore){
                    string[] labels={"주제 어울림","말투","추측 억제","내용 연결"};
                    int?[] differences={best.FitTopicScore-next.FitTopicScore,best.FitToneScore-next.FitToneScore,best.FitCareScore-next.FitCareScore,best.FitLinkScore-next.FitLinkScore};
                    summary+="\n차점과 항목별 차이: "+string.Join(" · ",differences.Select((v,i)=>labels[i]+" "+(v>0 ? "+" : "")+v+"점"));
                }
                summary+="\n차점 댓글: ‘"+next.Text+"’";
            }
            return summary;
        }
        void ShowFitDetails(DataGridViewRow row)
        {
            if(!(row.Tag is CommentSuggestion))return;
            using(var dialog=new Form{Text="댓글 선정 이유와 적합도",Font=Font,ClientSize=new Size(690,360),MinimumSize=new Size(440,260),StartPosition=FormStartPosition.CenterParent,ShowInTaskbar=false,MinimizeBox=false})
            {
                var details=new TextBox{Name="FitDetails",Multiline=true,ReadOnly=true,Dock=DockStyle.Fill,ScrollBars=ScrollBars.Vertical,Text="선택된 댓글: "+row.Cells["text"].Value+"\r\n\r\n"+row.Cells["fit"].ToolTipText.Replace("\n","\r\n")+"\r\n\r\n항목 점수는 두 모델의 판단입니다. 최고점이라는 이유만으로 내용의 정확성을 보장하지는 않습니다."};
                var close=new Button{Text="닫기",Dock=DockStyle.Bottom,Height=36,DialogResult=DialogResult.OK};
                dialog.Controls.Add(details);dialog.Controls.Add(close);dialog.CancelButton=close;dialog.ShowDialog(this);
            }
        }
        static string CommentSummary(DualCommentResult result)
        {
            if(HasBestComment(result)){int passed=result.Batches.Where(b=>b.Result!=null).Sum(b=>b.Result.Comments.Count(c=>c.FitEligible!=false));return passed==1 ? "두 모델 검사 통과 · 표시 가능한 댓글 1개 (후보 "+result.Count+"개 평가)" : "두 모델 검사 통과 "+passed+"개 중 말투 비교로 선택한 댓글 1개";}
            if(result.Complete && result.Count==0 && result.Batches.Count==2 && result.Batches.All(b=>b.Result!=null && b.Result.QualityFiltered))return "근거·말투 검사를 통과한 댓글이 없습니다. 다시 생성해 주세요.";
            if(result.Complete && !result.Cancelled && result.Count>0 && !string.IsNullOrEmpty(result.ScoreError))return "생성 댓글 "+result.Count+"개 · "+result.ScoreError+" · 다시 평가해 주세요";
            if(result.Complete && !result.Cancelled && result.Count>0 && string.IsNullOrEmpty(result.ScoreError) && result.Batches.Where(b=>b.Result!=null).SelectMany(b=>b.Result.Comments).All(c=>c.FitEligible==false))return "내용·말투 검사를 통과한 댓글이 없습니다. 다시 생성해 주세요.";
            string text="생성 후보 "+result.Count+"개";
            if(result.ActiveModel=="적합도")return text+" · 적합도 평가 중…";
            if(result.ActiveModel.Length>0) return text+" · "+result.ActiveModel+" 생성 중…";
            if(result.Cancelled) return text+" · 중지됨";
            var errors=result.Batches.Where(b=>b.Error.Length>0).Select(b=>b.Label+" · "+b.Error).ToArray();
            string summary=errors.Length>0 ? text+" · "+string.Join(" / ",errors) : "댓글 "+result.Count+"개";
            return summary+(result.ScoreError.Length>0 ? " · "+result.ScoreError : "");
        }
        async Task LoadComments(Video video,int version,CancellationToken token,bool refresh,bool retainPrevious=false)
        {
            if(!warmupTask.IsCompleted){
                commentStatus.Text="로컬 AI 준비를 기다리는 중… · 댓글 생성 전";
                var cancelled=new TaskCompletionSource<int>();
                using(token.Register(()=>cancelled.TrySetResult(0)))await Task.WhenAny(warmupTask,cancelled.Task);
                if(token.IsCancellationRequested || IsDisposed || version!=pictureVersion)return;
                await warmupTask;
            }
            var generationWatch=System.Diagnostics.Stopwatch.StartNew();
            var userToken=token;var generationLimit=CancellationTokenSource.CreateLinkedTokenSource(token);generationLimit.CancelAfter(TimeSpan.FromSeconds(180));token=generationLimit.Token;
            var elapsedTimer=new System.Windows.Forms.Timer{Interval=1000};elapsedTimer.Tick+=(s,e)=>{if(!IsDisposed&&version==pictureVersion)commentStatus.Text=System.Text.RegularExpressions.Regex.Replace(commentStatus.Text,@" · [0-9.,]+초 경과$","")+" · "+generationWatch.Elapsed.TotalSeconds.ToString("F1")+"초 경과";};elapsedTimer.Start();
            bool hadPrevious=(refresh || retainPrevious) && commentGrid.Rows.Count>0;
            debugResult=null;debugError="";debugEvidence="";copyDebug.Enabled=false;copyDebug.Text="디버깅 정보 복사";
            bool acceptingProgress=true;
            incompleteComments=true;needsFitRetry=false;
            try
            {
                var content=await Task.Run(()=>contentStore.Load(video.Id),token);
                if(content==null) throw new InvalidDataException("확보한 자막이 없어 댓글을 생성하지 않았습니다.");
                if(IsDisposed || version!=pictureVersion)return;
                debugEvidence=string.Join("\n\n",CommentService.Evidence(content,video.Title).Select(e=>e.Key+" · "+CaptionService.Timestamp(e.Value.StartMs)+"\n"+e.Value.Text));
                var progress=new Progress<DualCommentResult>(partial=>{
                    if(!acceptingProgress || IsDisposed || token.IsCancellationRequested || version!=pictureVersion) return;
                    debugResult=partial;
                    commentStatus.Text=CommentSummary(partial)+" · "+generationWatch.Elapsed.TotalSeconds.ToString("F1")+"초 경과";
                });
                var result=await comments.Generate(video,content,token,refresh,progress);
                acceptingProgress=false;
                if(IsDisposed || version!=pictureVersion) return;
                debugResult=result;
                incompleteComments=!HasBestComment(result);
                forceNewCandidates=result.Complete && !result.Cancelled && string.IsNullOrEmpty(result.ScoreError) && result.Batches.Where(b=>b.Result!=null).SelectMany(b=>b.Result.Comments).All(c=>c.FitEligible==false);
                needsFitRetry=!result.Cancelled && result.Complete && result.Count>0 && !string.IsNullOrEmpty(result.ScoreError) && result.Batches.All(b=>b.Result!=null && string.IsNullOrEmpty(b.Error));
                bool keepPrevious=hadPrevious && incompleteComments;
                if(!keepPrevious) RenderComments(result);
                commentStatus.Text=CommentSummary(result)+(keepPrevious ? " · 기존 댓글 유지" : "");
            }
            catch(OperationCanceledException)
            {
                if(!IsDisposed && version==pictureVersion) commentStatus.Text=userToken.IsCancellationRequested ? "댓글 생성 중지됨" : "전체 처리 180초 제한을 초과해 중단했습니다. 다시 시도해 주세요.";
            }
            catch(Exception ex)
            {
                if(IsDisposed || version!=pictureVersion) return;
                if(!hadPrevious) commentGrid.Rows.Clear();
                debugError=ex is InvalidDataException || ex is InvalidOperationException ? ex.Message : "댓글 생성 실패";
                commentStatus.Text=debugError;
            }
            finally
            {
                acceptingProgress=false;elapsedTimer.Stop();elapsedTimer.Dispose();generationLimit.Dispose();
                if(!IsDisposed && version==pictureVersion && !busy)
                {
                    generationWatch.Stop();
                    commentStatus.Text+=" · 소요 "+generationWatch.Elapsed.TotalSeconds.ToString("F1")+"초";
                    refreshComments.Text=needsFitRetry ? "적합도 다시 평가" : incompleteComments ? "추천 댓글 재시도" : "댓글 다시 생성";
                    stop.Enabled=false;refreshComments.Enabled=currentVideo!=null;copyDebug.Enabled=currentVideo!=null;
                }
            }
        }

        async Task RestoreYoutubeConnection()
        {
            if(publisher.Account!=null){UpdateYoutubeConnection();return;}
            restoringYoutube=true;youtubeRestoreError="";UpdateYoutubeConnection();
            try{await Task.Run(()=>publisher.Restore(closing.Token));}
            catch(MissingYoutubeConnectionException){}
            catch(OperationCanceledException){}
            catch(Exception){youtubeRestoreError="저장된 연결을 확인하지 못했습니다. 인터넷 연결을 확인하거나 메뉴 → 유튜브 연결에서 다시 연결해 주세요.";}
            finally{
                restoringYoutube=false;
                if(!IsDisposed && !closing.IsCancellationRequested)UpdateYoutubeConnection();
            }
        }
        void UpdateYoutubeConnection()
        {
            var account=publisher.Account;
            connectYoutube.Enabled=!restoringYoutube;
            connectedYoutube.Text=restoringYoutube ? "유튜브 · 자동 연결 중…" : account!=null ? "유튜브 · "+account.Title :
                youtubeRestoreError.Length>0 ? "유튜브 · 연결 확인 필요" : "유튜브 · 연결 안 됨";
            connectedYoutube.ToolTipText=account==null ? (youtubeRestoreError.Length>0 ? youtubeRestoreError : "메뉴 → 유튜브 연결") : account.Title+"\n"+account.Id;
            UpdateSearchControls();
        }
        string ChannelRecommendationInput()
        {
            if(!string.IsNullOrWhiteSpace(query.Text))return query.Text.Trim();
            return publisher.Account==null ? "" : "https://www.youtube.com/channel/"+publisher.Account.Id;
        }
        void UpdateSearchControls()
        {
            int mode=searchMode.SelectedIndex;
            query.Visible=mode!=3;
            query.MaxLength=mode==2 ? 300 : mode==1 ? 80 : 200;
            query.Enabled=!busy;
            searchMode.Enabled=!busy;
            recommend.Enabled=!busy && ((mode!=2 && mode!=3) || settings.CategoryId=="20");
            if(mode==2 && restoringYoutube && string.IsNullOrWhiteSpace(query.Text))recommend.Enabled=false;
            string hint=mode==0 ? "검색어 입력" : mode==1 ? "관심 주제 (선택)" : "유튜브 채널 링크";
            if(mode==2 && publisher.Account!=null)hint="비우면 내 채널 · "+publisher.Account.Title;
            query.AccessibleName=hint;
            if(query.IsHandleCreated)SendMessage(query.Handle,0x1501,IntPtr.Zero,hint);
        }
        async Task PrepareModelsAtStartup()
        {
            commentStatus.Text="로컬 AI 준비 중…";
            var watch=System.Diagnostics.Stopwatch.StartNew();
            var timer=new System.Windows.Forms.Timer{Interval=1000};
            timer.Tick+=(s,e)=>{if(!IsDisposed && !closing.IsCancellationRequested)commentStatus.Text="로컬 AI 준비 중… · "+watch.Elapsed.TotalSeconds.ToString("F0")+"초 (댓글 생성 전)";};timer.Start();
            try{
                await comments.PrepareFirst(closing.Token);
                if(!IsDisposed && !closing.IsCancellationRequested && currentVideo==null)commentStatus.Text="로컬 AI 준비 완료 · 두 모델 상주 중";
            }catch(OperationCanceledException){}
            catch(Exception ex){if(!IsDisposed && !closing.IsCancellationRequested)commentStatus.Text="AI 준비 확인 필요 · "+ex.Message;}
            finally{timer.Stop();timer.Dispose();}
        }
        async Task WarmWhileSearching(CancellationToken searchToken)
        {
            using(var linked=CancellationTokenSource.CreateLinkedTokenSource(searchToken,closing.Token))
            {
                try{await comments.PrepareFirst(linked.Token);}
                catch(OperationCanceledException){}
                catch(Exception){} // Generation remains available if optional warmup fails.
            }
        }
        public Task AcquireVideos(){return LoadVideos(searchMode.SelectedIndex);}
        public Task RecommendVideos() {return LoadVideos(1);}
        public Task TrendingVideos() {return LoadVideos(3);}
        async Task LoadVideos(int mode)
        {
            bool fromTrending=mode==3;
            if (busy) return;
            if(!SaveSearchSelection(mode))return;
            if(mode==2 && restoringYoutube && string.IsNullOrWhiteSpace(query.Text)){status.Text="저장된 유튜브 계정에 연결 중입니다. 잠시 후 다시 눌러 주세요.";return;}
            if((mode==2 || fromTrending) && settings.CategoryId!="20"){status.Text="채널 게임 추천과 인급동은 게임 카테고리에서 사용할 수 있습니다.";return;}
            if(mode==0 && string.IsNullOrWhiteSpace(query.Text)){status.Text="검색어를 입력해 주세요.";query.Focus();return;}
            string channelFocus=mode==2 ? ChannelRecommendationInput() : "";
            if(mode==2){try{ChannelSearch.ChannelUrl(channelFocus);}catch(ArgumentException ex){status.Text=ex.Message;return;}}
            busy = true;
            running = CancellationTokenSource.CreateLinkedTokenSource(closing.Token);
            recommend.Enabled = false;
            searchMode.Enabled = false;
            query.Enabled = false;
            uploadPeriod.Enabled = false;
            category.Enabled = false;
            stop.Enabled = true;
            grid.Enabled = false;
            ClearVideo();
            grid.Rows.Clear();
            videos.Clear();
            selectedQuery.Text = fromTrending ? "한국 게임 인급동 확인 중…" : mode==2 ? "채널의 게임 확인 중…" : mode==0 ? "검색 중…" : "검색어 찾는 중…";
            status.Text = "";
            if(mode!=2 && warmupTask.IsCompleted)warmupTask=WarmWhileSearching(running.Token);
            try
            {
                string focus = mode==2 ? channelFocus : query.Text.Trim();
                string period = settings.UploadPeriod;
                string categoryId = settings.CategoryId;
                string searchTerm;
                Func<string,CancellationToken,Task<List<Video>>> source=null;
                if(fromTrending)
                {
                    searchTerm="YouTube 한국 게임 인기 급상승";
                    selectedQuery.Text="한국 게임 인급동 · 댓글수순";
                    source=(q,t)=>TrendingSearch.Fetch(t,period);
                }
                else if(mode==0)
                {
                    searchTerm=focus;
                    selectedQuery.Text="검색어 · "+searchTerm;
                }
                else if(mode==2)
                {
                    try{await SelectionTask;}catch(OperationCanceledException){}
                    await warmupTask;
                    running.Token.ThrowIfCancellationRequested();
                    List<ChannelGame> games=null;Exception analysisError=null;
                    try{games=await ChannelSearch.Analyze(focus,channelModel,running.Token,new Progress<string>(text=>{if(!IsDisposed && busy)status.Text=text;}));}
                    catch(Exception ex){analysisError=ex;}
                    try{await channelModel.Unload();}catch(Exception){}
                    if(analysisError!=null)System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(analysisError).Throw();
                    running.Token.ThrowIfCancellationRequested();
                    string game=TopicPicker.Pick(games.Select(g=>new Topic{Term=g.Name}).ToList()).Term;
                    searchTerm=game;
                    selectedQuery.Text="채널에서 찾은 게임 · "+game+" (무작위)";
                    source=(q,t)=>ChannelSearch.SearchGame(game,period,t);
                }
                else
                {
                    var topics = await TopicService.Discover(focus, history.Seen,
                        history.Query == focus && history.CategoryId == categoryId ? history.Cursor : 0, running.Token,category:categoryId);
                    running.Token.ThrowIfCancellationRequested();
                    history.Query = focus;
                    history.CategoryId = categoryId;
                    history.Cursor = topics.NextCursor;
                    historyStore.Save(history);
                    if(topics.Topics.Count == 0)
                    {
                        selectedQuery.Text = "새 추천 검색어가 없습니다.";
                        status.Text = "관심 주제를 바꿔서 다시 추천받아 주세요.";
                        return;
                    }
                    Topic chosen = TopicPicker.Pick(topics.Topics);
                    history.Selected = chosen.Term;
                    history.Seen.Add(chosen.Term);
                    history.Seen = history.Seen.Skip(Math.Max(0, history.Seen.Count - 300)).ToList();
                    historyStore.Save(history);
                    selectedQuery.Text = "검색어 · " + chosen.Term;
                    searchTerm=chosen.Term;
                }
                var progress = new Progress<string>(message => { if (!IsDisposed && busy) status.Text = message; });
                status.Text="영상 검색 중…";
                if(mode==2 && warmupTask.IsCompleted)warmupTask=WarmWhileSearching(running.Token);
                var result = await VideoBatch.Collect(searchTerm, null, contentStore, running.Token, progress, search:source,period: period,category:categoryId,koreanOnly:true,includeCommentCounts:true);
                if (IsDisposed || closing.IsCancellationRequested) return;
                videos = result.Videos;
                foreach (var video in videos)
                {
                    var content = contentStore.Load(video.Id);
                    int row=grid.Rows.Add(video.Title, video.Channel, video.DurationText ?? "미제공", video.ViewCountText ?? "미제공", video.PublishedText ?? "미제공", video.CommentCountText ?? "미확인");
                    grid.Rows[row].Tag=video;
                }
                GridSorting.Sort(grid,"comments",true);
                grid.ClearSelection();
                status.Text = (result.Cancelled ? "중지됨 · " : "") +
                    (result.Error.Length > 0 ? result.Error : videos.Count == 0 ? (fromTrending ? "조건에 맞는 인급동 영상이 없습니다." : "조건에 맞는 영상이 없습니다.") :
                    "영상 " + videos.Count + "개") +
                    " · 한국어 · " + VideoCategories.Label(categoryId) +
                    (result.CategoryExcluded+result.CategoryUnknown>0 ? " · 카테고리 제외 "+(result.CategoryExcluded+result.CategoryUnknown)+"개" : "") +
                    (result.LanguageExcluded>0 ? " · 언어 제외 "+result.LanguageExcluded+"개" : "");
            }
            catch (OperationCanceledException)
            {
                if (!IsDisposed && !closing.IsCancellationRequested) status.Text = "추천을 중지했습니다.";
            }
            catch (Exception ex)
            {
                if (IsDisposed || closing.IsCancellationRequested) return;
                status.Text = ex is InvalidDataException || ex is ArgumentException ? ex.Message :
                    ex is IOException ? "로컬 데이터를 저장하거나 읽지 못했습니다." :
                    "YouTube 조회에 실패했습니다. 잠시 후 다시 시도해 주세요.";
            }
            finally
            {
                busy = false;
                if (!IsDisposed && !closing.IsCancellationRequested)
                {
                    recommend.Enabled = true;
                    UpdateSearchControls();
                    query.Enabled = true;
                    uploadPeriod.Enabled = true;
                    category.Enabled = true;
                    stop.Enabled = false;
                    grid.Enabled = true;
                    // Generation starts only when the user selects a video.
                }
                running.Dispose();
                running = null;
            }
        }
    }

    public static class Program
    {
        [STAThread]
        public static void Main()
        {
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            // The executable is built at extension/.runtime/replier-desktop/.
            string extension = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", ".."));
            string state = Path.Combine(extension, "data", "replier", "desktop-history.json");
            Application.Run(new MainForm(state));
        }
    }
}



