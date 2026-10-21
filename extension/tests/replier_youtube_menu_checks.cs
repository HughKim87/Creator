using System;using System.Drawing;using System.IO;using System.Linq;using System.Reflection;using System.Threading;using System.Threading.Tasks;using System.Windows.Forms;using ReplierDesktop;
public static class YoutubeMenuChecks
{
 const string Channel="UCaaaaaaaaaaaaaaaaaaaaaa";
 static void Check(bool ok,string text){if(!ok)throw new Exception(text);Console.WriteLine("PASS "+text);}
 static T Find<T>(Form form,string name)where T:Control{return (T)form.Controls.Find(name,true)[0];}
 sealed class Publisher:IYoutubePublisher
 {
  public YoutubeAccount Account{get;set;}public int Connections,Restores,Posts;public TaskCompletionSource<int> Hold;public bool MissingFirstRestore;
  public async Task Connect(string file,CancellationToken t){Connections++;if(Hold!=null)using(t.Register(()=>Hold.TrySetCanceled()))await Hold.Task;t.ThrowIfCancellationRequested();Account=new YoutubeAccount{Id=Channel,Title="합성 연결 채널"};}
  public Task Restore(CancellationToken t){Restores++;if(MissingFirstRestore){MissingFirstRestore=false;throw new MissingYoutubeConnectionException();}return Connect(null,t);}public void Disconnect(){Account=null;}
  public Task<PostedComment> Publish(string id,string text,string author,CancellationToken t){Posts++;throw new Exception("must not post");}
 }
 static void DialogChecks(string output)
 {
  Exception error=null;var publisher=new Publisher();
  using(var f=new YoutubeConnectionDialog(publisher,()=>"synthetic.json"))
  {
   f.Opacity=0;f.Shown+=async(sender,e)=>{try{
    Check(f.Controls.Find("PostText",true).Length==0 && f.Controls.Find("PublishYoutube",true).Length==0,"connection window needs neither video nor comment and has no posting action");
    Find<Button>(f,"ConnectYoutube").PerformClick();await f.OperationTask;
    Check(publisher.Connections==1 && Find<Label>(f,"ConnectedAccount").Text.Contains(Channel),"selected connection file connects and shows verified channel");
    Find<Button>(f,"DisconnectYoutube").PerformClick();Check(publisher.Account==null && !Find<Button>(f,"DisconnectYoutube").Enabled,"disconnect updates account and buttons");
    Find<Button>(f,"RestoreYoutube").PerformClick();await f.OperationTask;Check(publisher.Restores==1 && publisher.Account!=null,"saved connection can be restored independently of posting");
    Application.DoEvents();using(var b=new Bitmap(f.Width,f.Height)){f.DrawToBitmap(b,new Rectangle(Point.Empty,b.Size));b.Save(Path.Combine(output,"connection-preview.png"));}
    Check(publisher.Posts==0,"connection actions never post a comment");
   }catch(Exception ex){error=ex;}finally{f.Close();}};Application.Run(f);
  }
  if(error!=null)throw error;
  publisher=new Publisher{Hold=new TaskCompletionSource<int>()};Task work=null;
  using(var f=new YoutubeConnectionDialog(publisher,()=>"synthetic.json"))
  {
   f.Opacity=0;f.Shown+=(sender,e)=>{Find<Button>(f,"ConnectYoutube").PerformClick();work=f.OperationTask;Check(!Find<Button>(f,"ConnectYoutube").Enabled,"connection blocks duplicate clicks while pending");f.Close();};Application.Run(f);
  }
  var deadline=DateTime.UtcNow.AddSeconds(3);while(!work.IsCompleted && DateTime.UtcNow<deadline){Application.DoEvents();Thread.Sleep(5);}
  Check(work.IsCompleted && publisher.Account==null,"closing pending connection cancels without signing in later");
 }
 static void MainChecks(string output)
 {
  var publisher=new Publisher{MissingFirstRestore=true};
  using(var f=new MainForm(Path.Combine(output,"history.json"),publisher))
  {
   f.Opacity=0;f.ShowInTaskbar=false;f.Show();Application.DoEvents();while(!f.ConnectionTask.IsCompleted){Application.DoEvents();Thread.Sleep(5);}
   var menu=(MenuStrip)f.MainMenuStrip;var root=(ToolStripMenuItem)menu.Items["MainMenu"];var connection=(ToolStripMenuItem)root.DropDownItems["YoutubeConnectionMenu"];
   Check(connection.Enabled && Find<DataGridView>(f,"Videos").Rows.Count==0,"YouTube menu available before any video selection");
   bool opened=false;using(var timer=new System.Windows.Forms.Timer{Interval=40})
   {
    timer.Tick+=(sender,e)=>{var d=Application.OpenForms.Cast<Form>().FirstOrDefault(x=>x is YoutubeConnectionDialog);if(d==null)return;opened=true;Find<Button>(d,"RestoreYoutube").PerformClick();d.Close();timer.Stop();};
    timer.Start();connection.PerformClick();
   }
   Check(opened && publisher.Account!=null && menu.Items["ConnectedYoutubeChannel"].Text.Contains("합성 연결 채널"),"menu opens account window and refreshes shared connected channel label");
   var input=Find<TextBox>(f,"Query");var modes=Find<ComboBox>(f,"SearchMode");modes.SelectedIndex=2;input.Text="";
   var method=typeof(MainForm).GetMethod("ChannelRecommendationInput",BindingFlags.NonPublic|BindingFlags.Instance);
   Check((string)method.Invoke(f,null)=="https://www.youtube.com/channel/"+Channel,"blank channel recommendation uses signed-in channel");
   input.Text="https://www.youtube.com/@another-channel";Check((string)method.Invoke(f,null)==input.Text,"explicit channel link remains available and takes priority");
   publisher.Disconnect();typeof(MainForm).GetMethod("UpdateYoutubeConnection",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(f,null);input.Text="";
   Check((string)method.Invoke(f,null)=="" && menu.Items["ConnectedYoutubeChannel"].Text.Contains("연결 안 됨"),"disconnect removes own-channel fallback and updates menu state");
   foreach(var size in new[]{new Size(800,600),new Size(1024,720)})
   {
    f.Size=size;f.PerformLayout();Application.DoEvents();var search=Find<ComboBox>(f,"SearchMode");var bounds=f.RectangleToClient(search.RectangleToScreen(search.ClientRectangle));
    Check(bounds.Top>=menu.Bottom && f.ClientRectangle.Contains(menu.Bounds),"menu does not overlap search controls at "+size.Width);
   }
   using(var b=new Bitmap(f.Width,f.Height)){f.DrawToBitmap(b,new Rectangle(Point.Empty,b.Size));b.Save(Path.Combine(output,"menu-preview.png"));}
   Check(publisher.Posts==0,"menu and channel defaults do not trigger posting");f.Close();
  }
 }
 [STAThread]public static int Main(string[] args){try{Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);string output=Path.Combine(Path.GetFullPath(args[0]),Guid.NewGuid().ToString("N"));Directory.CreateDirectory(output);DialogChecks(output);MainChecks(output);return 0;}catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}}
}
