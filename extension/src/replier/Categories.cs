using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Web;

namespace ReplierDesktop
{
    public sealed class VideoCategory
    {
        public string Id, Label, Genre;
        public string[] Seeds;
        public VideoCategory(string id,string label,string genre,params string[] seeds)
        { Id=id;Label=label;Genre=genre;Seeds=seeds; }
    }
    public static class VideoCategories
    {
        // Standard upload categories, not topic IDs. No API key or account is used.
        // https://developers.google.com/youtube/v3/docs/videoCategories
        public static readonly VideoCategory[] All={
            new VideoCategory("all","전체 카테고리","","요즘 화제","한국 브이로그","다큐멘터리","콘텐츠 추천"),
            new VideoCategory("1","영화/애니메이션","Film & Animation","영화 리뷰","애니메이션 추천","단편 영화","영화 해석"),
            new VideoCategory("2","자동차/교통","Autos & Vehicles","신차 리뷰","자동차 시승","전기차","자동차 관리"),
            new VideoCategory("10","음악","Music","신곡","라이브 공연","커버 노래","음악 추천"),
            new VideoCategory("15","애완동물/동물","Pets & Animals","강아지","고양이","반려동물","야생동물"),
            new VideoCategory("17","스포츠","Sports","축구","야구","농구","스포츠 하이라이트"),
            new VideoCategory("19","여행/이벤트","Travel & Events","국내 여행","해외 여행","여행 브이로그","여행 추천"),
            new VideoCategory("20","게임","Gaming"),
            new VideoCategory("22","인물/블로그","People & Blogs","일상 브이로그","직장인 브이로그","주말 일상","시골 생활"),
            new VideoCategory("23","코미디","Comedy","상황극","스케치 코미디","웃긴 영상","코미디"),
            new VideoCategory("24","엔터테인먼트","Entertainment","예능","연예인 인터뷰","웹예능","토크쇼"),
            new VideoCategory("25","뉴스/정치","News & Politics","오늘 뉴스","시사","정치 뉴스","국제 뉴스"),
            new VideoCategory("26","노하우/스타일","Howto & Style","생활 꿀팁","요리 레시피","패션 코디","집 정리"),
            new VideoCategory("27","교육","Education","역사 이야기","영어 공부","수학 강의","지식"),
            new VideoCategory("28","과학기술","Science & Technology","과학 이야기","신기술","스마트폰 리뷰","우주 과학"),
            new VideoCategory("29","비영리/사회운동","Nonprofits & Activism","자원봉사","환경 보호","사회 공헌","동물 보호")
        };
        public static int Index(string id) { return Array.FindIndex(All,c=>c.Id==id); }
        public static string Label(string id) { return All.First(c=>c.Id==id).Label; }
        public static string[] Seeds(string id)
        {
            if(Index(id)<0) throw new ArgumentException("카테고리 설정을 확인해 주세요.");
            return id=="20" ? TopicService.Seeds : All[Index(id)].Seeds;
        }
    }
    public static class KoreanVideos
    {
        public static bool TitleMatches(string title)
        {
            int korean=Regex.Matches(title ?? "",@"[가-힣]").Count;
            int other=Regex.Matches(title ?? "",@"[\u3400-\u9fff\u3040-\u30ff]").Count;
            return korean>=2 && korean>=other;
        }
        public static bool ContentMatches(VideoContent content)
        {
            string original=content.OriginalLanguage;
            if(string.IsNullOrEmpty(original) && content.IsAuto) original=content.Language;
            return (original=="ko" || (original ?? "").StartsWith("ko-")) &&
                (content.Language=="ko" || (content.Language ?? "").StartsWith("ko-"));
        }
    }
    public static class CategoryService
    {
        static string Attribute(string tag,string name)
        {
            var match=Regex.Match(tag,@"(?:^|\s)"+name+@"\s*=\s*([""'])?(?(1)(.*?)\1|([^\s>]+))",RegexOptions.IgnoreCase);
            return match.Success ? HttpUtility.HtmlDecode(match.Groups[2].Success ? match.Groups[2].Value : match.Groups[3].Value) : null;
        }
        public static string Parse(string html,string expectedId)
        {
            if(!VideoSearch.ValidId(expectedId)) throw new ArgumentException("유효하지 않은 영상 ID입니다.");
            string canonical=null,genre=null;
            foreach(Match match in Regex.Matches(html,@"<meta\b[^>]*>",RegexOptions.IgnoreCase))
            {
                string tag=match.Value;
                if(Attribute(tag,"property")=="og:url") canonical=Attribute(tag,"content");
                if(Attribute(tag,"itemprop")=="genre") genre=Attribute(tag,"content");
            }
            Uri uri;
            if(!Uri.TryCreate(canonical,UriKind.Absolute,out uri) || uri.Scheme!="https" ||
                (uri.Host!="www.youtube.com" && uri.Host!="youtube.com") || uri.AbsolutePath!="/watch" ||
                HttpUtility.ParseQueryString(uri.Query)["v"]!=expectedId) return null;
            var category=VideoCategories.All.FirstOrDefault(c=>c.Id!="all" && c.Genre==genre);
            return category==null ? null : category.Id;
        }
        public static async Task<string> Fetch(Video video,CancellationToken token)
        {
            if(video==null || !VideoSearch.ValidId(video.Id)) throw new ArgumentException("유효하지 않은 영상 ID입니다.");
            using(var handler=new HttpClientHandler {UseCookies=false,AllowAutoRedirect=false})
            using(var client=new HttpClient(handler) {Timeout=TimeSpan.FromSeconds(20)})
            {
                client.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0");
                using(var response=await client.GetAsync("https://www.youtube.com/watch?v="+video.Id+"&hl=en&gl=KR",HttpCompletionOption.ResponseHeadersRead,token).ConfigureAwait(false))
                {
                    response.EnsureSuccessStatusCode();
                    await response.Content.LoadIntoBufferAsync(8*1024*1024).ConfigureAwait(false);
                    token.ThrowIfCancellationRequested();
                    string html=await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                    CommentCounts.CapturePage(video,html);
                    return Parse(html,video.Id);
                }
            }
        }
    }
}
