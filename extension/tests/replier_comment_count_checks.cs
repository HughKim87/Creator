using System;using System.Collections.Generic;using System.Drawing;using System.Drawing.Imaging;using System.IO;using System.Linq;using System.Net;using System.Threading;using System.Threading.Tasks;using System.Web.Script.Serialization;using System.Windows.Forms;using ReplierDesktop;
public static class CommentCountChecks
{
 static void Check(bool ok,string label){if(!ok)throw new Exception(label);Console.WriteLine("PASS "+label);}
 static Video V(int i){return new Video{Id="N"+i.ToString("D10"),Title="게임 영상 "+i};}
 static VideoContent C(Video v){return new VideoContent{Version=1,VideoId=v.Id,Language="ko",IsAuto=true,Source="YouTube 공개 자막",AcquiredAt=DateTime.UtcNow.ToString("o"),Cues=new List<CaptionCue>{new CaptionCue{Text="검사용 대사"}}};}
 [STAThread] public static int Main(string[] args){try{
 ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;
 Check(CommentCounts.Normalize("1,234 Comments")=="1,234개" && CommentCounts.Normalize("댓글 2.3만개")=="2.3만개","full and abbreviated public comment counts preserved");
 Check(CommentCounts.Normalize("0 Comments")=="0개" && CommentCounts.Normalize("Comments")==null && CommentCounts.Normalize("Comments are turned off.")==null,"zero is explicit and not inferred from missing or disabled labels");
 object disabled=new JavaScriptSerializer().DeserializeObject("{\"messageRenderer\":{\"text\":{\"simpleText\":\"Comments are turned off.\"}}}");
 Check(CommentCounts.HeaderCount(disabled)=="사용 중지","explicit disabled comments distinguished from zero");
 var video=V(0);string meta="<meta property='og:url' content='https://www.youtube.com/watch?v="+video.Id+"'><meta itemprop='genre' content='Gaming'>";
 string json="{\"contents\":{\"twoColumnWatchNextResults\":{\"results\":{\"results\":{\"contents\":[{\"itemSectionRenderer\":{\"targetId\":\"comments-section\",\"header\":{\"commentsHeaderRenderer\":{\"countText\":{\"runs\":[{\"text\":\"123 Comments\"}]}}}}}]}}}}}";
 CommentCounts.CapturePage(video,meta+"var ytInitialData = "+json+";");
 Check(video.CommentCountText=="123개","only verified current-video comments section provides count");
 var wrong=V(1);CommentCounts.CapturePage(wrong,meta+"var ytInitialData = "+json+";");
 Check(wrong.CommentCountText==null && wrong.CommentContinuation==null,"other video identity cannot supply count or continuation");
 video.CommentContinuation="ephemeral-test";
 Check(!new JavaScriptSerializer().Serialize(video).Contains("ephemeral-test"),"ephemeral continuation excluded from public serialized video");
 string output=Path.GetFullPath(args[0]);Directory.CreateDirectory(output);string run=Path.Combine(output,"run-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(run);
 var ledger=new VideoLedger(Path.Combine(run,"videos.jsonl"));
 var batch=VideoBatch.Collect("검사",ledger,new ContentStore(Path.Combine(run,"content")),CancellationToken.None,
 search:(q,t)=>Task.FromResult(new List<Video>{V(0),V(1)}),captions:(v,t)=>Task.FromResult(C(v)),category:"all",includeCommentCounts:true,
 categories:(v,t)=>Task.FromResult("20"),commentCounts:(v,t)=>Task.FromResult(v.Id==V(0).Id?"123개":"미확인")).GetAwaiter().GetResult();
 Check(batch.Videos.Count==2 && batch.Videos[0].CommentCountText=="123개" && batch.Videos[1].CommentCountText=="미확인","all-category batch retains videos with known and unknown comment counts");
 Check(File.ReadAllText(Path.Combine(run,"videos.jsonl")).Contains("123개"),"selected video history retains comment count display");
 var live=new List<Video>();
 foreach(string id in new[]{"HPUpsEzL1ps","dQw4w9WgXcQ"}){
 var found=new Video{Id=id,Title="실제 영상 메타데이터 검사"};
 string category=CategoryService.Fetch(found,CancellationToken.None).GetAwaiter().GetResult();
 found.CommentCountText=CommentCounts.Fetch(found,CancellationToken.None).GetAwaiter().GetResult();
 Check(category!=null && found.CommentCountText!="미확인","actual public video provides comment header count: "+id);
 Console.WriteLine("ACTUAL COMMENT COUNT "+id+" "+found.CommentCountText);live.Add(found);
 }
 var actualBatch=VideoBatch.Collect("인디 게임 추천",new VideoLedger(Path.Combine(run,"live.jsonl")),new ContentStore(Path.Combine(run,"live-content")),CancellationToken.None,category:"20",koreanOnly:true,includeCommentCounts:true).GetAwaiter().GetResult();
 Check(actualBatch.Videos.Count>0 && actualBatch.Error=="" && actualBatch.Videos.All(v=>!string.IsNullOrEmpty(v.CommentCountText)) && actualBatch.Videos.Any(v=>v.CommentCountText.EndsWith("개")),"actual Korean gaming batch preserves metadata count through filters and ledger");
 Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
 using(var form=new MainForm(Path.Combine(run,"ui","history.json"))){form.Opacity=0;form.ShowInTaskbar=false;form.Show();Application.DoEvents();
 var grid=(DataGridView)form.Controls.Find("Videos",true)[0];Check(grid.Columns["comments"].HeaderText=="댓글 수","native recommendation list has comment count column");
 foreach(var item in live)grid.Rows.Add(item.Title,"채널","12:34","123회","1일 전",item.CommentCountText);
 Application.DoEvents();Check(grid.Rows[0].Cells["comments"].Value.ToString()==live[0].CommentCountText,"actual count value displayed in native row");
 using(var bitmap=new Bitmap(form.Width,form.Height)){form.DrawToBitmap(bitmap,new Rectangle(Point.Empty,bitmap.Size));bitmap.Save(Path.Combine(output,"comment-count-preview.png"),ImageFormat.Png);}form.Close();}
 return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}}
}
