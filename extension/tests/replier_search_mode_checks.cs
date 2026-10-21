using System;using System.Collections.Generic;using System.Drawing;using System.Drawing.Imaging;using System.IO;using System.Linq;using System.Net;using System.Threading;using System.Threading.Tasks;using System.Windows.Forms;using ReplierDesktop;
public static class SearchModeChecks
{
 static void Check(bool ok,string name){if(!ok)throw new Exception(name);Console.WriteLine("PASS "+name);}
 [STAThread]public static int Main(string[] args){try{
 ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;
 string output=Path.GetFullPath(args[0]);Directory.CreateDirectory(output);string run=Path.Combine(output,"run-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(run);
 Check(ChannelSearch.ChannelUrl("https://m.youtube.com/@sleepground/shorts?x=1")=="https://www.youtube.com/@sleepground/videos?hl=ko&gl=KR","channel URL normalized to public videos tab");
 foreach(string url in new[]{"https://youtube.com.evil.com/@abc","http://youtube.com/@abc","https://www.youtube.com/watch?v=123","https://user@youtube.com/@abc","https://youtube.com:444/@abc","https://127.0.0.1/@abc"}){
 bool rejected=false;try{ChannelSearch.ChannelUrl(url);}catch(ArgumentException){rejected=true;}Check(rejected,"non-channel or unsafe URL rejected");}
 var games=ChannelSearch.ParseGames("{\"games\":[\"마인크래프트\",\"없는게임\",\"마인크래프트\"]}",new[]{"마인크래프트 | Minecraft","마인크래프트 새 영상"});
 Check(games.Count==1 && games[0].VideoCount==2,"game candidates require observed names and retain counts");
 Check(ChannelSearch.Matches("마인크래프트 생존","마인크래프트") && !ChannelSearch.Matches("스타크래프트","마인크래프트"),"unrelated games excluded by observed game name");
 Check(ChannelSearch.Tags("<meta property='og:url' content='https://www.youtube.com/watch?v=V0000000001'><meta property='og:video:tag' content='마인크래프트'>","V0000000001")=="마인크래프트","uploader tags tied to canonical video");
 Check(ChannelSearch.Tags("<meta property='og:url' content='https://www.youtube.com/watch?v=V0000000002'><meta property='og:video:tag' content='마인크래프트'>","V0000000001")=="","different canonical video tags rejected");
 string fixture="var ytInitialData = {\"contents\":{\"twoColumnBrowseResultsRenderer\":{\"tabs\":[{\"tabRenderer\":{\"selected\":true,\"content\":{\"richGridRenderer\":{\"contents\":[{\"richItemRenderer\":{\"content\":{\"lockupViewModel\":{\"contentId\":\"V0000000001\",\"contentType\":\"LOCKUP_CONTENT_TYPE_VIDEO\",\"metadata\":{\"lockupMetadataViewModel\":{\"title\":{\"content\":\"게임 영상\"}}}}}}},{\"richItemRenderer\":{\"content\":{\"lockupViewModel\":{\"contentId\":\"V0000000002\",\"contentType\":\"LOCKUP_CONTENT_TYPE_PLAYLIST\",\"metadata\":{\"lockupMetadataViewModel\":{\"title\":{\"content\":\"목록\"}}}}}}}]}}}},{\"tabRenderer\":{\"content\":{\"richGridRenderer\":{\"contents\":[{\"richItemRenderer\":{\"content\":{\"videoRenderer\":{\"videoId\":\"V0000000003\",\"title\":{\"simpleText\":\"다른 탭 영상\"}}}}}]}}}}]}}};";
 var fixtureVideos=ChannelSearch.ParseVideos(fixture);
 Check(fixtureVideos.Count==1 && fixtureVideos[0].Id=="V0000000001","channel parser excludes playlists and unselected tabs");
 bool noGame=false;try{ChannelSearch.ParseGames("{\"games\":[\"없는게임\"]}",new[]{"일반 일상 영상"});}catch(InvalidDataException){noGame=true;}
 Check(noGame,"unknown game analysis has no invented fallback");
 var actual=ChannelSearch.ParseVideos(ChannelSearch.Read(ChannelSearch.ChannelUrl("https://www.youtube.com/@sleepground"),CancellationToken.None).GetAwaiter().GetResult());
 Check(actual.Count>0 && actual.Count<=12 && actual.Select(v=>v.Id).Distinct().Count()==actual.Count,"actual public channel recent video cards parsed");
 Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Exception error=null;
 using(var form=new MainForm(Path.Combine(run,"history.json"))){form.Opacity=0;form.ShowInTaskbar=false;
 form.Shown+=async(sender,e)=>{try{
 var mode=(ComboBox)form.Controls.Find("SearchMode",true)[0];var query=(TextBox)form.Controls.Find("Query",true)[0];var get=(Button)form.Controls.Find("Recommend",true)[0];var category=(ComboBox)form.Controls.Find("Category",true)[0];
 Check(mode.Items.Count==4 && get.Text=="가져오기","four search modes share one acquisition button");
 query.Text="관심 게임";mode.SelectedIndex=0;query.Text="마인크래프트";mode.SelectedIndex=1;Check(query.Text=="관심 게임","automatic topic input restored per mode");
 mode.SelectedIndex=0;Check(query.Text=="마인크래프트" && query.AccessibleName=="검색어 입력","direct keyword input restored with matching hint");
 mode.SelectedIndex=3;Check(!query.Visible,"trending hides text input");category.SelectedIndex=VideoCategories.Index("10");Check(!get.Enabled,"gaming-only trending unavailable in music category");
 mode.SelectedIndex=0;Check(get.Enabled,"direct search remains available in other categories");category.SelectedIndex=VideoCategories.Index("20");
 foreach(var size in new[]{new Size(800,600),new Size(1120,850)}){
 form.Size=size;form.PerformLayout();Application.DoEvents();
 foreach(var control in new Control[]{mode,query,get,category,form.Controls.Find("UploadPeriod",true)[0],form.Controls.Find("Stop",true)[0]}){
 var rect=form.RectangleToClient(control.RectangleToScreen(control.ClientRectangle));Check(form.ClientRectangle.Contains(rect) && rect.Width>=40,"header control inside "+size+": "+control.Name);}
 }
 ((ComboBox)form.Controls.Find("UploadPeriod",true)[0]).SelectedIndex=3;
 query.Text="";await form.AcquireVideos();Check(((Label)form.Controls.Find("BatchStatus",true)[0]).Text.Contains("검색어를 입력"),"empty direct keyword rejected before search");
 query.Text="마인크래프트";await form.AcquireVideos();var grid=(DataGridView)form.Controls.Find("Videos",true)[0];
 Check(grid.Rows.Count>0 && grid.Rows.Count<=10 && ((Label)form.Controls.Find("SelectedQuery",true)[0]).Text=="검색어 · 마인크래프트","direct keyword reaches shared filtered results without autocomplete");
 Check(!File.Exists(Path.Combine(run,"history.json")),"direct search leaves automatic keyword history unchanged");
 mode.SelectedIndex=2;query.Text="https://www.youtube.com/@sleepground";
 await form.AcquireVideos();
 Check(grid.Rows.Count>0 && ((Label)form.Controls.Find("SelectedQuery",true)[0]).Text.StartsWith("채널에서 찾은 게임 · "),"actual local model channel analysis and random game reach shared results");
 Check(!File.Exists(Path.Combine(run,"history.json")),"channel search leaves automatic keyword history unchanged");
 Check(get.Enabled && mode.Enabled && query.Enabled,"common acquisition controls restored");
 using(var bitmap=new Bitmap(form.Width,form.Height)){form.DrawToBitmap(bitmap,new Rectangle(Point.Empty,bitmap.Size));bitmap.Save(Path.Combine(output,"search-modes.png"),ImageFormat.Png);}
 }catch(Exception ex){error=ex;}finally{form.Close();}};Application.Run(form);}
 if(error!=null)throw error;return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
