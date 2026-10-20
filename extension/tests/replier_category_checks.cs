using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using ReplierDesktop;
public static class CategoryChecks
{
 static void Check(bool ok,string name){if(!ok)throw new Exception(name);Console.WriteLine("PASS "+name);}
 static Video V(int i){return new Video {Id="C"+i.ToString("D10"),Title="게임 영상 추천 "+i};}
 static VideoContent C(Video v,string original="ko",bool auto=true){return new VideoContent {Version=1,VideoId=v.Id,Language="ko",OriginalLanguage=original,IsAuto=auto,Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=new List<CaptionCue>{new CaptionCue{StartMs=0,DurationMs=1000,Text="실제 데이터가 아닌 검사 대사"}}};}
 [STAThread] public static int Main(string[] args)
 {
  try{
   ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;
   string output=Path.GetFullPath(args[0]);Directory.CreateDirectory(output);
   string run=Path.Combine(output,"run-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(run);
   Check(VideoCategories.All.Length==16 && VideoCategories.All.Select(c=>c.Id).Distinct().Count()==16,"fifteen upload categories plus explicit all option");
   string html="<meta content='https://www.youtube.com/watch?v=HPUpsEzL1ps' property='og:url'><meta content='Gaming' itemprop='genre'>";
   Check(CategoryService.Parse(html,"HPUpsEzL1ps")=="20","category metadata parses independent of attribute order");
   Check(CategoryService.Parse(html,"gx4mlQJHtJY")==null,"wrong video identity cannot supply category");
   Check(CategoryService.Parse(html.Replace("Gaming","Mystery"),"HPUpsEzL1ps")==null && CategoryService.Parse("<title>Gaming</title>","HPUpsEzL1ps")==null,"unknown category and title keywords do not pass metadata filter");
   Check(CategoryService.Parse(html.Replace("Gaming","Film &amp; Animation"),"HPUpsEzL1ps")=="1","HTML-encoded category maps to upload category");
   Check(KoreanVideos.TitleMatches("스팀 신작 게임 TOP 10") && !KoreanVideos.TitleMatches("Game of the year") && !KoreanVideos.TitleMatches("公司承諾給我10萬年終獎"),"Korean title required and foreign titles rejected");
   Check(KoreanVideos.ContentMatches(C(V(0))) && !KoreanVideos.ContentMatches(C(V(0),"en",false)),"translated Korean captions do not prove Korean original");
   Check(!KoreanVideos.ContentMatches(C(V(0),null,false)) && KoreanVideos.ContentMatches(C(V(0),null,true)),"unknown manual caption origin excluded while legacy Korean ASR remains usable");
   var config=Path.Combine(run,"settings.json");File.WriteAllText(config,"{\"UploadPeriod\":\"month\"}");
   var store=new SettingsStore(config);
   Check(store.Load().CategoryId=="20" && store.Load().UploadPeriod=="month","old settings migrate to gaming without resetting upload period");
   foreach(var category in VideoCategories.All){store.Save(new ReplierSettings{CategoryId=category.Id,UploadPeriod="day"});Check(store.Load().CategoryId==category.Id,"category persists: "+category.Id);}
   bool rejected=false;try{store.Save(new ReplierSettings{CategoryId="999"});}catch(InvalidDataException){rejected=true;}
   Check(rejected,"invalid category cannot be saved");
   var ledger=new VideoLedger(Path.Combine(run,"ledger.jsonl"));var content=new ContentStore(Path.Combine(run,"content"));
   int captions=0;
   var batch=VideoBatch.Collect("게임",ledger,content,CancellationToken.None,
    search:(q,t)=>Task.FromResult(Enumerable.Range(0,5).Select(V).ToList()),
    captions:(v,t)=>{captions++;return Task.FromResult(C(v,v.Id==V(3).Id?"en":"ko",v.Id!=V(3).Id));},
    category:"20",categories:(v,t)=>Task.FromResult(v.Id==V(1).Id?"24":v.Id==V(2).Id?null:"20"),koreanOnly:true).GetAwaiter().GetResult();
   Check(batch.Videos.Count==2 && batch.CategoryExcluded==1 && batch.CategoryUnknown==1 && batch.LanguageExcluded==1,"category mismatch unknown and foreign original excluded separately");
   Check(captions==3 && ledger.ReadIds().Count==0,"category rejects occur before captions and selection history remains unused");
   var later=VideoBatch.Collect("예능",ledger,content,CancellationToken.None,
    search:(q,t)=>Task.FromResult(new List<Video>{V(1)}),captions:(v,t)=>Task.FromResult(C(v)),category:"24",categories:(v,t)=>Task.FromResult("24"),koreanOnly:true).GetAwaiter().GetResult();
   Check(later.Videos.Count==1,"category excluded video remains available after switching category");
   var topics=TopicService.Discover("",new string[0],0,CancellationToken.None,(q,t)=>{Check(!q.Contains("게임"),"music discovery does not use gaming seeds");return Task.FromResult(new List<string>{q+" 추천"});},category:"10").GetAwaiter().GetResult();
   Check(topics.Topics.Count>0,"other category discovers actual supplied autocomplete candidates");
   Check(CategoryService.Fetch(new Video{Id="HPUpsEzL1ps"},CancellationToken.None).GetAwaiter().GetResult()=="20","actual public gaming video identifies Gaming category");
   Check(CategoryService.Fetch(new Video{Id="dQw4w9WgXcQ"},CancellationToken.None).GetAwaiter().GetResult()=="10","actual public music video identifies Music category");
   var live=VideoBatch.Collect("인디 게임 추천",new VideoLedger(Path.Combine(run,"live.jsonl")),new ContentStore(Path.Combine(run,"live-content")),CancellationToken.None,category:"20",koreanOnly:true).GetAwaiter().GetResult();
   Check(live.Videos.Count>0 && live.Videos.Count<=10 && live.Error.Length==0,"actual batch returns Korean-captioned gaming videos only");
   foreach(var video in live.Videos)Console.WriteLine("ACTUAL "+video.Title);
   Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
   string ui=Path.Combine(run,"ui");Directory.CreateDirectory(ui);
   using(var form=new MainForm(Path.Combine(ui,"history.json"))){
    form.ShowInTaskbar=false;form.Opacity=0;form.Show();Application.DoEvents();
    var category=(ComboBox)form.Controls.Find("Category",true)[0];var period=(ComboBox)form.Controls.Find("UploadPeriod",true)[0];
    Check(category.SelectedIndex==VideoCategories.Index("20"),"native default is Gaming");
    category.SelectedIndex=VideoCategories.Index("10");period.SelectedIndex=2;
    Check(new SettingsStore(Path.Combine(ui,"settings.json")).Load().CategoryId=="10","native category change saved immediately");
    using(var locked=new FileStream(Path.Combine(ui,"settings.json.new"),FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None)){
     category.SelectedIndex=VideoCategories.Index("17");Check(category.SelectedIndex==VideoCategories.Index("10"),"failed category save restores prior control value");
    }
    var table=(TableLayoutPanel)category.Parent;
    Check(new[]{"Category","UploadPeriod","Query","Recommend"}.All(n=>table.GetRow(form.Controls.Find(n,true)[0])==0),"all search controls share a single row");
    var grid=(DataGridView)form.Controls.Find("Videos",true)[0];for(int i=0;i<10;i++)grid.Rows.Add("추천 영상 "+i,"채널","12:34","123회","1일 전");
    Application.DoEvents();
    Check(grid.GetRowDisplayRectangle(9,false).Bottom<=grid.ClientSize.Height && grid.Rows[9].Displayed,"ten recommendation rows visible at initial fitted window size");
    using(var bitmap=new Bitmap(form.Width,form.Height)){form.DrawToBitmap(bitmap,new Rectangle(Point.Empty,bitmap.Size));bitmap.Save(Path.Combine(output,"category-preview.png"),ImageFormat.Png);}
    form.Close();
   }
   using(var form=new MainForm(Path.Combine(ui,"history.json")))Check(((ComboBox)form.Controls.Find("Category",true)[0]).SelectedIndex==VideoCategories.Index("10"),"category survives native window restart");
   return 0;
  }catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}
 }
}
