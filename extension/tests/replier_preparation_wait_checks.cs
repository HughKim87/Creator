using System;using System.IO;using System.Reflection;using System.Threading;using System.Threading.Tasks;using System.Windows.Forms;using ReplierDesktop;
public static class PreparationWaitChecks{
 sealed class Publisher:IYoutubePublisher{public YoutubeAccount Account{get{return null;}}public Task Restore(CancellationToken t){throw new MissingYoutubeConnectionException();}public Task Connect(string f,CancellationToken t){throw new Exception();}public void Disconnect(){}public Task<PostedComment> Publish(string i,string c,string a,CancellationToken t){throw new Exception();}}
 static void Check(bool b,string m){if(!b)throw new Exception(m);Console.WriteLine("PASS "+m);}
 [STAThread]public static int Main(string[] args){try{Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Exception error=null;int calls=0;
 using(var f=new MainForm(Path.Combine(args[0],"history.json"),new Publisher())){
 f.Opacity=0;f.ShowInTaskbar=false;var field=typeof(MainForm).GetField("comments",BindingFlags.Instance|BindingFlags.NonPublic);((DualCommentService)field.GetValue(f)).Dispose();field.SetValue(f,new DualCommentService((m,v,c,t,r)=>{calls++;throw new Exception("must not start while preparing");},preparer:async t=>{await Task.Delay(Timeout.Infinite,t);}));
 f.Shown+=async(s,e)=>{try{
 var token=new CancellationTokenSource();var method=typeof(MainForm).GetMethod("LoadComments",BindingFlags.Instance|BindingFlags.NonPublic);var work=(Task)method.Invoke(f,new object[]{new Video{Id="V0000000001"},0,token.Token,false,false});
 await Task.Delay(80);Check(!work.IsCompleted&&calls==0,"selection waits for preparation before starting generation");Check(f.Controls.Find("CommentStatus",true)[0].Text.Contains("준비"),"waiting phase is visibly identified as preparation");token.Cancel();await work;Check(calls==0,"cancel while awaiting preparation never launches generation");token.Dispose();
 }catch(Exception ex){error=ex;}finally{f.Close();}};Application.Run(f);
 }
 if(error!=null)throw error;return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
