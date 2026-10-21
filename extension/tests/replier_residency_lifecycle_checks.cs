using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Reflection;using System.Threading;using System.Threading.Tasks;using System.Windows.Forms;using System.Net.Http;using ReplierDesktop;
public static class ResidencyLifecycleChecks{
 sealed class Publisher:IYoutubePublisher{
  public YoutubeAccount Account{get{return null;}}
  public Task Restore(CancellationToken t){throw new MissingYoutubeConnectionException();}
  public Task Connect(string f,CancellationToken t){throw new Exception("No login allowed");}
  public void Disconnect(){}
  public Task<PostedComment> Publish(string i,string c,string a,CancellationToken t){throw new Exception("No posting allowed");}
 }
 static void Check(bool ok,string message){if(!ok)throw new Exception(message);Console.WriteLine("PASS "+message);}
 static Task Warm(MainForm f){return (Task)typeof(MainForm).GetField("warmupTask",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(f);}
 static bool ServerUp(){try{using(var c=new HttpClient(new HttpClientHandler{UseProxy=false}){Timeout=TimeSpan.FromSeconds(1)})return c.GetAsync(LocalModel.Endpoint+"/api/ps").GetAwaiter().GetResult().IsSuccessStatusCode;}catch{return false;}}
 [STAThread]public static int Main(string[] args){try{
 Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
 Check(!ServerUp(),"test starts without a foreign server");
 foreach(bool early in new[]{false,true}){
 Exception error=null;Task work=null;
 using(var f=new MainForm(Path.Combine(args[0],early?"early":"normal","history.json"),new Publisher())){
  f.Opacity=0;f.ShowInTaskbar=false;
  f.Shown+=async(s,e)=>{try{
   work=Warm(f);Check(work!=null,"show starts model preparation");
   if(early){await Task.Delay(100);f.Close();return;}
   await work;var loaded=await LocalModel.LoadedOnGpu(CancellationToken.None);
   Check(DualCommentService.Models.All(loaded.Contains),"both models loaded on GPU at app startup");
   var service=(DualCommentService)typeof(MainForm).GetField("comments",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(f);
   var runtimes=(List<LocalModel>)typeof(DualCommentService).GetField("owned",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(service);
   foreach(var m in runtimes){await m.Chat(new{model=m.Name,stream=false,think=false,keep_alive="30s",options=new{num_ctx=8192,num_predict=12},messages=new[]{new{role="user",content="확인이라고만 답하세요."}}},CancellationToken.None);await m.Unload();}
   await Task.Delay(32000);
   loaded=await LocalModel.LoadedOnGpu(CancellationToken.None);
   Check(DualCommentService.Models.All(loaded.Contains),"transition unload and legacy 30s keep_alive do not evict resident models");
  }catch(Exception ex){error=ex;}finally{if(!early && !f.IsDisposed)f.Close();}};
  Application.Run(f);
 }
 var until=DateTime.UtcNow.AddSeconds(8);while((ServerUp() || (work!=null&&!work.IsCompleted)) && DateTime.UtcNow<until){Application.DoEvents();Thread.Sleep(50);}
 Check(!ServerUp(),early?"closing during startup leaves no model server":"closing ready app releases model server and runners");
 Check(work!=null && work.IsCompleted,"startup task ends after window closes");if(error!=null)throw error;
 }
 return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
