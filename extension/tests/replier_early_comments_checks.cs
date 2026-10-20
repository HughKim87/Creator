using System;using System.Collections.Generic;using System.IO;using System.Linq;using System.Reflection;using System.Threading;using System.Threading.Tasks;using System.Windows.Forms;using ReplierDesktop;
public static class EarlyCommentsChecks{
 static void Check(bool ok,string label){if(!ok)throw new Exception(label);Console.WriteLine("PASS "+label);}
 static void Set(MainForm f,string n,object v){typeof(MainForm).GetField(n,BindingFlags.Instance|BindingFlags.NonPublic).SetValue(f,v);}
 [STAThread]public static int Main(string[] args){try{
 Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);string run=Path.Combine(Path.GetFullPath(args[0]),Guid.NewGuid().ToString("N"));Directory.CreateDirectory(run);
 var v=new Video{Id="V0000000001",Title="합성 검사"};new ContentStore(Path.Combine(run,"content")).Save(new VideoContent{Version=1,VideoId=v.Id,Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=new List<CaptionCue>{new CaptionCue{Text="실제 영상이 아닌 검사 자막"}}});
 Exception error=null;using(var f=new MainForm(Path.Combine(run,"history.json"))){f.Opacity=0;f.ShowInTaskbar=false;
 ((DualCommentService)typeof(MainForm).GetField("comments",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(f)).Dispose();
 var gate=new TaskCompletionSource<int>();int sequence=0;var refreshArguments=new List<bool>();bool failWriter=false,failScore=false,failQuality=false;
 Set(f,"comments",new DualCommentService((name,video,content,t,refresh)=>{
 refreshArguments.Add(refresh);if(failWriter && name.StartsWith("qwen"))throw new InvalidOperationException("합성 생성 실패");sequence++;
 return Task.FromResult(new CommentResult{Comments=Enumerable.Range(0,5).Select(i=>new CommentSuggestion{Text=sequence+" 번째 검사 댓글 "+i,Evidence="합성 자막",CueId="c0"}).ToList()});},evaluator:async(video,content,rows,t)=>{
 if(failScore)throw new InvalidOperationException("합성 평가 실패");
 var current=gate;using(t.Register(()=>current.TrySetCanceled())){await current.Task;}
 for(int i=0;i<rows.Count;i++){rows[i].FitScore=i+70;rows[i].FitEligible=failQuality ? (bool?)false : null;}
 }));
 f.Shown+=async(sender,e)=>{try{
 var videos=(DataGridView)f.Controls.Find("Videos",true)[0];var comments=(DataGridView)f.Controls.Find("Comments",true)[0];var refresh=(Button)f.Controls.Find("RefreshComments",true)[0];
 Set(f,"busy",true);int row=videos.Rows.Add(v.Title,"검사 채널","1:00","1회","1일 전");videos.Rows[row].Tag=v;videos.ClearSelection();Set(f,"busy",false);videos.Rows[row].Selected=true;
 await Task.Delay(100);Check(comments.Rows.Count==0 && !f.SelectionTask.IsCompleted,"no winner before both models finish grading");
 Check(!refresh.Enabled,"refresh waits for initial grading");
 gate.SetResult(0);await f.SelectionTask;
 Check(comments.Rows.Count==1 && comments.Rows[0].Cells["fit"].Value.ToString()=="79점" && comments.Rows[0].Cells["model"].Value.ToString()=="Qwen","best of all ten shown after grading");
 Check(refresh.Text=="댓글 다시 생성" && refresh.Enabled,"one visible row is treated as complete result");
 var old=comments.Rows[0].Cells["text"].Value.ToString();gate=new TaskCompletionSource<int>();refresh.PerformClick();await Task.Delay(100);
 Check(!f.SelectionTask.IsCompleted && comments.Rows.Count==1 && comments.Rows[0].Cells["text"].Value.ToString()==old,"previous winner retained during regeneration and grading");
 Check(((Label)f.Controls.Find("CommentStatus",true)[0]).Text.Contains("적합도 평가 중"),"pending grading is identified");
 gate.SetResult(0);await f.SelectionTask;
 Check(comments.Rows.Count==1 && comments.Rows[0].Cells["text"].Value.ToString()!=old,"new scored winner replaces previous winner");
 old=comments.Rows[0].Cells["text"].Value.ToString();gate=new TaskCompletionSource<int>();refresh.PerformClick();await Task.Delay(100);((Button)f.Controls.Find("Stop",true)[0]).PerformClick();await f.SelectionTask;
 Check(comments.Rows.Count==1 && comments.Rows[0].Cells["text"].Value.ToString()==old,"cancelled grading keeps prior winner");
 failWriter=true;gate=new TaskCompletionSource<int>();refresh.PerformClick();await Task.Delay(100);gate.SetResult(0);await f.SelectionTask;
 Check(comments.Rows.Count==1 && comments.Rows[0].Cells["text"].Value.ToString()==old && refresh.Text=="추천 댓글 재시도","partial generation cannot replace complete winner");
 failWriter=false;failScore=true;refresh.PerformClick();await f.SelectionTask;
 Check(comments.Rows.Count==1 && comments.Rows[0].Cells["text"].Value.ToString()==old && refresh.Text=="적합도 다시 평가","failed grading preserves prior winner and offers retry");
 failScore=false;gate=new TaskCompletionSource<int>();gate.SetResult(0);refresh.PerformClick();await f.SelectionTask;
 Check(comments.Rows.Count==1 && comments.Rows[0].Cells["text"].Value.ToString()!=old && refresh.Text=="댓글 다시 생성","retry returns to complete single-winner display");
 failScore=true;typeof(MainForm).GetMethod("ClearVideo",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(f,new object[0]);
 await f.ShowSelectedVideo();
 Check(comments.Rows.Count==1 && comments.Rows[0].Cells["fit"].Value.ToString()=="미평가" && comments.Rows[0].Cells["fit"].ToolTipText.Contains("점수와 순위가 없는"),"first grading failure shows an explicitly unranked generated comment instead of a blank list");
 Check(refresh.Enabled && refresh.Text=="적합도 다시 평가","grading failure exposes evaluation retry");
 failScore=false;gate=new TaskCompletionSource<int>();gate.SetResult(0);refresh.PerformClick();await f.SelectionTask;
 Check(refreshArguments.Skip(refreshArguments.Count-2).All(r=>!r) && comments.Rows[0].Cells["fit"].Value.ToString()=="79점","evaluation retry reuses generation path without requesting regeneration and restores ranked winner");
 failQuality=true;typeof(MainForm).GetMethod("ClearVideo",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(f,new object[0]);await f.ShowSelectedVideo();
 Check(comments.Rows.Count==0 && refresh.Enabled,"all quality vetoes hide every generated candidate while allowing retry");
 failQuality=false;refresh.PerformClick();await f.SelectionTask;
 Check(refreshArguments.Skip(refreshArguments.Count-2).All(r=>r) && comments.Rows.Count==1,"quality rejection retries request fresh candidates instead of rescoring cached rejected comments");
 }catch(Exception ex){error=ex;}finally{f.Close();}};Application.Run(f);}
 if(error!=null)throw error;return 0;}catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}}
