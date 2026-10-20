using System;using System.IO;using System.Linq;using System.Reflection;using System.Threading;using System.Threading.Tasks;using System.Windows.Forms;using ReplierDesktop;
public static class SearchWarmupChecks{
 static void Check(bool ok,string message){if(!ok)throw new Exception(message);Console.WriteLine("PASS "+message);}
 [STAThread]public static int Main(string[] args){try{
 Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);string run=Path.Combine(Path.GetFullPath(args[0]),Guid.NewGuid().ToString("N"));Directory.CreateDirectory(run);Exception error=null;int calls=0;CancellationToken warmToken=CancellationToken.None;var started=new TaskCompletionSource<int>();var cancelled=new TaskCompletionSource<int>();
 using(var form=new MainForm(Path.Combine(run,"history.json"))){form.Opacity=0;form.ShowInTaskbar=false;var field=typeof(MainForm).GetField("comments",BindingFlags.Instance|BindingFlags.NonPublic);((DualCommentService)field.GetValue(form)).Dispose();field.SetValue(form,new DualCommentService((m,v,c,t,r)=>{throw new Exception("search must not generate comments");},preparer:async t=>{warmToken=t;calls++;started.SetResult(0);using(t.Register(()=>cancelled.TrySetResult(0))){await Task.Delay(Timeout.Infinite,t);}}));
 form.Shown+=async(s,e)=>{try{
 ((ComboBox)form.Controls.Find("SearchMode",true)[0]).SelectedIndex=0;((ComboBox)form.Controls.Find("UploadPeriod",true)[0]).SelectedIndex=3;((TextBox)form.Controls.Find("Query",true)[0]).Text="마인크래프트";
 var search=form.AcquireVideos();await started.Task;Check(!search.IsCompleted,"warmup starts while actual video search is in progress");await search;
 Check(((DataGridView)form.Controls.Find("Videos",true)[0]).Rows.Count>0,"actual search finishes while optional model warmup remains pending");
 Check(calls==1 && !cancelled.Task.IsCompleted,"warmup is not mistaken for comment generation or cancelled on successful search");
 }catch(Exception ex){error=ex;}finally{form.Close();}};Application.Run(form);}
 Check(warmToken.IsCancellationRequested,"closing window cancels its pending warmup");if(error!=null)throw error;return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}}
