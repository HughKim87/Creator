using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace ReplierDesktop
{
    public sealed class ModelCommentBatch
    {
        public string Model, Label, Error;
        public CommentResult Result;
    }
    public sealed class DualCommentResult
    {
        public List<ModelCommentBatch> Batches = new List<ModelCommentBatch>();
        public string ActiveModel = "";
        public string ScoreError = "";
        public bool Cancelled, Complete;
        public int Count { get { return Batches.Where(b=>b.Result!=null).Sum(b=>b.Result.Comments.Count); } }
    }
    public sealed class DualCommentService : IDisposable
    {
        public static readonly string[] Models={"gemma4:e2b-it-qat","qwen3.5:4b"};
        public static readonly string[] Labels={"Gemma","Qwen"};
        readonly SemaphoreSlim gate=new SemaphoreSlim(1,1);
        readonly List<LocalModel> owned=new List<LocalModel>();
        readonly Func<string,Video,VideoContent,CancellationToken,bool,Task<CommentResult>> generate;
        readonly Func<string,Task> release;
        readonly Func<CancellationToken,Task> prepare;
        readonly Func<Video,VideoContent,IList<CommentSuggestion>,CancellationToken,Task> evaluate;
        readonly Func<Video,VideoContent,CancellationToken,Task> plan;
        readonly bool retryQuality;
        readonly TimeSpan writerTimeout;
        readonly bool qwenWritesFirst;
        public DualCommentService(string root,bool retryRejected=false)
        {
            retryQuality=retryRejected;writerTimeout=TimeSpan.FromSeconds(75);qwenWritesFirst=true;
            var runtimes=Models.ToDictionary(name=>name,name=>new LocalModel(root,name,true));
            owned.AddRange(Models.Select(name=>runtimes[name]));
            var services=Models.ToDictionary(name=>name,name=>new CommentService(runtimes[name]));
            Dictionary<string,string> material=null;string plannedKey=null;
            var planner=new ScenePlanner(runtimes[Models[1]]);
            plan=async (video,content,token)=>{
                string key=video.Id+"\n"+video.Title+"\n"+new System.Web.Script.Serialization.JavaScriptSerializer{MaxJsonLength=8*1024*1024}.Serialize(content);
                if(key!=plannedKey){await runtimes[Models[0]].Unload().ConfigureAwait(false);var sample=await AudienceComments.Fetch(video,token).ConfigureAwait(false);var next=await planner.Prepare(video,content,token).ConfigureAwait(false);next=await ClearReactionPoints.Select(runtimes[Models[1]],next,CommentService.Evidence(content,video.Title),token,video.Title).ConfigureAwait(false);AudienceAngle[] angles=new AudienceAngle[0];
                 if(sample.Comments.Length>0)try{angles=await AudienceComments.Plan(runtimes[Models[1]],video,CommentService.Evidence(content,video.Title),sample,token).ConfigureAwait(false);}catch(InvalidDataException){sample.Status+=" · 반응 소재 추출 실패, 제목·자막으로 작성";}catch(ArgumentException){sample.Status+=" · 반응 소재 형식 오류, 제목·자막으로 작성";}
                 material=AudienceComments.Attach(next,CommentService.Evidence(content,video.Title),sample,angles);plannedKey=key;}
            };
            generate=(name,video,content,token,refresh)=>services[name].Generate(video,content,token,refresh,material);
            release=name=>runtimes[name].Unload();
            prepare=async token=>{
                var loaded=await LocalModel.LoadedOnGpuAfterStart(runtimes[Models[0]],token).ConfigureAwait(false);
                if(Models.All(loaded.Contains))return;
                foreach(var name in Models)await runtimes[name].Warm(token).ConfigureAwait(false);
                loaded=await LocalModel.LoadedOnGpu(token).ConfigureAwait(false);
                if(!Models.All(loaded.Contains))throw new InvalidOperationException("두 모델 동시 준비 미완료 · GPU 메모리 여유를 확인해 주세요. 생성은 가능하지만 모델 전환이 느릴 수 있습니다.");
            };
            var scoring=new CombinedFitScoring(new FitScoring(runtimes[Models[0]]),new FitScoring(runtimes[Models[1]]),runtimes[Models[0]].Unload,false);
            var tieBreaker=new SceneTieBreaker((name,body,token)=>runtimes[name].Chat(body,token),name=>runtimes[name].Unload(),true);
            evaluate=async (video,content,rows,token)=>{
                bool scene=rows.All(c=>SceneMaterial.IsScene(c.Material));
                if(scene){
                    await runtimes[Models[1]].Unload().ConfigureAwait(false);
                    await new ScenePolisher(runtimes[Models[0]]).Apply(rows,token).ConfigureAwait(false);
                }
                await scoring.Evaluate(video,content,rows,token).ConfigureAwait(false);
                if(!rows.Any(c=>c.FitEligible==true)&&rows.Any(c=>!string.IsNullOrEmpty(c.FitError)))throw new InvalidDataException("일부 후보 평가 응답 오류 · 후보별 디버깅 사유를 확인해 주세요.");
                if(scene){
                    await tieBreaker.Apply(video,rows,token).ConfigureAwait(false);
                }
            };
        }
        public DualCommentService(Func<string,Video,VideoContent,CancellationToken,bool,Task<CommentResult>> writer,Func<string,Task> unloader=null,
            Func<Video,VideoContent,IList<CommentSuggestion>,CancellationToken,Task> evaluator=null,Func<CancellationToken,Task> preparer=null,bool retryRejected=false,TimeSpan? generationTimeout=null)
        { retryQuality=retryRejected;writerTimeout=generationTimeout??TimeSpan.FromSeconds(60);generate=writer; release=unloader ?? (name=>Task.FromResult(0));evaluate=evaluator;prepare=preparer ?? (token=>Task.FromResult(0)); }
        public async Task PrepareFirst(CancellationToken token)
        {
            await gate.WaitAsync(token).ConfigureAwait(false);
            try{await prepare(token).ConfigureAwait(false);}finally{gate.Release();}
        }
        static void Report(DualCommentResult result,IProgress<DualCommentResult> progress)
        {
            if(progress!=null) progress.Report(new DualCommentResult { Batches=result.Batches.ToList(),ActiveModel=result.ActiveModel,
                Cancelled=result.Cancelled,Complete=result.Complete,ScoreError=result.ScoreError });
        }
        public async Task<DualCommentResult> Generate(Video video,VideoContent content,CancellationToken token,bool refresh=false,IProgress<DualCommentResult> progress=null)
        {
            await gate.WaitAsync(token).ConfigureAwait(false);
            var result=new DualCommentResult();
            try
            {
                if(plan!=null){result.ActiveModel="내용 확인";Report(result,progress);await plan(video,content,token).ConfigureAwait(false);}
                for(int pass=0;pass<(retryQuality?2:1);pass++){
                for(int i=0;i<Models.Length;i++)
                {
                    token.ThrowIfCancellationRequested();
                    string name=qwenWritesFirst?Models[Models.Length-1-i]:Models[i];
                    result.ActiveModel=Labels[Array.IndexOf(Models,name)];Report(result,progress);
                    var batch=new ModelCommentBatch {Model=name,Label=Labels[Array.IndexOf(Models,name)],Error=""};
                    bool cancelled=false;
                    try
                    {
                        using(var writerLimit=CancellationTokenSource.CreateLinkedTokenSource(token)){writerLimit.CancelAfter(writerTimeout);try{batch.Result=await generate(name,video,content,writerLimit.Token,refresh).ConfigureAwait(false);}catch(OperationCanceledException){token.ThrowIfCancellationRequested();throw new InvalidOperationException(name+" 생성 제한 시간을 초과해 중단했습니다.");}}
                        token.ThrowIfCancellationRequested();
                        if(batch.Result==null || batch.Result.Comments.Count>5 || (batch.Result.Comments.Count<5 && !batch.Result.QualityFiltered)) throw new InvalidDataException("댓글 5개를 완성하지 못했습니다.");
                    }
                    catch(OperationCanceledException)
                    {
                        cancelled=token.IsCancellationRequested;batch.Error="응답 시간 초과";batch.Result=null;
                    }
                    catch(Exception ex)
                    {
                        batch.Result=null;
                        batch.Error=ex is InvalidDataException || ex is InvalidOperationException ? ex.Message : "댓글 생성 실패";
                    }
                    // The evaluator owns the transition from the last writer to surface editing and grading.
                    bool reuseForScoring=evaluate!=null && i==Models.Length-1 && batch.Result!=null;
                    if(!reuseForScoring)try { await release(name).ConfigureAwait(false); } catch { }
                    if(cancelled) token.ThrowIfCancellationRequested();
                    result.Batches.Add(batch);Report(result,progress);
                }
                if(evaluate!=null && result.Count>0)
                {
                    result.ActiveModel="적합도";Report(result,progress);
                    bool cancelled=false;
                    try
                    {
                        await evaluate(video,content,result.Batches.Where(b=>b.Result!=null).SelectMany(b=>b.Result.Comments).ToList(),token).ConfigureAwait(false);
                    }
                    catch(OperationCanceledException) {cancelled=token.IsCancellationRequested;result.ScoreError="적합도 평가 시간 초과";}
                    catch(Exception ex) {result.ScoreError="적합도 평가 실패"+(ex is InvalidDataException ? " · "+ex.Message : "");}
                    foreach(var gradingModel in Models)
                        try {await release(gradingModel).ConfigureAwait(false);}catch { }
                    if(cancelled) token.ThrowIfCancellationRequested();
                }
                bool allRejected=string.IsNullOrEmpty(result.ScoreError) && result.Batches.Count==2 && result.Batches.All(b=>b.Result!=null && string.IsNullOrEmpty(b.Error)) && result.Batches.SelectMany(b=>b.Result.Comments).All(c=>c.FitEligible==false);
                if(!allRejected || pass==1 || !retryQuality)break;
                // One bounded rewrite with the rejected cached drafts in avoid; never relax quality gates.
                token.ThrowIfCancellationRequested();refresh=true;result.Batches.Clear();result.ActiveModel="다시 작성";Report(result,progress);
                }
                result.ActiveModel="";result.Complete=true;
            }
            catch(OperationCanceledException) { result.ActiveModel="";result.Cancelled=true; }
            finally { gate.Release(); }
            Report(result,progress);return result;
        }
        public void Dispose() { foreach(var runtime in owned.AsEnumerable().Reverse()) runtime.Dispose(); }
    }
}

