using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Threading;
using ReplierDesktop;

public static class CommentChecks
{
    static void Check(bool ok,string name) { if(!ok) throw new Exception(name); Console.WriteLine("PASS "+name); }
    public static int Main(string[] args)
    {
        try
        {
            ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;
            var video=new Video {Id="HPUpsEzL1ps",Title="스팀평가 매우긍정적 이상! 꿀잼 인디게임 추천 14종",Channel="겜생각"};
            var content=CaptionService.Fetch(video,CancellationToken.None).GetAwaiter().GetResult();
            var evidence=CommentService.Evidence(content);
            Check(evidence.Count>0 && evidence.Count<=40,"bounded evidence comes from actual subtitle cues");
            Check(evidence.Values.All(c=>content.Cues.Any(original=>original.StartMs==c.StartMs && string.Join(" ",content.Cues.Skip(content.Cues.IndexOf(original)).Take(5).Select(x=>x.Text)).StartsWith(c.Text))),"every supplied evidence fragment maps to actual speech");
            bool rejected=false;
            try { CommentService.Parse("{\"comments\":[]}",evidence,content.Cues.Count); } catch(InvalidDataException){rejected=true;}
            Check(rejected,"fewer than five suggestions rejected");
            rejected=false;
            try { CommentService.Parse("{\"comments\":[{\"text\":\"자막에 없는 근거를 쓰는 댓글입니다\",\"cue_id\":\"missing\"},{},{},{},{}]}",evidence,content.Cues.Count); } catch(InvalidDataException){rejected=true;}
            Check(rejected,"unknown subtitle references rejected");
            var evidenceId=evidence.Keys.First();
            string badLanguage=new System.Web.Script.Serialization.JavaScriptSerializer().Serialize(new {
                comments=Enumerable.Range(0,5).Select(i=>new {text="게임 시스템设计가 재미있네요 "+i,cue_id=evidenceId}).ToArray() });
            rejected=false;
            try { CommentService.Parse(badLanguage,evidence,content.Cues.Count); } catch(InvalidDataException){rejected=true;}
            Check(rejected,"mixed Chinese output rejected before display");
            var plain=new[]{"살짝 구경하려다 고를 것만 늘어나네요","구경하다가 시간 가는 줄 모르겠네요","어떤 게임부터 볼지 고민되네요","보기만 해도 해보고 싶어지네요","이런 게임 구경하는 재미가 있네요"};
            Func<string[],string> response=items=>new System.Web.Script.Serialization.JavaScriptSerializer().Serialize(new {
                comments=items.Select(t=>new {text=t,cue_id=evidenceId}).ToArray() });
            Check(CommentService.Parse(response(plain),evidence,content.Cues.Count).Comments.Count==5,"ordinary reactions are allowed without forcing a joke");
            foreach(string bad in new[]{"제 손이 느려서 게임을 못 따라가네요ㅋㅋ","나이가 들수록 체력이 떨어지네요ㅋㅋ","제 허리는 벌써 레벨다운이네요ㅋㅋ"})
            {
                var rows=(string[])plain.Clone();rows[0]=bad;rejected=false;
                try{CommentService.Parse(response(rows),evidence,content.Cues.Count);}catch(InvalidDataException){rejected=true;}
                Check(rejected,"unwanted physical self-deprecation is rejected: "+bad);
            }
            Check(CommentService.ParsePlain(string.Join("\n\n",plain.Select((t,i)=>(i+1)+". "+t)),evidence,evidenceId,content.Cues.Count).Comments.Count==5,"plain model output accepts five numbered lines without losing validation");
            Check(evidence.Count==5 && evidence.Values.Select(c=>c.StartMs).Distinct().Count()==5,"long video supplies five separate real subtitle windows");
            int writers=0,classifications=0;
            var sent=new List<string>();
            using(var traceModel=new LocalModel("unused-test-runtime"))
            {
                var traced=new CommentService(traceModel,(body,token)=>{
                    var root=new System.Web.Script.Serialization.JavaScriptSerializer().DeserializeObject(new System.Web.Script.Serialization.JavaScriptSerializer().Serialize(body));
                    var messages=(object[])CaptionService.Get(root,"messages");
                    string prompt=(string)CaptionService.Get(messages[messages.Length-1],"content");
                    if(!prompt.Contains("참고 자막:"))
                    {classifications++;return System.Threading.Tasks.Task.FromResult("{\"kind\":\"게임 추천\",\"mood\":\"가벼움\"}");}
                    var anchor=evidence.ElementAt(writers%evidence.Count);
                    Check(prompt.Contains(anchor.Value.Text) && !evidence.Where(e=>e.Key!=anchor.Key).Any(e=>prompt.Contains(e.Value.Text)),"writer request receives only its own subtitle window "+(writers+1));
                    sent.Add(anchor.Key);writers++;
                    return System.Threading.Tasks.Task.FromResult("구간 "+new string('가',writers)+"는 가볍게 구경하는 재미가 있네요");
                },usePlanning:false);
                var tracedResult=traced.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult();
                Check(tracedResult.Comments.Select(c=>c.CueId).SequenceEqual(sent),"each displayed reference is exactly the window sent for that comment");
                Check(tracedResult.Comments.Select(c=>c.CueId).Distinct().Count()==5,"five comments do not share one classification reference");
                traced.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult();
                Check(writers==5 && classifications==0,"writer skips speculative classification and reselection uses complete cached drafts");
            }
            var cts=new CancellationTokenSource();cts.Cancel();
            string extension=Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"..",".."));
            using(var model=new LocalModel(Path.Combine(extension,".runtime","replier-llm"),LocalModel.ConfiguredName(extension)))
            {
                var service=new CommentService(model);
                bool cancelled=false;
                try { service.Generate(video,content,cts.Token).GetAwaiter().GetResult(); } catch(OperationCanceledException){cancelled=true;}
                Check(cancelled,"cancelled selection does not start model generation");
                if(args.Contains("--validation-only")) return 0;
                var result=service.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult();
                Check(result.Comments.Count==5 && result.Comments.Select(c=>c.Text).Distinct().Count()==5,"actual local model produces five distinct Korean comments");
                Check(result.Comments.All(c=>evidence.ContainsKey(c.CueId) && c.Evidence==evidence[c.CueId].Text),"generated comments carry verified subtitle evidence");
                var again=service.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult();
                Check(Object.ReferenceEquals(result,again),"repeat selection reuses validated results within this session");
                foreach(var item in result.Comments) Console.WriteLine("COMMENT "+item.Text+" | "+CaptionService.Timestamp(item.StartMs)+" | "+item.Evidence);
            }
            return 0;
        }
        catch(Exception ex){Console.Error.WriteLine(ex.GetType().Name+": "+ex.Message);return 1;}
    }
}
