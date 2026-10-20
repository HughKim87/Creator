using System;using System.Collections.Generic;using System.Drawing;using System.Drawing.Imaging;using System.IO;using System.Linq;using System.Net;using System.Threading;using System.Windows.Forms;using ReplierDesktop;
public static class TrendingChecks
{
 static void Check(bool ok,string label){if(!ok)throw new Exception(label);Console.WriteLine("PASS "+label);}
 [STAThread] public static int Main(string[] args){try{
 ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;
 string card="{\"gridVideoRenderer\":{\"videoId\":\"HPUpsEzL1ps\",\"title\":{\"simpleText\":\"검사 영상\"},\"shortBylineText\":{\"runs\":[{\"text\":\"검사 채널\"}]},\"publishedTimeText\":{\"simpleText\":\"3일 전\"},\"viewCountText\":{\"simpleText\":\"조회수 123회\"},\"thumbnailOverlays\":[{\"thumbnailOverlayTimeStatusRenderer\":{\"text\":{\"simpleText\":\"12:34\"},\"style\":\"DEFAULT\"}}]}}";
 string html="var ytInitialData = {\"contents\":{\"twoColumnBrowseResultsRenderer\":{\"tabs\":[{\"tabRenderer\":{\"selected\":true,\"content\":{\"sectionListRenderer\":{\"contents\":[{\"itemSectionRenderer\":{\"contents\":[{\"shelfRenderer\":{\"title\":{\"runs\":[{\"text\":\"인기 급상승 동영상\"}]},\"content\":{\"gridRenderer\":{\"items\":["+card+","+card+"]}}}}]}}]}}}}]}}};";
 var parsed=TrendingSearch.Parse(html,"week");
 Check(parsed.Count==2 && parsed[0].Channel=="검사 채널" && parsed[0].DurationText=="12:34" && parsed[0].ViewCountText=="조회수 123회","repeated trend card fields parsed from exact chart shelf");
 Check(TrendingSearch.Parse(html,"day").Count==0,"trending videos obey selected upload period");
 bool rejected=false;try{TrendingSearch.Parse(html.Replace("인기 급상승 동영상","추천 영상"),"all");}catch(InvalidDataException){rejected=true;}
 Check(rejected,"generic recommendation shelf is not passed off as trending");
 Check(TrendingSearch.Parse(html.Replace("DEFAULT","LIVE"),"all").Count==0,"live streams excluded from chart candidates");
 var actual=TrendingSearch.Fetch(CancellationToken.None,"week").GetAwaiter().GetResult();
 Check(actual.Count>0 && actual.All(v=>UploadPeriods.IncludesDisplayAge(v.PublishedText,"week")),"actual Korean gaming trend page provides recent video cards");
 Console.WriteLine("ACTUAL TREND CANDIDATES "+actual.Count);
 string output=Path.GetFullPath(args[0]);Directory.CreateDirectory(output);string run=Path.Combine(output,"run-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(run);
 Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Exception error=null;
 using(var form=new MainForm(Path.Combine(run,"history.json"))){form.ShowInTaskbar=false;form.Opacity=0;
 form.Shown+=async(sender,e)=>{try{
 var mode=(ComboBox)form.Controls.Find("SearchMode",true)[0];mode.SelectedIndex=3;var button=(Button)form.Controls.Find("Recommend",true)[0];var category=(ComboBox)form.Controls.Find("Category",true)[0];
 Check(button.Enabled,"common acquisition button enabled in trending mode");
 category.SelectedIndex=VideoCategories.Index("10");Check(!button.Enabled,"unsupported category cannot masquerade as a gaming chart");
 category.SelectedIndex=VideoCategories.Index("20");Check(button.Enabled,"switching back to gaming enables chart button");
 ((TextBox)form.Controls.Find("Query",true)[0]).Text="검색하지 않을 관심 주제";
 var task=form.TrendingVideos();
 Check(!button.Enabled && !((Button)form.Controls.Find("Recommend",true)[0]).Enabled,"acquisition controls disabled during collection");
 await task;
 var grid=(DataGridView)form.Controls.Find("Videos",true)[0];
 Check(grid.Rows.Count>0 && grid.Rows.Count<=10,"native trending action returns up to ten filtered captioned videos");
 Check(((Label)form.Controls.Find("SelectedQuery",true)[0]).Text=="한국 게임 인급동 · 조회수순","chart source and view-count display order explicit");
 Check(!File.Exists(Path.Combine(run,"history.json")),"trending bypasses autocomplete and leaves keyword history intact");
 var ids=new VideoLedger(Path.Combine(run,"videos.jsonl")).ReadIds();var store=new ContentStore(Path.Combine(run,"content"));
 Check(ids.Count==0 && !File.Exists(Path.Combine(run,"videos.jsonl")),"trending does not write permanent selection history");
 Check(grid.Rows.Cast<DataGridViewRow>().All(r=>KoreanVideos.ContentMatches(store.Load(((Video)r.Tag).Id))),"trending retains Korean caption requirement");
 Check(grid.Rows.Cast<DataGridViewRow>().All(r=>r.Cells["comments"].Value!=null),"trending rows retain comment count metadata");
 Check(button.Enabled && ((Button)form.Controls.Find("Recommend",true)[0]).Enabled,"buttons restored after trending collection");
 var counts=grid.Rows.Cast<DataGridViewRow>().Select(r=>ViewCounts.Parse(r.Cells["views"].Value.ToString())).ToArray();
 Check(counts.SequenceEqual(counts.OrderByDescending(x=>x)),"trending results respect existing descending view-count preference");
 using(var bitmap=new Bitmap(form.Width,form.Height)){form.DrawToBitmap(bitmap,new Rectangle(Point.Empty,bitmap.Size));bitmap.Save(Path.Combine(output,"trending-preview.png"),ImageFormat.Png);}
 }catch(Exception ex){error=ex;}finally{form.Close();}};
 Application.Run(form);}
 if(error!=null)throw error;
 return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}}
}
