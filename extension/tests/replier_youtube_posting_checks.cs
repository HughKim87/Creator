using System;using System.Collections.Generic;using System.Drawing;using System.IO;using System.Linq;using System.Net;using System.Net.Http;using System.Reflection;using System.Text;using System.Threading;using System.Threading.Tasks;using System.Web;using System.Web.Script.Serialization;using System.Windows.Forms;using ReplierDesktop;
public static class YoutubePostingChecks
{
 const string Author="UCaaaaaaaaaaaaaaaaaaaaaa",Owner="UCbbbbbbbbbbbbbbbbbbbbbb",VideoId="V0000000001";
 static void Check(bool ok,string name){if(!ok)throw new Exception(name);Console.WriteLine("PASS "+name);}
 static void Throws(Action action,string name){try{action();}catch(InvalidOperationException){Check(true,name);return;}throw new Exception(name);}
 sealed class Store:IYoutubeCredentialStore{public YoutubeCredentials Value;public YoutubeCredentials Load(){return Value;}public void Save(YoutubeCredentials value){Value=value;}}
 sealed class Handler:HttpMessageHandler
 {
  public int Posts,Tokens,Refreshes;public string Body,TokenBody,Reason="",CurrentAuthor=Author;public int Status=200;public bool Broken,CancelPost,ShortExpiry;public TaskCompletionSource<int> Hold;
  protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage r,CancellationToken t)
  {
   string path=r.RequestUri.AbsolutePath;
   if(path=="/token")
   {
    Tokens++;TokenBody=await r.Content.ReadAsStringAsync();bool refresh=TokenBody.Contains("refresh_token");if(refresh)Refreshes++;
    return Json(200,new{access_token="synthetic-access",refresh_token="synthetic-refresh",expires_in=ShortExpiry && !refresh?1:3600,scope=YoutubeOAuth.Scope});
   }
   Check(r.Headers.Authorization!=null && r.Headers.Authorization.Scheme=="Bearer","API uses bearer authorization header");
   if(path.EndsWith("/channels"))
   {if(Hold!=null)await Hold.Task;return Json(200,new{items=new[]{new{id=CurrentAuthor,snippet=new{title="합성 작성 채널"}}}});}
   if(path.EndsWith("/videos")){Check(r.RequestUri.Query.Contains(VideoId),"video metadata lookup uses captured video ID");return Json(200,new{items=new[]{new{id=VideoId,snippet=new{channelId=Owner}}}});}
   if(path.EndsWith("/commentThreads"))
   {
    Posts++;Body=await r.Content.ReadAsStringAsync();if(CancelPost)throw new TaskCanceledException();
    if(Status!=200)return Json(Status,new{error=new{errors=new[]{new{reason=Reason}}}});
    if(Broken)return new HttpResponseMessage(HttpStatusCode.OK){Content=new StringContent("{broken")};
    return Json(200,new{id="thread",snippet=new{videoId=VideoId,topLevelComment=new{id="synthetic-comment"}}});
   }
   throw new Exception("unexpected endpoint");
  }
 }
 static HttpResponseMessage Json(int status,object value){return new HttpResponseMessage((HttpStatusCode)status){Content=new StringContent(new JavaScriptSerializer().Serialize(value),Encoding.UTF8,"application/json")};}
 static Store Ready(){return new Store{Value=new YoutubeCredentials{ClientId="synthetic.apps.googleusercontent.com",ClientSecret="synthetic-secret",RefreshToken="synthetic-refresh"}};}
 static async Task ApiChecks(string root)
 {
  Check(YoutubeOAuth.Challenge("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk")=="E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM","PKCE S256 matches RFC vector");
  Check(YoutubeOAuth.RandomValue().Length==43 && YoutubeOAuth.RandomValue()!=YoutubeOAuth.RandomValue(),"state and verifier have random entropy");
  Throws(()=>YoutubeOAuth.ParseClient("{\"web\":{\"client_id\":\"synthetic.apps.googleusercontent.com\"}}"),"web OAuth clients rejected");
  Throws(()=>YoutubeOAuth.ValidateCallback("/callback?state=wrong&code=x","expected"),"wrong OAuth state rejected");
  Throws(()=>YoutubeOAuth.ValidateCallback("/callback?state=expected&error=access_denied","expected"),"OAuth denial rejected");
  Check(YoutubeOAuth.ValidateCallback("/callback?state=expected&code=synthetic","expected")=="synthetic","matching callback accepted");
  Task browser=null;string challenge=null;
  string grant=await YoutubeOAuth.AuthorizeWithBrowser("synthetic.apps.googleusercontent.com",CancellationToken.None,url=>{
   var query=HttpUtility.ParseQueryString(new Uri(url).Query);challenge=query["code_challenge"];
   browser=Task.Run(async()=>{using(var h=new HttpClient()){
    var wrong=await h.GetAsync(query["redirect_uri"]+"?state=wrong&code=bad");Check(wrong.StatusCode==HttpStatusCode.BadRequest,"loopback refuses unsolicited state");
    var valid=await h.GetAsync(query["redirect_uri"]+"?state="+query["state"]+"&code=synthetic");Check(valid.IsSuccessStatusCode,"real loopback callback completes");
   }});
  });await browser;
  var parts=new JavaScriptSerializer().Deserialize<string[]>(grant);Check(parts[0]=="synthetic" && YoutubeOAuth.Challenge(parts[2])==challenge,"loopback grant retains matching PKCE verifier");
  string encrypted=Path.Combine(root,"youtube-private","synthetic.bin");var encryptedStore=new EncryptedYoutubeCredentialStore(encrypted);encryptedStore.Save(Ready().Value);
  Check(!Encoding.UTF8.GetString(File.ReadAllBytes(encrypted)).Contains("synthetic-refresh") && encryptedStore.Load().ClientId==Ready().Value.ClientId,"Windows user encryption round trips without plaintext token on disk");
  encryptedStore.Save(null);Check(encryptedStore.Load()==null,"disconnect removes usable saved credential");
  string file=Path.Combine(root,"synthetic-client.json");File.WriteAllText(file,"{\"installed\":{\"client_id\":\"synthetic.apps.googleusercontent.com\",\"client_secret\":\"synthetic-secret\"}}");
  var storage=new Store();var handler=new Handler();
  using(var service=new YoutubePublisher(storage,handler,(id,t)=>Task.FromResult("[\"synthetic-code\",\"http://127.0.0.1:1234/callback\",\"synthetic-verifier\"]")))
  {
   await service.Connect(file,CancellationToken.None);Check(service.Account.Id==Author && storage.Value!=null && handler.TokenBody.Contains("code_verifier"),"connect validates channel before saving refresh credentials");
   var sent=await service.Publish(VideoId,"  수정한 댓글입니다  ",Author,CancellationToken.None);
   var payload=new JavaScriptSerializer().DeserializeObject(handler.Body);var snippet=CaptionService.Get(payload,"snippet");
   Check(handler.Posts==1 && (string)CaptionService.Get(snippet,"channelId")==Owner && (string)CaptionService.Get(snippet,"videoId")==VideoId,"one POST targets exact video and uploader channel");
   Check((string)CaptionService.Get(CaptionService.Get(CaptionService.Get(snippet,"topLevelComment"),"snippet"),"textOriginal")=="수정한 댓글입니다","edited comment sent exactly after whitespace trim");
   Check(sent.Id=="synthetic-comment" && sent.Url.Contains("lc=synthetic-comment"),"success returns created comment link");
   handler.CurrentAuthor=Owner;bool rejected=false;try{await service.Publish(VideoId,"댓글",Author,CancellationToken.None);}catch(InvalidOperationException){rejected=true;}
   Check(rejected && handler.Posts==1,"changed author cannot post under stale confirmation");
  }
  handler=new Handler{ShortExpiry=true};using(var service=new YoutubePublisher(new Store(),handler,(id,t)=>Task.FromResult("[\"code\",\"http://127.0.0.1:1234/callback\",\"verifier\"]")))
  {await service.Connect(file,CancellationToken.None);Check(handler.Refreshes==1,"expired access token refreshes without repeating login");}
  handler=new Handler();using(var service=new YoutubePublisher(Ready(),handler))
  {
   await service.Restore(CancellationToken.None);handler.Hold=new TaskCompletionSource<int>();var first=service.Publish(VideoId,"첫 댓글",Author,CancellationToken.None);bool rejected=false;
   try{await service.Publish(VideoId,"둘째 댓글",Author,CancellationToken.None);}catch(InvalidOperationException){rejected=true;}
   handler.Hold.SetResult(0);await first;Check(rejected && handler.Posts==1,"concurrent submission is rejected rather than queued");
  }
  foreach(string mode in new[]{"disabled","timeout","server","broken"})
  {
   handler=new Handler();using(var service=new YoutubePublisher(Ready(),handler))
   {
    await service.Restore(CancellationToken.None);if(mode=="disabled"){handler.Status=403;handler.Reason="commentsDisabled";}if(mode=="timeout")handler.CancelPost=true;if(mode=="server")handler.Status=503;if(mode=="broken")handler.Broken=true;
    bool uncertain=false,rejected=false;try{await service.Publish(VideoId,"댓글",Author,CancellationToken.None);}catch(PostingUncertainException){uncertain=true;}catch(InvalidOperationException ex){rejected=ex.Message.Contains("사용 중지");}
    Check(handler.Posts==1 && (mode=="disabled"?rejected:uncertain),mode+" has explicit outcome and no automatic repost");
   }
  }
 }
 sealed class FakePublisher:IYoutubePublisher
 {
  public YoutubeAccount Account {get;set;}public int Posts;public string Text,Video,AuthorId;public bool Uncertain;public TaskCompletionSource<int> Hold=new TaskCompletionSource<int>();
  public Task Connect(string file,CancellationToken t){Account=new YoutubeAccount{Id=Author,Title="합성 채널"};return Task.FromResult(0);}
  public Task Restore(CancellationToken t){return Connect(null,t);}public void Disconnect(){Account=null;}
  public async Task<PostedComment> Publish(string video,string text,string author,CancellationToken t){Posts++;Text=text;Video=video;AuthorId=author;await Hold.Task;if(Uncertain)throw new PostingUncertainException();return new PostedComment{Id="synthetic",VideoId=video};}
 }
 static T Find<T>(Form form,string name)where T:Control{return (T)form.Controls.Find(name,true)[0];}
 static void DialogChecks(string root)
 {
  Exception error=null;var publisher=new FakePublisher();var v=new Video{Id=VideoId,Title="선택한 합성 영상"};
  using(var form=new YoutubePostDialog(v,"원본 추천 댓글",publisher))
  {
   form.Opacity=0;form.Shown+=async(sender,e)=>{try{
    var post=Find<Button>(form,"PublishYoutube");Check(!post.Enabled,"posting disabled before account is connected");
    Find<Button>(form,"RestoreYoutube").PerformClick();await form.OperationTask;
    Check(post.Enabled && Find<Label>(form,"PostingAccount").Text.Contains(Author),"connected posting channel is visible");
    Find<TextBox>(form,"PostText").Text="사용자가 고친 댓글";v.Id="V9999999999";post.PerformClick();var work=form.OperationTask;post.PerformClick();
    Check(!post.Enabled && !Find<Button>(form,"ClosePosting").Enabled && publisher.Posts==1,"post locks controls and duplicate clicks send once");
    Check(publisher.Video==VideoId && publisher.Text=="사용자가 고친 댓글" && publisher.AuthorId==Author,"dialog freezes video and submits reviewed text with confirmed author");
    publisher.Hold.SetResult(0);await work;Check(!post.Enabled && Find<Label>(form,"PostStatus").Text.Contains("등록"),"successful dialog cannot repost");
    Application.DoEvents();Check(Find<LinkLabel>(form,"PostedCommentLink").Visible,"created comment link is visible after success");
    using(var bmp=new Bitmap(form.Width,form.Height)){form.DrawToBitmap(bmp,new Rectangle(Point.Empty,bmp.Size));bmp.Save(Path.Combine(root,"posting-preview.png"));}
   }catch(Exception ex){error=ex;}finally{form.Close();}};Application.Run(form);
  }
  if(error!=null)throw error;
  publisher=new FakePublisher{Account=new YoutubeAccount{Id=Author,Title="합성 채널"},Uncertain=true};
  using(var form=new YoutubePostDialog(new Video{Id=VideoId,Title="합성 영상"},"댓글",publisher))
  {
   form.Opacity=0;form.Shown+=async(sender,e)=>{try{
    var post=Find<Button>(form,"PublishYoutube");post.PerformClick();publisher.Hold.SetResult(0);await form.OperationTask;post.PerformClick();
    Check(publisher.Posts==1 && !post.Enabled && Find<Label>(form,"PostStatus").Text.Contains("확인하지 못"),"uncertain result disables retry and requests manual verification");
   }catch(Exception ex){error=ex;}finally{form.Close();}};Application.Run(form);
  }
  if(error!=null)throw error;
  publisher=new FakePublisher{Account=new YoutubeAccount{Id=Author,Title="합성 채널"}};
  using(var form=new YoutubePostDialog(new Video{Id=VideoId,Title="합성 영상"},"댓글",publisher))
  {form.Opacity=0;form.Shown+=(sender,e)=>Find<Button>(form,"ClosePosting").PerformClick();Application.Run(form);Check(publisher.Posts==0,"closing review without posting sends nothing");}
 }
 [STAThread]public static int Main(string[] args){try{Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);string root=Path.Combine(Path.GetFullPath(args[0]),Guid.NewGuid().ToString("N"));Directory.CreateDirectory(root);ApiChecks(root).GetAwaiter().GetResult();DialogChecks(root);return 0;}catch(Exception ex){Console.Error.WriteLine(ex.GetType().Name+": "+ex.Message);return 1;}}
}
