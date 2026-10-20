using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;

namespace ReplierDesktop
{
    public sealed class BatchResult
    {
        public readonly List<Video> Videos = new List<Video>();
        public int Candidates;
        public int Checked;
        public int NoCaptions;
        public int CategoryExcluded;
        public int CategoryUnknown;
        public int LanguageExcluded;
        public bool Cancelled;
        public string Error = "";
    }
    public static class TopicPicker
    {
        public static Topic Pick(IList<Topic> topics)
        {
            if (topics == null || topics.Count == 0) throw new InvalidDataException("새 추천 검색어가 없습니다. 다시 눌러 다른 분야를 찾아보세요.");
            uint count = (uint)topics.Count;
            uint ceiling = uint.MaxValue - (uint.MaxValue % count);
            var bytes = new byte[4];
            uint value;
            using (var random = RandomNumberGenerator.Create())
            {
                do { random.GetBytes(bytes); value = BitConverter.ToUInt32(bytes, 0); } while (value >= ceiling);
            }
            return topics[(int)(value % count)];
        }
    }
    public static class VideoBatch
    {
        sealed class Prepared
        {
            public Video Video;
            public VideoContent Content;
            public bool CategoryExcluded, CategoryUnknown, LanguageExcluded;
        }
        static async Task<Prepared> Prepare(Video video, ContentStore store, CancellationToken token,
            Func<Video, CancellationToken, Task<VideoContent>> fetch,string category,
            Func<Video,CancellationToken,Task<string>> readCategory,bool koreanOnly,bool includeCommentCounts,
            Func<Video,CancellationToken,Task<string>> readCount)
        {
            if(koreanOnly && !KoreanVideos.TitleMatches(video.Title)) return new Prepared {LanguageExcluded=true};
            if(category!="all" || includeCommentCounts)
            {
                string actual=null;
                try { actual=await readCategory(video,token).ConfigureAwait(false); }
                catch(HttpRequestException) {if(category!="all")return new Prepared {CategoryUnknown=true};}
                catch(OperationCanceledException) { if(token.IsCancellationRequested) throw; if(category!="all")return new Prepared {CategoryUnknown=true}; }
                if(category!="all" && (actual==null || VideoCategories.Index(actual)<0 || actual=="all")) return new Prepared {CategoryUnknown=true};
                if(category!="all" && actual!=category) return new Prepared {CategoryExcluded=true};
            }
            VideoContent content;
            lock(store){content=store.Load(video.Id);}
            if (content == null)
            {
                try { content = await fetch(video, token).ConfigureAwait(false); }
                catch (ContentUnavailable) { return new Prepared(); }
                catch (HttpRequestException) { return new Prepared(); }
                catch (OperationCanceledException) { if (token.IsCancellationRequested) throw; return new Prepared(); }
                ContentStore.Validate(content, video.Id);
                if(koreanOnly && !KoreanVideos.ContentMatches(content)) return new Prepared {LanguageExcluded=true};
                lock(store){store.Save(content);}
            }
            if(koreanOnly && !KoreanVideos.ContentMatches(content)) return new Prepared {LanguageExcluded=true};
            if(includeCommentCounts) video.CommentCountText=await readCount(video,token).ConfigureAwait(false) ?? "미확인";
            return new Prepared { Video = video, Content = content };
        }

        public static async Task<BatchResult> Collect(string query, VideoLedger unusedHistory, ContentStore store,
            CancellationToken token, IProgress<string> progress = null,
            Func<string, CancellationToken, Task<List<Video>>> search = null,
            Func<Video, CancellationToken, Task<VideoContent>> captions = null,string period="all",string category="all",
            Func<Video,CancellationToken,Task<string>> categories=null,bool koreanOnly=false,bool includeCommentCounts=false,
            Func<Video,CancellationToken,Task<string>> commentCounts=null)
        {
            if(VideoCategories.Index(category)<0) throw new ArgumentException("카테고리 설정을 확인해 주세요.");
            var result = new BatchResult();
            Func<string,CancellationToken,Task<List<Video>>> searcher = search ?? ((q,t)=>VideoSearch.Search(q,t,period));
            var fetch = captions ?? CaptionService.Fetch;
            try
            {
                // Selection history is no longer read or written in any acquisition mode.
                var raw = await searcher(query, token).ConfigureAwait(false);

                var candidates = raw.Where(v => VideoSearch.ValidId(v.Id))
                    .OrderByDescending(v=>ViewCounts.Parse(v.ViewCountText)).Take(30).ToList();
                result.Candidates = candidates.Count;

                // At most three caption lookups concurrently; only start another wave when needed.
                for (int i = 0; i < candidates.Count && result.Videos.Count < 10; i += 3)
                {
                    token.ThrowIfCancellationRequested();
                    if (progress != null) progress.Report("영상 확인 " + result.Checked +
                        "/" + candidates.Count + " · 확보 " + result.Videos.Count + "/10");
                    var wave = await Task.WhenAll(candidates.Skip(i).Take(3)
                        .Select(v => Prepare(v, store, token, fetch,category,categories ?? CategoryService.Fetch,koreanOnly,includeCommentCounts,commentCounts ?? CommentCounts.Fetch))).ConfigureAwait(false);
                    foreach (var prepared in wave)
                    {
                        token.ThrowIfCancellationRequested();
                        result.Checked++;
                        if(prepared.LanguageExcluded) {result.LanguageExcluded++;continue;}
                        if(prepared.CategoryExcluded) {result.CategoryExcluded++;continue;}
                        if(prepared.CategoryUnknown) {result.CategoryUnknown++;continue;}
                        if (prepared.Video == null) { result.NoCaptions++; continue; }
                        if (result.Videos.Count == 10) break;
                        result.Videos.Add(prepared.Video);
                    }
                }
            }
            catch (OperationCanceledException) { result.Cancelled = true; }
            catch (InvalidDataException) { result.Error = "자막 데이터를 확인할 수 없어 수집을 중단했습니다."; }
            catch (IOException) { result.Error = "자막을 저장하지 못해 수집을 중단했습니다. 다른 앱에서 사용 중인지 확인해 주세요."; }
            return result;
        }
    }
}
