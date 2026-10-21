using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

namespace ReplierDesktop
{
    public static class TrendingSearch
    {
        public const string Source="https://www.youtube.com/gaming/trending?hl=ko&gl=KR";
        static object Get(object obj,string key){return CaptionService.Get(obj,key);}
        static IEnumerable<object> Items(object obj){return obj as object[] ?? new object[0];}
        static string Text(object obj){return Get(obj,"simpleText") as string ?? string.Concat(Items(Get(obj,"runs")).Select(r=>Get(r,"text") as string ?? ""));}
        public static List<Video> Parse(string html,string period)
        {
            UploadPeriods.Filter(period);
            object root;
            try{root=new JavaScriptSerializer{MaxJsonLength=8*1024*1024,RecursionLimit=150}.DeserializeObject(VideoSearch.ExtractData(html));}
            catch(ArgumentException){throw new InvalidDataException("게임 인급동 응답을 읽지 못했습니다.");}
            var tabs=Items(Get(Get(Get(root,"contents"),"twoColumnBrowseResultsRenderer"),"tabs"));
            var tab=tabs.Select(t=>Get(t,"tabRenderer")).FirstOrDefault(t=>object.Equals(Get(t,"selected"),true));
            var sections=Items(Get(Get(Get(tab,"content"),"sectionListRenderer"),"contents"));
            var shelves=sections.SelectMany(s=>Items(Get(Get(s,"itemSectionRenderer"),"contents"))).Select(s=>Get(s,"shelfRenderer"));
            var shelf=shelves.FirstOrDefault(s=>Text(Get(s,"title"))=="인기 급상승 동영상");
            var grid=Get(Get(shelf,"content"),"gridRenderer");
            if(grid==null)throw new InvalidDataException("YouTube 게임 인기 급상승 목록을 확인하지 못했습니다. 일반 추천으로 대체하지 않았습니다.");
            var videos=new List<Video>();
            foreach(var item in Items(Get(grid,"items")))
            {
                var card=Get(item,"gridVideoRenderer");string id=Get(card,"videoId") as string;
                if(!VideoSearch.ValidId(id))continue;
                string title=Text(Get(card,"title")),channel=Text(Get(card,"shortBylineText"));
                if(string.IsNullOrWhiteSpace(channel))channel=Text(Get(card,"ownerText"));
                if(string.IsNullOrWhiteSpace(title) || string.IsNullOrWhiteSpace(channel))continue;
                string published=Text(Get(card,"publishedTimeText"));
                if(!UploadPeriods.IncludesDisplayAge(published,period))continue;
                string duration=Text(Get(card,"lengthText"));bool skip=false;
                foreach(var overlay in Items(Get(card,"thumbnailOverlays")))
                {
                    var clock=Get(overlay,"thumbnailOverlayTimeStatusRenderer");
                    string style=Get(clock,"style") as string;
                    if(style=="LIVE" || style=="SHORTS")skip=true;
                    if(duration.Length==0)duration=Text(Get(clock,"text"));
                }
                if(skip)continue;
                string views=Text(Get(card,"viewCountText"));
                if(views.Length==0)views=Text(Get(card,"shortViewCountText"));
                videos.Add(new Video{Id=id,Title=title,Channel=channel,PublishedText=published.Length>0?published:"미제공",
                    DurationText=duration.Length>0?duration:"미제공",ViewCountText=views.Length>0?views:"미제공"});
            }
            return videos;
        }
        public static async Task<List<Video>> Fetch(CancellationToken token,string period)
        {
            using(var handler=new HttpClientHandler{UseCookies=false,AllowAutoRedirect=false})
            using(var client=new HttpClient(handler){Timeout=TimeSpan.FromSeconds(22)})
            {
                client.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0");
                using(var response=await client.GetAsync(Source,HttpCompletionOption.ResponseHeadersRead,token).ConfigureAwait(false))
                {
                    response.EnsureSuccessStatusCode();await response.Content.LoadIntoBufferAsync(8*1024*1024).ConfigureAwait(false);
                    var bytes=await response.Content.ReadAsByteArrayAsync().ConfigureAwait(false);token.ThrowIfCancellationRequested();
                    return Parse(Encoding.UTF8.GetString(bytes),period);
                }
            }
        }
    }
}
