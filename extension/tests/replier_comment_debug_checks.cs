using System;using System.Linq;using System.IO;using System.Reflection;using System.Windows.Forms;using ReplierDesktop;
public static class CommentDebugChecks {
 static void Check(bool ok,string name){if(!ok)throw new Exception(name);Console.WriteLine("PASS "+name);}
 static void Field(object o,string name,object value){o.GetType().GetField(name,BindingFlags.NonPublic|BindingFlags.Instance).SetValue(o,value);}
 [STAThread] public static int Main(string[] args){try{
 string copied=null;using(var form=new MainForm(Path.Combine(args[0],"history.json"),clipboardWriter:text=>copied=text)){
 var button=(Button)form.Controls.Find("CopyCommentDebug",true)[0];Check(!button.Enabled,"copy disabled without selected video");
 var video=new Video{Id="V0000000001",Title="디버깅 검사용 영상",Channel="검사용 채널"};Field(form,"currentVideo",video);
 var result=new DualCommentResult{Complete=true};for(int model=0;model<2;model++)result.Batches.Add(new ModelCommentBatch{Model=DualCommentService.Models[model],Label=DualCommentService.Labels[model],Result=new CommentResult{Comments=Enumerable.Range(0,5).Select(i=>new CommentSuggestion{Text="후보 "+model+"-"+i,GroundingQuote="실제 선택 구절",Evidence="선택 구절의 앞뒤 문맥",FitScore=model*20+i,FitEligible=i!=0,GemmaFitScore=10,QwenFitScore=20,FitReason="Gemma 판단: 근거 연결\nQwen 판단: 말투 확인"}).ToList()}});
 Field(form,"debugResult",result);typeof(MainForm).GetMethod("RenderComments",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(form,new object[]{result});button.Enabled=true;
 typeof(MainForm).GetMethod("CopyCommentDebug",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(form,null);
 Check(copied.Contains(video.Title)&&copied.Contains(video.Url)&&copied.Contains(video.Channel),"copy contains selected video title link and channel");
 Check(result.Batches.SelectMany(b=>b.Result.Comments).All(c=>copied.Contains(c.Text)),"copy includes all ten generated candidates including rejected ones");
 Check(copied.Contains("최종 추천 댓글]\r\n후보 1-4")&&copied.Contains("Gemma 판단")&&copied.Contains("Qwen 판단")&&copied.Contains("앞뒤 문맥"),"copy contains actual displayed winner both model judgments and source context");
 Check(!copied.Contains("이전 결과 유지"),"current winner is identified as part of latest batch");
 Field(form,"debugResult",null);Field(form,"debugError","확보한 자막이 없어 댓글을 생성하지 않았습니다.");typeof(MainForm).GetMethod("CopyCommentDebug",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(form,null);
 Check(copied.Contains("이전 결과 유지")&&copied.Contains("생성 오류")&&copied.Contains("생성 결과 없음"),"failed refresh distinguishes retained winner from failed latest attempt");
 typeof(MainForm).GetMethod("ClearVideo",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(form,null);Check(!button.Enabled,"switching video clears stale debug report and disables copy");
 var empty=CommentDebugReport.Format(video,new DualCommentResult{Complete=true},null,"전체 탈락","");Check(empty.Contains("최종 추천 댓글]\r\n없음"),"no winner is not misrepresented in diagnostic text");
 }return 0;}catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
