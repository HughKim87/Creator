using System;using System.Collections.Generic;using System.IO;using System.Linq;using System.Reflection;using System.Threading;using System.Threading.Tasks;using System.Web.Script.Serialization;using System.Windows.Forms;using ReplierDesktop;
public static class MissingRetryChecks
{
 static void Check(bool ok,string text){if(!ok)throw new Exception(text);Console.WriteLine("PASS "+text);}
 static void Set(MainForm form,string field,object value){typeof(MainForm).GetField(field,BindingFlags.Instance|BindingFlags.NonPublic).SetValue(form,value);}
 [STAThread] public static int Main(string[] args){try{
 Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
 string run=Path.Combine(Path.GetFullPath(args[0]),"run-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(run);
 var video=new Video{Id="HPUpsEzL1ps",Title="검사용 게임 영상"};var content=new VideoContent{Version=1,VideoId=video.Id,Language="ko",Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=Enumerable.Range(0,10).Select(i=>new CaptionCue{StartMs=i*1000,Text="검사용 분위기 대사"}).ToList()};
 new ContentStore(Path.Combine(run,"content")).Save(content);int gCalls=0,qCalls=0;bool failQ=true;Exception error=null;
 using(var gModel=new LocalModel("unused","gemma4:e2b-it-qat"))using(var qModel=new LocalModel("unused","qwen3.5:4b")){
 Func<object,bool> classification=body=>CaptionService.Get(new JavaScriptSerializer().DeserializeObject(new JavaScriptSerializer().Serialize(body)),"format")!=null;
 var gService=new CommentService(gModel,(body,t)=>{if(classification(body))return Task.FromResult("{\"kind\":\"게임 플레이\",\"mood\":\"가벼움\"}");gCalls++;return Task.FromResult("차분하게 구경하기 좋은 분위기네요 "+new string('가',gCalls));},usePlanning:false);
 var qService=new CommentService(qModel,(body,t)=>{if(classification(body))return Task.FromResult("{\"kind\":\"게임 플레이\",\"mood\":\"가벼움\"}");qCalls++;return Task.FromResult(failQ?"제 손이 느려서 따라가기 힘드네요ㅋㅋ":"가볍게 보다가 시간이 가는 줄 몰랐네요 "+new string('가',qCalls));},usePlanning:false);
 using(var form=new MainForm(Path.Combine(run,"history.json"))){
 ((DualCommentService)typeof(MainForm).GetField("comments",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(form)).Dispose();
 Set(form,"comments",new DualCommentService((name,v,c,t,r)=>name.StartsWith("gemma")?gService.Generate(v,c,t,r):qService.Generate(v,c,t,r),evaluator:(v,c,rows,t)=>{for(int i=0;i<rows.Count;i++)rows[i].FitScore=70+i;return Task.FromResult(0);}));
 form.Opacity=0;form.ShowInTaskbar=false;
 form.Shown+=async(sender,e)=>{try{
 var grid=(DataGridView)form.Controls.Find("Videos",true)[0];var comments=(DataGridView)form.Controls.Find("Comments",true)[0];var retry=(Button)form.Controls.Find("RefreshComments",true)[0];
 Set(form,"busy",true);Set(form,"videos",new List<Video>{video});int row=grid.Rows.Add(video.Title,"채널","10:00","100회","1일 전");grid.Rows[row].Tag=video;grid.ClearSelection();Set(form,"busy",false);grid.Rows[row].Selected=true;await form.SelectionTask;
 Check(comments.Rows.Count==0 && retry.Text=="추천 댓글 재시도","partial generation offers retry without publishing a false winner");
 int prior=gCalls;var old=comments.Rows.Cast<DataGridViewRow>().Select(r=>r.Cells["text"].Value.ToString()).ToArray();failQ=false;retry.PerformClick();await form.SelectionTask;
 Check(comments.Rows.Count==1,"retry selects one winner after completing ten candidates");
 Check(gCalls==prior,"successful model drafts are cached during recovery");
 Check(retry.Text=="댓글 다시 생성" && retry.Enabled,"complete results restore normal regenerate-all action");
 }catch(Exception ex){error=ex;}finally{form.Close();}};Application.Run(form);}
 }
 if(error!=null)throw error;return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}}
}
