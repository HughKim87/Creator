using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

namespace ReplierDesktop
{
    public static class CommentCounts
    {
        static IEnumerable<object> Items(object value){return value as object[] ?? new object[0];}
        static object Get(object value,string key){return CaptionService.Get(value,key);}
        static string Text(object value)
        {return Get(value,"simpleText") as string ?? string.Concat(Items(Get(value,"runs")).Select(r=>Get(r,"text") as string ?? ""));}
        public static string Normalize(string text)
        {
            var match=Regex.Match(text ?? "",@"^\s*(?:댓글\s*)?([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?\s*(?:억|만|천|[KMB])?)\s*(?:Comments?|개)?\s*$",RegexOptions.IgnoreCase);
            if(!match.Success || ViewCounts.Parse(match.Groups[1].Value+" views")<0) return null;
            return match.Groups[1].Value.Trim()+"개";
        }
        public static string HeaderCount(object value)
        {
            var map=value as Dictionary<string,object>;
            if(map!=null)
            {
                object header;
                if(map.TryGetValue("commentsHeaderRenderer",out header))
                {
                    var count=Normalize(Text(Get(header,"countText")));
                    if(count!=null)return count;
                }
                object message;
                if(map.TryGetValue("messageRenderer",out message))
                {
                    string text=Text(Get(message,"text"));
                    if(text=="Comments are turned off." || text=="댓글 사용이 중지되었습니다." || text=="댓글이 사용 중지되었습니다.") return "사용 중지";
                }
                foreach(var child in map.Values){var found=HeaderCount(child);if(found!=null)return found;}
            }
            else foreach(var child in Items(value)){var found=HeaderCount(child);if(found!=null)return found;}
            return null;
        }
        static string Continuation(object value)
        {
            var map=value as Dictionary<string,object>;
            if(map!=null)
            {
                object item;
                if(map.TryGetValue("continuationItemRenderer",out item))
                {
                    string token=Get(Get(Get(item,"continuationEndpoint"),"continuationCommand"),"token") as string;
                    if(!string.IsNullOrEmpty(token) && token.Length<=20000 && !token.Any(char.IsControl)) return token;
                }
                foreach(var child in map.Values){var found=Continuation(child);if(found!=null)return found;}
            }
            else foreach(var child in Items(value)){var found=Continuation(child);if(found!=null)return found;}
            return null;
        }
        public static void CapturePage(Video video,string html)
        {
            video.CommentCountText=null;video.CommentContinuation=null;
            // The existing category parser validates this page's canonical video ID.
            if(CategoryService.Parse(html,video.Id)==null)return;
            object root;
            try{root=new JavaScriptSerializer{MaxJsonLength=8*1024*1024,RecursionLimit=150}.DeserializeObject(VideoSearch.ExtractData(html));}
            catch(ArgumentException){return;}catch(System.IO.InvalidDataException){return;}
            var sections=Get(Get(Get(Get(Get(root,"contents"),"twoColumnWatchNextResults"),"results"),"results"),"contents");
            var section=Items(sections).Select(s=>Get(s,"itemSectionRenderer"))
                .FirstOrDefault(s=>(Get(s,"targetId") as string)=="comments-section");
            if(section==null)return;
            video.CommentCountText=HeaderCount(section);
            if(video.CommentCountText==null)video.CommentContinuation=Continuation(Get(section,"contents"));
        }
        public static async Task<string> Fetch(Video video,CancellationToken token)
        {
            token.ThrowIfCancellationRequested();
            if(!string.IsNullOrEmpty(video.CommentCountText)) return video.CommentCountText;
            if(string.IsNullOrEmpty(video.CommentContinuation)) return "미확인";
            // Only the count header is retained. Comment bodies and continuation tokens are not stored.
            try
            {
                using(var handler=new HttpClientHandler {UseCookies=false,AllowAutoRedirect=false})
                using(var client=new HttpClient(handler){Timeout=TimeSpan.FromSeconds(15)})
                {
                    client.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0");
                    var body=new {context=new {client=new {clientName="WEB",clientVersion="2.20261015.01.00",hl="en",gl="KR"}},continuation=video.CommentContinuation};
                    using(var request=new StringContent(new JavaScriptSerializer().Serialize(body),Encoding.UTF8,"application/json"))
                    using(var response=await client.PostAsync("https://www.youtube.com/youtubei/v1/next",request,token).ConfigureAwait(false))
                    {
                        response.EnsureSuccessStatusCode();await response.Content.LoadIntoBufferAsync(4*1024*1024).ConfigureAwait(false);
                        var json=await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                        token.ThrowIfCancellationRequested();
                        var root=new JavaScriptSerializer{MaxJsonLength=4*1024*1024,RecursionLimit=150}.DeserializeObject(json);
                        // Restrict to continuation updates, not unrelated video recommendations.
                        var updates=Get(root,"onResponseReceivedEndpoints") ?? Get(root,"onResponseReceivedActions");
                        return HeaderCount(updates) ?? "미확인";
                    }
                }
            }
            catch(OperationCanceledException){token.ThrowIfCancellationRequested();return "미확인";}
            catch(HttpRequestException){return "미확인";}
            catch(ArgumentException){return "미확인";}
        }
    }
}
