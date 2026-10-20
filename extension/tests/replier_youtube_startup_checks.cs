using System;using System.IO;using System.Threading;using System.Threading.Tasks;using System.Windows.Forms;using ReplierDesktop;
public static class YoutubeStartupChecks
{
 static void Check(bool ok,string message){if(!ok)throw new Exception(message);Console.WriteLine("PASS "+message);}
 sealed class Publisher:IYoutubePublisher
 {
  public YoutubeAccount Account{get;private set;}public string Mode;public int Restores,Connections;public bool Cancelled;
  public TaskCompletionSource<int> Hold=new TaskCompletionSource<int>();
  public Publisher(string mode){Mode=mode;}
  public Task Connect(string f,CancellationToken t){Connections++;throw new Exception("must not start interactive login");}
  public async Task Restore(CancellationToken t){Restores++;if(Mode=="missing")throw new MissingYoutubeConnectionException();if(Mode=="error")throw new InvalidOperationException("synthetic failure");
   if(Mode=="hold")try{using(t.Register(()=>Hold.TrySetCanceled()))await Hold.Task;}catch(OperationCanceledException){Cancelled=true;throw;}
   t.ThrowIfCancellationRequested();Account=new YoutubeAccount{Id="UCaaaaaaaaaaaaaaaaaaaaaa",Title="자동 연결 검사 채널"};
  }
  public void Disconnect(){Account=null;}public Task<PostedComment> Publish(string id,string text,string a,CancellationToken t){throw new Exception("must not post");}
 }
 [STAThread]public static int Main(string[] args){try{
 Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);string output=Path.GetFullPath(args[0]);Directory.CreateDirectory(output);
 foreach(string mode in new[]{"success","missing","error","hold","close"})
 {
  var p=new Publisher(mode=="close"?"hold":mode);Exception error=null;Task work=null;
  using(var f=new MainForm(Path.Combine(output,Guid.NewGuid().ToString("N"),"history.json"),p))
  {
   f.Opacity=0;f.ShowInTaskbar=false;f.Shown+=async(sender,e)=>{try{
    work=f.ConnectionTask;
    if(mode=="hold" || mode=="close"){
     Check(!work.IsCompleted && f.Controls.Find("Recommend",true)[0].Enabled,"automatic connection does not block general search");
     Check(f.MainMenuStrip.Items["ConnectedYoutubeChannel"].Text.Contains("자동 연결 중"),"pending restore is visible");
     if(mode=="close"){f.Close();return;}p.Hold.SetResult(0);
    }
    await work;
    Check(p.Restores==1 && p.Connections==0,"startup restores once without opening login: "+mode);
    var text=f.MainMenuStrip.Items["ConnectedYoutubeChannel"].Text;
    if(mode=="success" || mode=="hold")Check(p.Account!=null && text.Contains(p.Account.Title),"saved channel displayed automatically: "+mode);
    if(mode=="missing")Check(text.Contains("연결 안 됨"),"first run without saved credentials stays quietly disconnected");
    if(mode=="error")Check(text.Contains("확인 필요") && f.Controls.Find("Recommend",true)[0].Enabled,"failed restore offers reconnection while search remains usable");
    Check(((ToolStripMenuItem)((ToolStripMenuItem)f.MainMenuStrip.Items["MainMenu"]).DropDownItems["YoutubeConnectionMenu"]).Enabled,"connection menu available after restore finishes");
   }catch(Exception ex){error=ex;}finally{if(mode!="close")f.Close();}};
   Application.Run(f);
  }
  if(mode=="close"){
   var deadline=DateTime.UtcNow.AddSeconds(3);while(!work.IsCompleted && DateTime.UtcNow<deadline){Application.DoEvents();Thread.Sleep(5);}
   Check(work.IsCompleted && p.Account==null,"closing cancels automatic restore without stale sign-in");
  }
  if(error!=null)throw error;
 }
 return 0;}catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
